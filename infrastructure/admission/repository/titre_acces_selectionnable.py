# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional

from django.db.models import QuerySet, Max, Q

from admission.contrib.models.base import (
    BaseAdmission,
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from admission.ddd import MOIS_DEBUT_ANNEE_ACADEMIQUE, BE_ISO_CODE
from admission.ddd.admission.domain.model.enums.condition_acces import TypeTitreAccesSelectionnable
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.model.titre_acces_selectionnable import (
    TitreAccesSelectionnable,
    TitreAccesSelectionnableIdentity,
)
from admission.ddd.admission.domain.repository.i_titre_acces_selectionnable import ITitreAccesSelectionnableRepository
from admission.ddd.admission.domain.validator.exceptions import (
    PropositionNonTrouveeException,
    ExperienceNonTrouveeException,
)
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from osis_profile.models.enums.curriculum import Result


class TitreAccesSelectionnableRepository(ITitreAccesSelectionnableRepository):
    @classmethod
    def search_by_proposition(
        cls,
        proposition_identity: PropositionIdentity,
        seulement_selectionnes: Optional[bool] = None,
    ) -> List[TitreAccesSelectionnable]:
        # Retrieve the secondary studies
        admission: BaseAdmission = (
            BaseAdmission.objects.select_related(
                'candidate__belgianhighschooldiploma__academic_graduation_year',
                'candidate__foreignhighschooldiploma__academic_graduation_year',
                'candidate__foreignhighschooldiploma__country',
                'candidate__highschooldiplomaalternative',
                'candidate__graduated_from_high_school_year',
            )
            .only(
                'are_secondary_studies_access_title',
                'candidate__belgianhighschooldiploma__uuid',
                'candidate__foreignhighschooldiploma__uuid',
                'candidate__belgianhighschooldiploma__academic_graduation_year__year',
                'candidate__foreignhighschooldiploma__academic_graduation_year__year',
                'candidate__foreignhighschooldiploma__country__iso_code',
                'candidate__highschooldiplomaalternative__uuid',
                'candidate__graduated_from_high_school_year__year',
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
            .filter(
                Q(educationalexperience__obtained_diploma=True)
                | Q(educationalexperience__educationalexperienceyear__result=Result.WAITING_RESULT.name)
            )
            .annotate(last_year=Max('educationalexperience__educationalexperienceyear__academic_year__year'))
            .select_related('educationalexperience__country')
        )

        # Retrieve the non academic experiences from the curriculum
        professional_valuated_experiences: QuerySet[AdmissionProfessionalValuatedExperiences] = (
            AdmissionProfessionalValuatedExperiences.objects.filter(
                baseadmission=admission,
                **additional_filters,
            )
            .select_related('professionalexperience')
            .only('professionalexperience__end_date')
        )

        access_titles = []

        high_school_diploma_experience_uuid = None
        high_school_diploma_experience_year = None
        high_school_diploma = None
        high_school_diploma_country = ''

        if getattr(admission.candidate, 'belgianhighschooldiploma', None):
            high_school_diploma = admission.candidate.belgianhighschooldiploma
            high_school_diploma_country = BE_ISO_CODE
        elif getattr(admission.candidate, 'foreignhighschooldiploma', None):
            high_school_diploma = admission.candidate.foreignhighschooldiploma
            if getattr(admission.candidate.foreignhighschooldiploma, 'country', None):
                high_school_diploma_country = admission.candidate.foreignhighschooldiploma.country.iso_code
        elif (
            getattr(admission.candidate, 'highschooldiplomaalternative', None)
            and admission.candidate.highschooldiplomaalternative.first_cycle_admission_exam
        ):
            high_school_diploma = admission.candidate.highschooldiplomaalternative

        if high_school_diploma:
            high_school_diploma_experience_uuid = high_school_diploma.uuid

            if getattr(high_school_diploma, 'academic_graduation_year', None):
                high_school_diploma_experience_year = high_school_diploma.academic_graduation_year.year

        elif getattr(admission.candidate, 'graduated_from_high_school_year', None):
            high_school_diploma_experience_uuid = OngletsDemande.ETUDES_SECONDAIRES.name
            high_school_diploma_experience_year = admission.candidate.graduated_from_high_school_year.year

        if high_school_diploma_experience_uuid and (
            not seulement_selectionnes or admission.are_secondary_studies_access_title
        ):
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
                ),
            )

        for experience in educational_valuated_experiences:
            access_titles.append(
                TitreAccesSelectionnable(
                    entity_id=TitreAccesSelectionnableIdentity(
                        uuid_experience=experience.educationalexperience_id,
                        uuid_proposition=experience.baseadmission_id,
                        type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE,
                    ),
                    selectionne=bool(experience.is_access_title),
                    annee=experience.last_year,
                    pays_iso_code=experience.educationalexperience.country.iso_code
                    if experience.educationalexperience.country
                    else '',
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
