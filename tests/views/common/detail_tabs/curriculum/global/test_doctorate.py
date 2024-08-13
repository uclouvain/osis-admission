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
import datetime
import uuid

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.contrib.models import DoctorateAdmission
from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import (
    ProfessionalExperienceFactory,
    AdmissionEducationalValuatedExperiencesFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
)
from admission.tests.factories.roles import ProgramManagerRoleFactory, CentralManagerRoleFactory
from base.models.enums.teaching_type import TeachingTypeEnum
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from osis_profile import BE_ISO_CODE
from osis_profile.models import EducationalExperienceYear, EducationalExperience, ProfessionalExperience
from osis_profile.models.enums.curriculum import (
    EvaluationSystem,
    TranscriptType,
    Grade,
    Result,
    Reduction,
    ActivityType,
    ActivitySector,
)
from osis_profile.tests.factories.curriculum import EducationalExperienceFactory, EducationalExperienceYearFactory
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.diploma_title import DiplomaTitleFactory
from reference.tests.factories.language import LanguageFactory
from reference.tests.factories.superior_non_university import SuperiorNonUniversityFactory


@freezegun.freeze_time('2024-06-01')
class CurriculumGlobalDetailsViewForDoctorateTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]
        cls.entity = EntityVersionFactory().entity
        cls.sic_manager_user = CentralManagerRoleFactory(entity=cls.entity).person.user
        cls.be_country = CountryFactory(iso_code=BE_ISO_CODE, name='Belgique', name_en='Belgium')
        cls.foreign_country = CountryFactory(iso_code=FR_ISO_CODE, name='France', name_en='France')
        cls.diploma = DiplomaTitleFactory()
        cls.other_diploma = DiplomaTitleFactory()
        cls.linguistic_regime = LanguageFactory(code=FR_ISO_CODE)
        cls.institute = SuperiorNonUniversityFactory(teaching_type=TeachingTypeEnum.SOCIAL_PROMOTION.name)

    def setUp(self):
        self.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=self.entity,
            training__academic_year=self.academic_years[1],
            curriculum=[],
        )

        self.fac_manager_user = ProgramManagerRoleFactory(
            education_group=self.doctorate_admission.training.education_group,
        ).person.user

        self.url = resolve_url('admission:doctorate:curriculum', uuid=self.doctorate_admission.uuid)

    def test_get_curriculum_with_sic_manager_user(self):
        self.client.force_login(user=self.sic_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_curriculum_with_fac_manager_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        curriculum: CurriculumAdmissionDTO = response.context['curriculum']
        self.assertEqual(curriculum.experiences_academiques, [])
        self.assertEqual(curriculum.experiences_non_academiques, [])
        self.assertEqual(curriculum.annee_minimum_a_remplir, 2019)
        self.assertEqual(curriculum.annee_derniere_inscription_ucl, None)
        self.assertEqual(curriculum.annee_diplome_etudes_secondaires, None)

        self.assertTrue(response.context['display_curriculum'])
        self.assertFalse(response.context['display_equivalence'])

    def test_get_curriculum_with_academic_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        educational_experience: EducationalExperience = EducationalExperienceFactory(
            person=self.doctorate_admission.candidate,
            country=self.foreign_country,
            institute=None,
            institute_address='My custom institute address',
            institute_name='My custom institute name',
            program=None,
            fwb_equivalent_program=None,
            education_name='My custom program name',
            study_system=TeachingTypeEnum.SOCIAL_PROMOTION.name,
            evaluation_type=EvaluationSystem.ECTS_CREDITS.name,
            linguistic_regime=None,
            transcript_type=TranscriptType.ONE_FOR_ALL_YEARS.name,
            obtained_diploma=True,
            obtained_grade=Grade.DISTINCTION.name,
            graduate_degree=[uuid.uuid4()],
            graduate_degree_translation=[uuid.uuid4()],
            transcript=[uuid.uuid4()],
            transcript_translation=[uuid.uuid4()],
            rank_in_diploma='50/100',
            expected_graduation_date=datetime.date(2024, 1, 1),
            dissertation_title='Dissertation title',
            dissertation_score='15/20',
            dissertation_summary=[uuid.uuid4()],
        )

        educational_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=educational_experience,
            academic_year=self.academic_years[1],
            registered_credit_number=20,
            acquired_credit_number=19,
            result=Result.SUCCESS.name,
            transcript=[uuid.uuid4()],
            transcript_translation=[uuid.uuid4()],
            with_block_1=True,
            with_complement=True,
            fwb_registered_credit_number=30,
            fwb_acquired_credit_number=29,
            reduction=Reduction.A150.name,
            is_102_change_of_course=True,
        )

        # There is an experience but not valuated, so we don't display it
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        curriculum: CurriculumAdmissionDTO = response.context['curriculum']
        self.assertEqual(len(curriculum.experiences_academiques), 0)

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.doctorate_admission,
            educationalexperience=educational_experience,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        curriculum: CurriculumAdmissionDTO = response.context['curriculum']
        self.assertEqual(len(curriculum.experiences_academiques), 1)

        experience = curriculum.experiences_academiques[0]
        self.assertEqual(experience.uuid, educational_experience.uuid)
        self.assertEqual(len(experience.annees), 1)

        annee = experience.annees[0]
        self.assertEqual(annee.uuid, educational_experience_year.uuid)

    def test_get_curriculum_with_non_academic_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        non_academic_experience: ProfessionalExperience = ProfessionalExperienceFactory(
            person=self.doctorate_admission.candidate,
            institute_name='My custom institute name',
            start_date=datetime.date(2000, 1, 1),
            end_date=datetime.date(2001, 1, 31),
            type=ActivityType.WORK.name,
            certificate=[uuid.uuid4()],
            role='Role',
            sector=ActivitySector.PUBLIC.name,
            activity='My custom activity',
        )

        # There is an experience but not valuated, so we don't display it
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        curriculum: CurriculumAdmissionDTO = response.context['curriculum']
        self.assertEqual(len(curriculum.experiences_non_academiques), 0)

        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=self.doctorate_admission,
            professionalexperience=non_academic_experience,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        curriculum: CurriculumAdmissionDTO = response.context['curriculum']
        self.assertEqual(len(curriculum.experiences_non_academiques), 1)

        experience = curriculum.experiences_non_academiques[0]

        self.assertEqual(experience.uuid, non_academic_experience.uuid)
