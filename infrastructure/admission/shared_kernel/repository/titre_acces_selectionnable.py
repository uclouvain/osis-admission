# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import uuid
from typing import List, Optional

from django.conf import settings
from django.db.models import F, Max, Prefetch, Q, QuerySet
from django.utils.translation import get_language, gettext

from admission.ddd.admission.shared_kernel.domain.model.enums.condition_acces import (
    TypeTitreAccesSelectionnable,
)
from admission.ddd.admission.shared_kernel.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.shared_kernel.domain.model.titre_acces_selectionnable import (
    TitreAccesSelectionnable,
    TitreAccesSelectionnableIdentity,
)
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import (
    ExperienceNonTrouveeException,
    PropositionNonTrouveeException,
)
from admission.ddd.admission.shared_kernel.enums.emplacement_document import (
    OngletsDemande,
)
from admission.ddd.admission.shared_kernel.repository.i_titre_acces_selectionnable import (
    ITitreAccesSelectionnableRepository,
)
from admission.models.base import (
    BaseAdmission,
)
from admission.models.valuated_epxeriences import (
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from base.utils.utils import format_academic_year
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import (
    IExperienceParcoursInterneTranslator,
)
from osis_profile import BE_ISO_CODE, MOIS_DEBUT_ANNEE_ACADEMIQUE
from osis_profile.models import EXAM_TYPE_PREMIER_CYCLE_LABEL_FR, Exam
from osis_profile.models.enums.curriculum import ActivityType, Result


class TitreAccesSelectionnableRepository(ITitreAccesSelectionnableRepository):
    @classmethod
    def search_by_proposition(
        cls,
        proposition_identity: PropositionIdentity,
        experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
        seulement_selectionnes: Optional[bool] = None,
    ) -> List[TitreAccesSelectionnable]:
        # Retrieve the secondary studies
        admission: BaseAdmission = (
            BaseAdmission.objects.select_related(
                'candidate__belgianhighschooldiploma__academic_graduation_year',
                'candidate__belgianhighschooldiploma__institute',
                'candidate__foreignhighschooldiploma__academic_graduation_year',
                'candidate__foreignhighschooldiploma__country',
                'candidate__graduated_from_high_school_year',
                'training__academic_year',
            )
            .prefetch_related(
                Prefetch(
                    'candidate__exams',
                    queryset=Exam.objects.filter(type__label_fr=EXAM_TYPE_PREMIER_CYCLE_LABEL_FR),
                    to_attr='exam_high_school_diploma_alternative',
                ),
            )
            .get(uuid=proposition_identity.uuid)
        )

        additional_filters = {'is_access_title': True} if seulement_selectionnes else {}

        # Retrieve the academic experiences from the curriculum
        educational_valuated_experiences: QuerySet[AdmissionEducationalValuatedExperiences] = (
            AdmissionEducationalValuatedExperiences.objects.filter(
                baseadmission=admission,
                **additional_filters,
            )
            .annotate(last_year=Max('educationalexperience__educationalexperienceyear__academic_year__year'))
            .filter(
                Q(educationalexperience__obtained_diploma=True)
                | Q(
                    educationalexperience__educationalexperienceyear__result__in=[
                        Result.WAITING_RESULT.name,
                        Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
                    ],
                    educationalexperience__educationalexperienceyear__academic_year__year=F('last_year'),
                )
            )
            .distinct()
            .select_related(
                'educationalexperience__country',
                'educationalexperience__institute',
                'educationalexperience__program',
                'educationalexperience__fwb_equivalent_program',
            )
        )

        # Retrieve the non academic experiences from the curriculum
        professional_valuated_experiences: QuerySet[AdmissionProfessionalValuatedExperiences] = (
            AdmissionProfessionalValuatedExperiences.objects.filter(
                baseadmission=admission,
                **additional_filters,
            ).select_related('professionalexperience')
        )

        # Retrieve the internal experiences
        internal_access_titles_uuids = set(
            [
                str(uuid.UUID(int=internal_access_title_id))
                for internal_access_title_id in admission.internal_access_titles.all().values_list('pk', flat=True)
            ]
        )

        internal_experiences = (
            experience_parcours_interne_translator.recuperer(
                matricule=admission.candidate.global_id,
                avec_credits=False,
            )
            if not seulement_selectionnes or seulement_selectionnes and internal_access_titles_uuids
            else []
        )

        access_titles = []

        high_school_diploma_experience_uuid = None
        high_school_diploma_experience_year = None
        high_school_diploma = None
        high_school_diploma_country = ''
        has_default_language = get_language() == settings.LANGUAGE_CODE
        formatted_high_school_diploma_name = ''
        formatted_high_school_diploma_name_variables = {}

        if getattr(admission.candidate, 'belgianhighschooldiploma', None):
            high_school_diploma = admission.candidate.belgianhighschooldiploma
            high_school_diploma_country = BE_ISO_CODE
            formatted_high_school_diploma_name = '{title} ({year}) - {institute}'
            formatted_high_school_diploma_name_variables['title'] = gettext('CESS')
            formatted_high_school_diploma_name_variables['institute'] = (
                high_school_diploma.institute.name
                if high_school_diploma.institute_id
                else high_school_diploma.other_institute_name
            )

        elif getattr(admission.candidate, 'foreignhighschooldiploma', None):
            high_school_diploma = admission.candidate.foreignhighschooldiploma
            formatted_high_school_diploma_name = '{title} ({year}) - {country}'
            formatted_high_school_diploma_name_variables['title'] = (
                high_school_diploma.get_foreign_diploma_type_display()
            )
            if getattr(high_school_diploma, 'country', None):
                high_school_diploma_country = high_school_diploma.country.iso_code
                formatted_high_school_diploma_name_variables['country'] = (
                    high_school_diploma.country.name if has_default_language else high_school_diploma.country.name_en
                )
        elif admission.candidate.exam_high_school_diploma_alternative:
            high_school_diploma = admission.candidate.exam_high_school_diploma_alternative[0]
            formatted_high_school_diploma_name = '{title}'
            formatted_high_school_diploma_name_variables['title'] = gettext("Bachelor's course entrance exam")

        if high_school_diploma:
            high_school_diploma_experience_uuid = high_school_diploma.uuid

            if getattr(high_school_diploma, 'academic_graduation_year', None):
                high_school_diploma_experience_year = high_school_diploma.academic_graduation_year.year
            elif isinstance(high_school_diploma, Exam) and high_school_diploma.year is not None:
                high_school_diploma_experience_year = high_school_diploma.year.year

        elif getattr(admission.candidate, 'graduated_from_high_school_year', None):
            high_school_diploma_experience_uuid = OngletsDemande.ETUDES_SECONDAIRES.name
            high_school_diploma_experience_year = admission.candidate.graduated_from_high_school_year.year
            formatted_high_school_diploma_name = '{title} ({year})'
            formatted_high_school_diploma_name_variables['title'] = gettext('Secondary school')

        if high_school_diploma_experience_uuid and (
            not seulement_selectionnes or admission.are_secondary_studies_access_title
        ):
            formatted_high_school_diploma_name_variables['year'] = format_academic_year(
                high_school_diploma_experience_year,
            )
            access_titles.append(
                TitreAccesSelectionnable(
                    entity_id=TitreAccesSelectionnableIdentity(
                        uuid_experience=high_school_diploma_experience_uuid,
                        uuid_proposition=admission.uuid,
                        type_titre=TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES,
                    ),
                    selectionne=bool(admission.are_secondary_studies_access_title),
                    annee=high_school_diploma_experience_year,
                    pays_iso_code=high_school_diploma_country,
                    nom=formatted_high_school_diploma_name.format(**formatted_high_school_diploma_name_variables),
                ),
            )

        exam = (
            Exam.objects.filter(
                admissions__admission=admission,
            )
            .select_related('year')
            .first()
        )
        if exam is not None and (not seulement_selectionnes or admission.is_exam_access_title):
            access_titles.append(
                TitreAccesSelectionnable(
                    entity_id=TitreAccesSelectionnableIdentity(
                        uuid_experience=str(exam.uuid),
                        uuid_proposition=str(admission.uuid),
                        type_titre=TypeTitreAccesSelectionnable.EXAMENS,
                    ),
                    selectionne=bool(admission.is_exam_access_title),
                    annee=exam.year.year if exam.year else None,
                    pays_iso_code='',
                    nom='{title} ({year})'.format(
                        title=exam.type.title,
                        year=format_academic_year(exam.year.year) if exam.year else '',
                    ),
                ),
            )

        for experience in educational_valuated_experiences:
            educational_experience = experience.educationalexperience
            institute_name = (
                educational_experience.institute.name
                if educational_experience.institute_id
                else educational_experience.institute_name
            )
            training_name = (
                educational_experience.program.title
                if educational_experience.program_id
                else educational_experience.education_name
            )

            if educational_experience.fwb_equivalent_program_id:
                training_name += f' ({educational_experience.fwb_equivalent_program.title})'

            access_titles.append(
                TitreAccesSelectionnable(
                    entity_id=TitreAccesSelectionnableIdentity(
                        uuid_experience=experience.educationalexperience_id,
                        uuid_proposition=experience.baseadmission_id,
                        type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE,
                    ),
                    selectionne=bool(experience.is_access_title),
                    annee=experience.last_year,
                    pays_iso_code=(educational_experience.country.iso_code if educational_experience.country else ''),
                    nom='{title} ({year}) - {institute}'.format(
                        title=training_name,
                        year=format_academic_year(experience.last_year),
                        institute=institute_name,
                    ),
                )
            )

        for experience in professional_valuated_experiences:
            last_year = None
            if experience.professionalexperience.end_date:
                last_year = (
                    experience.professionalexperience.end_date.year
                    if experience.professionalexperience.end_date.month >= MOIS_DEBUT_ANNEE_ACADEMIQUE
                    else experience.professionalexperience.end_date.year - 1
                )
            access_titles.append(
                TitreAccesSelectionnable(
                    entity_id=TitreAccesSelectionnableIdentity(
                        uuid_experience=experience.professionalexperience_id,
                        uuid_proposition=experience.baseadmission_id,
                        type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE,
                    ),
                    selectionne=bool(experience.is_access_title),
                    annee=last_year,
                    pays_iso_code='',
                    nom='{title} ({year})'.format(
                        title=(
                            experience.professionalexperience.activity
                            if experience.professionalexperience.type == ActivityType.OTHER.name
                            else str(ActivityType.get_value(experience.professionalexperience.type))
                        ),
                        year=format_academic_year(last_year),
                    ),
                )
            )

        selectable_internal_experience_years = {
            admission.training.academic_year.year,
            admission.training.academic_year.year - 1,
        }

        for experience in internal_experiences:
            is_selected = experience.uuid in internal_access_titles_uuids
            last_experience = experience.derniere_annee
            last_year = last_experience.annee

            # Add the experience
            if (
                # > if it can be chosen because
                not (
                    # > the diploma has already been or will be obtained
                    experience.est_diplome_ou_diplomable
                    # > the last year is the same year or the previous year of the enrolment
                    or last_year in selectable_internal_experience_years
                )
                # > if it has already been selected if we only want the selected ones
                or seulement_selectionnes
                and not is_selected
            ):
                continue

            access_titles.append(
                TitreAccesSelectionnable(
                    entity_id=TitreAccesSelectionnableIdentity(
                        uuid_experience=experience.uuid,
                        uuid_proposition=admission.uuid,
                        type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_PARCOURS_INTERNE,
                    ),
                    selectionne=is_selected,
                    annee=last_year,
                    pays_iso_code=BE_ISO_CODE,
                    nom='{title} ({year}) - UCL'.format(
                        title=last_experience.intitule_formation,
                        year=format_academic_year(last_year),
                    ),
                )
            )

        return access_titles

    @classmethod
    def save(cls, entity: TitreAccesSelectionnable) -> None:
        if entity.entity_id.type_titre == TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES:
            if not BaseAdmission.objects.filter(uuid=entity.entity_id.uuid_proposition).update(
                are_secondary_studies_access_title=entity.selectionne,
            ):
                raise PropositionNonTrouveeException

        elif entity.entity_id.type_titre == TypeTitreAccesSelectionnable.EXAMENS:
            if not BaseAdmission.objects.filter(uuid=entity.entity_id.uuid_proposition).update(
                is_exam_access_title=entity.selectionne,
            ):
                raise PropositionNonTrouveeException

        elif entity.entity_id.type_titre == TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE:
            if not AdmissionEducationalValuatedExperiences.objects.filter(
                baseadmission_id=entity.entity_id.uuid_proposition,
                educationalexperience_id=entity.entity_id.uuid_experience,
            ).update(is_access_title=entity.selectionne):
                raise ExperienceNonTrouveeException

        elif entity.entity_id.type_titre == TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE:
            if not AdmissionProfessionalValuatedExperiences.objects.filter(
                baseadmission_id=entity.entity_id.uuid_proposition,
                professionalexperience_id=entity.entity_id.uuid_experience,
            ).update(is_access_title=entity.selectionne):
                raise ExperienceNonTrouveeException

        elif entity.entity_id.type_titre == TypeTitreAccesSelectionnable.EXPERIENCE_PARCOURS_INTERNE:
            experience_pk = uuid.UUID(entity.entity_id.uuid_experience).int
            current_admission = BaseAdmission.objects.get(uuid=entity.entity_id.uuid_proposition)

            if entity.selectionne:
                current_admission.internal_access_titles.add(experience_pk)
            else:
                current_admission.internal_access_titles.remove(experience_pk)
