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
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity as PropositionIdentityDoctorat,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.shared_kernel.domain.service.conditions_d_acces import ConditionDAcces
from admission.infrastructure.admission.doctorat.preparation.repository.proposition import (
    PropositionRepository as PropositionRepositoryDoctorat,
)
from admission.infrastructure.admission.formation_generale.repository.proposition import PropositionRepository
from admission.infrastructure.admission.shared_kernel.domain.service.calcul_condition_acces_translator import (
    CalculConditionAccesTranslator,
)
from admission.models.base import BaseAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import (
    AdmissionEducationalValuatedExperiencesFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
    ProfessionalExperienceFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.secondary_studies import BelgianHighSchoolDiplomaFactory
from base.models.academic_year import AcademicYear
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from epc.models.enums.condition_acces import ConditionAcces
from osis_profile import BE_ISO_CODE
from osis_profile.models.enums.curriculum import Result
from osis_profile.tests.factories.exam import ExamFactory
from reference.models.enums.cycle import Cycle
from reference.models.enums.duration_type import DurationType
from reference.models.enums.study_type import StudyType
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.diploma_title import DiplomaTitleFactory


class ComputeAdmissionRequirementTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        AcademicYearFactory.produce(2025, 2, 2)
        cls.country_be = CountryFactory(iso_code=BE_ISO_CODE)

    def test_aucun_titre_d_acces(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.BACHELOR.name)

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, '')
        self.assertIsNone(admission.admission_requirement_year)

    def test_secondaire_bachelier(self):
        admission = GeneralEducationAdmissionFactory(
            are_secondary_studies_access_title=True,
            training__education_group_type__name=TrainingType.BACHELOR.name,
        )
        BelgianHighSchoolDiplomaFactory(
            person=admission.candidate,
            academic_graduation_year__year=2025,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.SECONDAIRE.name)
        self.assertEqual(admission.admission_requirement_year.year, 2025)

    def test_secondaire_master(self):
        admission = GeneralEducationAdmissionFactory(
            are_secondary_studies_access_title=True,
            training__education_group_type__name=TrainingType.MASTER_M1.name,
        )
        BelgianHighSchoolDiplomaFactory(person=admission.candidate)

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.INSUFFISANT.name)
        self.assertIsNone(admission.admission_requirement_year)

    def test_examen_bachelier(self):
        admission = GeneralEducationAdmissionFactory(
            is_exam_access_title=True,
            training__education_group_type__name=TrainingType.BACHELOR.name,
        )
        ExamFactory(
            person=admission.candidate,
            type__education_group_years=[admission.training],
            year=AcademicYear.objects.get(year=2025),
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.EXAMEN_ADMISSION.name)
        self.assertEqual(admission.admission_requirement_year.year, 2025)

    def test_examen_master(self):
        admission = GeneralEducationAdmissionFactory(
            is_exam_access_title=True,
            training__education_group_type__name=TrainingType.MASTER_M1.name,
        )
        ExamFactory(
            person=admission.candidate,
            type__education_group_years=[admission.training],
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.INSUFFISANT.name)
        self.assertIsNone(admission.admission_requirement_year)

    def test_diplome_1er_cycle_master(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.MASTER_M1.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, country=self.country_be, with_fwb_bachelor_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2025)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.BAC.name)
        self.assertEqual(admission.admission_requirement_year.year, 2025)

    def test_diplome_2eme_cycle_master(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.MASTER_MC.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, country=self.country_be, with_fwb_master_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2025)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.MASTER.name)
        self.assertEqual(admission.admission_requirement_year.year, 2025)

    def test_bama15_master(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.MASTER_M1.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate,
            country=self.country_be,
            with_fwb_bachelor_fields=True,
            obtained_diploma=True,
        )
        EducationalExperienceYearFactory(
            educational_experience=educational_experience,
            academic_year__year=2025,
            result=Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
        )
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.BAMA15.name)
        self.assertEqual(admission.admission_requirement_year.year, 2025)

    def test_snu_court_bachelier(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.BACHELOR.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate,
            program=DiplomaTitleFactory(
                cycle=Cycle.FIRST_CYCLE.name,
                study_type=StudyType.NON_UNIVERSITY.name,
                duration_type=DurationType.SHORT.name,
            ),
            obtained_diploma=True,
            country=self.country_be,
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2025)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.SNU_TYPE_COURT.name)
        self.assertEqual(admission.admission_requirement_year.year, 2025)

    def test_snu_court_master(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.MASTER_M1.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate,
            program=DiplomaTitleFactory(
                cycle=Cycle.FIRST_CYCLE.name,
                study_type=StudyType.NON_UNIVERSITY.name,
                duration_type=DurationType.SHORT.name,
            ),
            obtained_diploma=True,
            country=self.country_be,
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2025)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.PASSERELLE.name)
        self.assertEqual(admission.admission_requirement_year.year, 2025)

    def test_snu_long_1er_cycle_master(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.BACHELOR.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate,
            program=DiplomaTitleFactory(
                cycle=Cycle.FIRST_CYCLE.name,
                study_type=StudyType.NON_UNIVERSITY.name,
                duration_type=DurationType.LONG.name,
            ),
            obtained_diploma=True,
            country=self.country_be,
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2025)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.name)
        self.assertEqual(admission.admission_requirement_year.year, 2025)

    def test_snu_long_2eme_cycle_master(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.BACHELOR.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate,
            program=DiplomaTitleFactory(
                cycle=Cycle.SECOND_CYCLE.name,
                study_type=StudyType.NON_UNIVERSITY.name,
                duration_type=DurationType.LONG.name,
            ),
            obtained_diploma=True,
            country=self.country_be,
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2025)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.name)
        self.assertEqual(admission.admission_requirement_year.year, 2025)

    def test_un_seul_titre_non_academique(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.BACHELOR.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=base_admission,
            professionalexperience=ProfessionalExperienceFactory(person=admission.candidate),
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.INSUFFISANT.name)
        self.assertIsNone(admission.admission_requirement_year)

    def test_vae(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.BACHELOR.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=base_admission,
            professionalexperience=ProfessionalExperienceFactory(person=admission.candidate),
            is_access_title=True,
        )
        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=base_admission,
            professionalexperience=ProfessionalExperienceFactory(person=admission.candidate),
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.VAE.name)
        self.assertEqual(admission.admission_requirement_year.year, admission.training.academic_year.year - 1)

    def test_diplomes_non_belge(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.MASTER_M1.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, with_fwb_bachelor_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2025)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, with_fwb_bachelor_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2024)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.VALORISATION_180_ECTS.name)
        self.assertEqual(admission.admission_requirement_year.year, 2025)

    def test_diplomes_non_belge_mc_premier_cycle(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.MASTER_MC.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, country=self.country_be, with_fwb_bachelor_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2025)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, country=self.country_be, with_fwb_bachelor_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2024)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.INSUFFISANT.name)
        self.assertIsNone(admission.admission_requirement_year)

    def test_diplomes_non_belge_mc_second_cycle(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.MASTER_MC.name)
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, country=self.country_be, with_fwb_bachelor_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2025)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, with_fwb_master_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2024)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepository.get(PropositionIdentity(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.VALORISATION_240_ECTS.name)
        self.assertEqual(admission.admission_requirement_year.year, 2024)

    def test_diplomes_non_belge_doctorat_premier_cycle(self):
        admission = DoctorateAdmissionFactory()
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, country=self.country_be, with_fwb_bachelor_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2025)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, country=self.country_be, with_fwb_bachelor_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2024)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepositoryDoctorat.get(PropositionIdentityDoctorat(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.INSUFFISANT.name)
        self.assertIsNone(admission.admission_requirement_year)

    def test_diplomes_non_belge_doctorat_second_cycle(self):
        admission = DoctorateAdmissionFactory()
        base_admission = BaseAdmission.objects.get(id=admission.id)
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, with_fwb_bachelor_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2025)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )
        educational_experience = EducationalExperienceFactory(
            person=admission.candidate, with_fwb_master_fields=True, obtained_diploma=True
        )
        EducationalExperienceYearFactory(educational_experience=educational_experience, academic_year__year=2024)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=base_admission,
            educationalexperience=educational_experience,
            is_access_title=True,
        )

        proposition = PropositionRepositoryDoctorat.get(PropositionIdentityDoctorat(uuid=str(admission.uuid)))
        ConditionDAcces.calculer_condition_d_acces(
            proposition, calcul_condition_acces_translator=CalculConditionAccesTranslator
        )
        admission.refresh_from_db()

        self.assertEqual(admission.admission_requirement, ConditionAcces.VALORISATION_300_ECTS.name)
        self.assertEqual(admission.admission_requirement_year.year, 2024)
