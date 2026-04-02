# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.db.models import Prefetch

from admission.ddd.admission.shared_kernel.domain.model.enums.condition_acces import TypeTitreAccesSelectionnable
from admission.ddd.admission.shared_kernel.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.shared_kernel.domain.service.conditions_d_acces import IConditionDAcces
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import PropositionNonTrouveeException
from admission.models import DoctorateAdmission, GeneralEducationAdmission
from admission.models.valuated_epxeriences import (
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from ddd.logic.deliberation.cloture.queries import RechercherDeliberationsProgrammesAnnuelsActeesQuery
from ddd.logic.deliberation.propositions.domain.model._decision import Decision
from ddd.logic.deliberation.propositions.domain.model._impact_progression import BAMA15
from base.models.enums.condition_acces import ConditionAcces
from osis_profile import BE_ISO_CODE
from osis_profile.models import EducationalExperienceYear, Exam
from osis_profile.models.enums.curriculum import Result
from reference.models.enums.cycle import Cycle
from reference.models.enums.duration_type import DurationType
from reference.models.enums.study_type import StudyType

MASTERS_TYPES = {
    TrainingType.MASTER_MA_120.name,
    TrainingType.MASTER_MD_120.name,
    TrainingType.MASTER_MS_120.name,
    TrainingType.MASTER_M4.name,
    TrainingType.MASTER_MS_180_240.name,
    TrainingType.MASTER_M1.name,
}

DOCTORATS_TYPES = {
    TrainingType.PHD.name,
    TrainingType.FORMATION_PHD.name,
}


class ConditionDAcces(IConditionDAcces):

    @classmethod
    def _compute_diplome_secondaire(self, admission: GeneralEducationAdmission | DoctorateAdmission):
        if admission.training.education_group_type.name == TrainingType.BACHELOR.name:
            admission.admission_requirement = ConditionAcces.SECONDAIRE.name
            diplome_secondaire_belge = getattr(admission.candidate, 'belgianhighschooldiploma', None)
            diplome_secondaire_etranger = getattr(admission.candidate, 'foreignhighschooldiploma', None)

            if diplome_secondaire_belge is not None:
                admission.admission_requirement_year = diplome_secondaire_belge.academic_graduation_year
            elif diplome_secondaire_etranger is not None:
                admission.admission_requirement_year = diplome_secondaire_etranger.academic_graduation_year
            else:
                admission.admission_requirement = ConditionAcces.INCOMPLET.name
                admission.admission_requirement_year = None
        else:
            admission.admission_requirement = ConditionAcces.INSUFFISANT.name
            admission.admission_requirement_year = None

    @classmethod
    def _compute_examen(self, admission: GeneralEducationAdmission | DoctorateAdmission, exam: Exam):
        if admission.training.education_group_type.name == TrainingType.BACHELOR.name:
            admission.admission_requirement = ConditionAcces.EXAMEN_ADMISSION.name
            admission.admission_requirement_year = exam.year
        else:
            admission.admission_requirement = ConditionAcces.INSUFFISANT.name
            admission.admission_requirement_year = None

    @classmethod
    def _compute_diplome_1er_cycle(self, admission: GeneralEducationAdmission | DoctorateAdmission, annee_diplome):
        if (
            admission.training.education_group_type.name
            in {
                TrainingType.BACHELOR.name,
                TrainingType.CERTIFICATE.name,
            }
            | MASTERS_TYPES
        ):
            admission.admission_requirement = ConditionAcces.BAC.name
            admission.admission_requirement_year = annee_diplome
        else:
            admission.admission_requirement = ConditionAcces.INSUFFISANT.name
            admission.admission_requirement_year = None

    @classmethod
    def _compute_diplome_2eme_cycle(self, admission: GeneralEducationAdmission | DoctorateAdmission, annee_diplome):
        admission.admission_requirement = ConditionAcces.MASTER.name
        admission.admission_requirement_year = annee_diplome

    @classmethod
    def _compute_bama15_1er_cycle(self, admission: GeneralEducationAdmission | DoctorateAdmission, annee_diplome):
        if admission.training.education_group_type.name in MASTERS_TYPES:
            admission.admission_requirement = ConditionAcces.BAMA15.name
            admission.admission_requirement_year = annee_diplome
        else:
            admission.admission_requirement = ConditionAcces.INSUFFISANT.name
            admission.admission_requirement_year = None

    @classmethod
    def _compute_diplome_snu_court(self, admission: GeneralEducationAdmission | DoctorateAdmission, annee_diplome):
        if admission.training.education_group_type.name in [
            TrainingType.BACHELOR.name,
            TrainingType.CERTIFICATE.name,
        ]:
            admission.admission_requirement = ConditionAcces.SNU_TYPE_COURT.name
            admission.admission_requirement_year = annee_diplome
        elif admission.training.education_group_type.name in MASTERS_TYPES:
            admission.admission_requirement = ConditionAcces.PASSERELLE.name
            admission.admission_requirement_year = annee_diplome
        else:
            admission.admission_requirement = ConditionAcces.INSUFFISANT.name
            admission.admission_requirement_year = None

    @classmethod
    def _compute_diplome_snu_long_1er_cycle(
        self, admission: GeneralEducationAdmission | DoctorateAdmission, annee_diplome
    ):
        if (
            admission.training.education_group_type.name
            in {
                TrainingType.BACHELOR.name,
                TrainingType.CERTIFICATE.name,
            }
            | MASTERS_TYPES
        ):
            admission.admission_requirement = ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.name
            admission.admission_requirement_year = annee_diplome
        else:
            admission.admission_requirement = ConditionAcces.INSUFFISANT.name
            admission.admission_requirement_year = None

    @classmethod
    def _compute_diplome_snu_long_2eme_cycle(
        self, admission: GeneralEducationAdmission | DoctorateAdmission, annee_diplome
    ):
        admission.admission_requirement = ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.name
        admission.admission_requirement_year = annee_diplome

    @classmethod
    def _compute_vae(cls, admission: GeneralEducationAdmission | DoctorateAdmission, access_titles):
        if (
            admission.training.education_group_type.name
            in {
                TrainingType.AGGREGATION.name,
            }
            | DOCTORATS_TYPES
        ):
            admission.admission_requirement = ConditionAcces.INSUFFISANT.name
            admission.admission_requirement_year = None
        else:
            admission.admission_requirement = ConditionAcces.VAE.name
            admission.admission_requirement_year = AcademicYear.objects.get(
                year=admission.training.academic_year.year - 1
            )

    @classmethod
    def _compute_diplome_acces_non_belge(cls, admission: GeneralEducationAdmission | DoctorateAdmission, access_titles):
        experiences_academiques = [
            experience[1]
            for experience in access_titles
            if experience[0] == TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE
            and experience[1].educationalexperience.country.iso_code != BE_ISO_CODE
        ]
        if not experiences_academiques or admission.training.education_group_type.name in [
            TrainingType.BACHELOR.name,
            TrainingType.AGGREGATION.name,
        ]:
            admission.admission_requirement = ConditionAcces.INSUFFISANT.name
            admission.admission_requirement_year = None
            return

        # Check we have all the needed information
        all_experiences_have_a_cycle = all(
            experience.educationalexperience.program is not None
            and bool(experience.educationalexperience.program.cycle)
            for experience in experiences_academiques
        )
        all_experiences_have_an_academic_year = all(
            experience.educationalexperience.program is not None
            and experience.educationalexperience.last_academic_year is not None
            for experience in experiences_academiques
        )
        if not all_experiences_have_a_cycle or not all_experiences_have_an_academic_year:
            admission.admission_requirement = ConditionAcces.INCOMPLET.name
            admission.admission_requirement_year = None
            return

        # Sort experiences by cycle and year to get the latest higher cycle one
        cycle_weight = {
            Cycle.FIRST_CYCLE.name: 1,
            Cycle.SECOND_CYCLE.name: 2,
            Cycle.THIRD_CYCLE.name: 3,
        }
        # Most recent highest cycle experience
        most_important_experience = sorted(
            experiences_academiques,
            key=lambda experience: (
                cycle_weight[experience.educationalexperience.program.cycle],
                experience.educationalexperience.last_academic_year.year,
            ),
        )[-1]
        if (
            admission.training.education_group_type.name
            in DOCTORATS_TYPES
            | {
                TrainingType.MASTER_MC.name,
                TrainingType.MASTER_M5.name,
            }
            and most_important_experience.educationalexperience.program.cycle == Cycle.FIRST_CYCLE.name
        ):
            admission.admission_requirement = ConditionAcces.INSUFFISANT.name
            admission.admission_requirement_year = None
        else:
            if admission.training.education_group_type.name in [
                TrainingType.MASTER_MC.name,
                TrainingType.MASTER_M5.name,
            ]:
                admission.admission_requirement = ConditionAcces.VALORISATION_240_ECTS.name
            elif admission.training.education_group_type.name in DOCTORATS_TYPES:
                admission.admission_requirement = ConditionAcces.VALORISATION_300_ECTS.name
            else:
                admission.admission_requirement = ConditionAcces.VALORISATION_180_ECTS.name
            admission.admission_requirement_year = most_important_experience.educationalexperience.last_academic_year

    @classmethod
    def _compute_single_access_title(
        cls,
        admission: GeneralEducationAdmission | DoctorateAdmission,
        access_title_type: TypeTitreAccesSelectionnable,
        access_title,
    ):
        # Avoid circular import
        from infrastructure.messages_bus import message_bus_instance

        if access_title_type == TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES:
            # Secondary study
            cls._compute_diplome_secondaire(admission)

        elif access_title_type == TypeTitreAccesSelectionnable.EXAMENS:
            # Exam
            exam = Exam.objects.filter(
                person=admission.candidate,
                type__education_group_years=admission.training,
            ).first()
            if exam is None:
                admission.admission_requirement = ConditionAcces.INCOMPLET.name
                admission.admission_requirement_year = None
                return
            cls._compute_examen(admission, exam)

        elif (
            access_title_type == TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE
            or access_title_type == TypeTitreAccesSelectionnable.EXPERIENCE_PARCOURS_INTERNE
        ):
            # Academic experience
            if access_title_type == TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE:
                experience = access_title.educationalexperience
                program = experience.program if experience.program else experience.fwb_equivalent_program
                experience_derniere_annee = experience.last_experience_year
                if experience_derniere_annee is None:
                    admission.admission_requirement = ConditionAcces.INCOMPLET.name
                    admission.admission_requirement_year = None
                    return

                est_diplomante = experience.obtained_diploma
                est_diplome_belge = experience.country.iso_code == BE_ISO_CODE
                est_1er_cycle = program.cycle == Cycle.FIRST_CYCLE.name
                est_2eme_cycle = program.cycle == Cycle.SECOND_CYCLE.name
                est_bama15 = (
                    est_1er_cycle and experience_derniere_annee.result == Result.SUCCESS_WITH_RESIDUAL_CREDITS.name
                )
                est_snu_court = (
                    program.study_type == StudyType.NON_UNIVERSITY.name
                    and program.duration_type == DurationType.SHORT.name
                )
                est_snu_long = (
                    program.study_type == StudyType.NON_UNIVERSITY.name
                    and program.duration_type == DurationType.LONG.name
                )
                annee_diplome = experience.last_academic_year
            else:
                sigle_formation = access_title.sigle_formation
                annee_formation = access_title.annee_formation
                formation = (
                    EducationGroupYear.objects.select_related('education_group_type')
                    .filter(
                        acronym=sigle_formation,
                        academic_year__year=annee_formation,
                    )
                    .first()
                )
                if (
                    formation is None
                    or formation.education_group_type is None
                    or formation.education_group_type.cycle is None
                ):
                    admission.admission_requirement = ConditionAcces.INCOMPLET.name
                    admission.admission_requirement_year = None
                    return

                try:
                    deliberations = message_bus_instance.invoke(
                        RechercherDeliberationsProgrammesAnnuelsActeesQuery(
                            nomas=[admission.student_registration_id],  # From annotation
                            annee=annee_formation,
                            sigle_formation=sigle_formation,
                        )
                    )
                except Exception as e:
                    admission.admission_requirement = ConditionAcces.INCOMPLET.name
                    admission.admission_requirement_year = None
                    return

                est_diplomante = any(deliberation.decision == Decision.REUSSITE.name for deliberation in deliberations)
                est_diplome_belge = True
                est_1er_cycle = formation.education_group_type.cycle == 1
                est_2eme_cycle = formation.education_group_type.cycle == 2
                est_bama15 = any(
                    deliberation.etat_cycle_annualise.bama15 == BAMA15.EST_BAMA15.name for deliberation in deliberations
                )
                est_snu_court = False
                est_snu_long = False
                annee_diplome = AcademicYear.objects.get(year=annee_formation)

            if not est_diplomante:
                admission.admission_requirement = ConditionAcces.INSUFFISANT.name
                admission.admission_requirement_year = None
            if est_diplome_belge and est_1er_cycle and not est_bama15 and not est_snu_court and not est_snu_long:
                cls._compute_diplome_1er_cycle(admission, annee_diplome)
            elif est_diplome_belge and est_2eme_cycle and not est_bama15 and not est_snu_court and not est_snu_long:
                cls._compute_diplome_2eme_cycle(admission, annee_diplome)
            elif est_diplome_belge and est_bama15:
                cls._compute_bama15_1er_cycle(admission, annee_diplome)
            elif est_diplome_belge and est_snu_court:
                cls._compute_diplome_snu_court(admission, annee_diplome)
            elif est_diplome_belge and est_snu_long and est_1er_cycle:
                cls._compute_diplome_snu_long_1er_cycle(admission, annee_diplome)
            elif est_diplome_belge and est_snu_long and est_2eme_cycle:
                cls._compute_diplome_snu_long_2eme_cycle(admission, annee_diplome)
            else:
                admission.admission_requirement = ConditionAcces.INSUFFISANT.name
                admission.admission_requirement_year = None
        else:
            # Non academic experiences, we need several titles selected
            admission.admission_requirement = ConditionAcces.INSUFFISANT.name
            admission.admission_requirement_year = None

    @classmethod
    def _compute_admission_requirement(cls, admission: GeneralEducationAdmission | DoctorateAdmission):
        access_titles = []

        # Get all access titles as 2-tuples (type, experience_instance)
        if admission.are_secondary_studies_access_title:
            access_titles.append((TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES, None))
        if admission.is_exam_access_title:
            access_titles.append((TypeTitreAccesSelectionnable.EXAMENS, None))
        for experience in admission.admissioneducationalvaluatedexperiences_set.all():
            if experience.is_access_title:
                access_titles.append((TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE, experience))
        for experience in admission.admissionprofessionalvaluatedexperiences_set.all():
            if experience.is_access_title:
                access_titles.append((TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE, experience))
        for experience in admission.internal_access_titles.all():
            access_titles.append((TypeTitreAccesSelectionnable.EXPERIENCE_PARCOURS_INTERNE, experience))

        # Computing admission requirements
        if not access_titles:
            # No access title selected
            admission.admission_requirement = ''
            admission.admission_requirement_year = None

        elif len(access_titles) == 1:
            # A single access title selected
            access_title_type, access_title = access_titles[0]
            cls._compute_single_access_title(admission, access_title_type, access_title)

        else:
            # More than one access title selected
            has_non_academic_access_title = any(
                admission_requirement[0] == TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE
                for admission_requirement in access_titles
            )
            if has_non_academic_access_title:
                cls._compute_vae(admission, access_titles)
            else:
                cls._compute_diplome_acces_non_belge(admission, access_titles)

        admission.save(update_fields=['admission_requirement', 'admission_requirement_year'])

    @classmethod
    def _get_queryset(cls, manager):
        return (
            manager.annotate_with_student_registration_id()
            .select_related(
                'candidate',
                'candidate__foreignhighschooldiploma__academic_graduation_year',
                'candidate__belgianhighschooldiploma__academic_graduation_year',
                'training',
            )
            .prefetch_related(
                Prefetch(
                    'admissioneducationalvaluatedexperiences_set',
                    queryset=AdmissionEducationalValuatedExperiences.objects.select_related(
                        'educationalexperience',
                        'educationalexperience__program',
                        'educationalexperience__fwb_equivalent_program',
                        'educationalexperience__country',
                    ).prefetch_related(
                        Prefetch(
                            'educationalexperience__educationalexperienceyear_set',
                            queryset=EducationalExperienceYear.objects.select_related('academic_year'),
                        ),
                    ),
                ),
                Prefetch(
                    'admissionprofessionalvaluatedexperiences_set',
                    queryset=AdmissionProfessionalValuatedExperiences.objects.select_related('professionalexperience'),
                ),
                'internal_access_titles',
            )
        )

    @classmethod
    def calculer_condition_d_acces(cls, proposition_id: PropositionIdentity):
        try:
            current_admission = cls._get_queryset(GeneralEducationAdmission.objects).get(uuid=proposition_id.uuid)
        except GeneralEducationAdmission.DoesNotExist:
            try:
                current_admission = cls._get_queryset(DoctorateAdmission.objects).get(uuid=proposition_id.uuid)
            except DoctorateAdmission.DoesNotExist:
                raise PropositionNonTrouveeException

        cls._compute_admission_requirement(current_admission)
