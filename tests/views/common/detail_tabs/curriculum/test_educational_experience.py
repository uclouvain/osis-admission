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
import uuid
from unittest.mock import patch

from django.shortcuts import resolve_url
from django.test import TestCase

from admission.contrib.models import ContinuingEducationAdmission, GeneralEducationAdmission
from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.curriculum import EducationalExperienceFactory, EducationalExperienceYearFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import (
    SicManagementRoleFactory,
    ProgramManagerRoleFactory,
    CandidateFactory,
)
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO
from osis_profile.models import EducationalExperience, EducationalExperienceYear
from reference.tests.factories.country import CountryFactory
from django.test import override_settings

from reference.tests.factories.language import LanguageFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class CurriculumEducationalExperienceDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.be_country = CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')
        cls.linguistic_regime = LanguageFactory(code=FR_ISO_CODE)

        cls.entity = EntityVersionFactory().entity

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.entity).person.user

        cls.candidate = CandidateFactory().person

        cls.educational_experience: EducationalExperience = EducationalExperienceFactory(
            person=cls.candidate,
            linguistic_regime=cls.linguistic_regime,
            country=cls.be_country,
        )

        cls.educational_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=cls.educational_experience,
            academic_year=academic_years[0],
        )

        cls.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=cls.entity,
            training__academic_year=academic_years[0],
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            candidate=cls.candidate,
        )

        cls.continuing_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.continuing_admission.training.education_group,
        ).person.user

        cls.continuing_url = resolve_url(
            'admission:continuing-education:curriculum:educational',
            uuid=cls.continuing_admission.uuid,
            experience_uuid=cls.educational_experience.uuid,
        )

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=cls.entity,
            training__academic_year=academic_years[0],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            candidate=cls.candidate,
        )

        cls.general_url = resolve_url(
            'admission:general-education:curriculum:educational',
            uuid=cls.general_admission.uuid,
            experience_uuid=cls.educational_experience.uuid,
        )

        cls.general_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user

    def setUp(self):
        # Mock documents
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'size': 1, 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_general_with_program_manager(self):
        self.client.force_login(user=self.general_program_manager_user)
        response = self.client.get(self.general_url)
        self.assertEqual(response.status_code, 200)

    def test_general_with_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)
        response = self.client.get(self.general_url)
        self.assertEqual(response.status_code, 200)

    def test_continuing_with_program_manager(self):
        self.client.force_login(user=self.continuing_program_manager_user)
        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, 200)

    def test_continuing_with_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)
        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, 200)

        experience = response.context['experience']

        self.assertIsInstance(experience, ExperienceAcademiqueDTO)
        self.assertEqual(experience.uuid, self.educational_experience.uuid)
        self.assertFalse(response.context['translation_required'])
        self.assertFalse(response.context['is_foreign_experience'])
        self.assertFalse(response.context['evaluation_system_with_credits'])
        self.assertTrue(response.context['is_belgian_experience'])
        self.assertEqual(
            response.context['edit_url'],
            f'/admissions/continuing-education/{self.continuing_admission.uuid}/update/curriculum/educational/'
            f'{self.educational_experience.uuid}',
        )

    def test_continuing_with_unknown_experience(self):
        self.client.force_login(user=self.sic_manager_user)
        response = self.client.get(
            resolve_url(
                'admission:continuing-education:curriculum:educational',
                uuid=self.continuing_admission.uuid,
                experience_uuid=uuid.uuid4(),
            )
        )
        self.assertEqual(response.status_code, 404)
