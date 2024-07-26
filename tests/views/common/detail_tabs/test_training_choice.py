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
from typing import List

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.models import GeneralEducationAdmission, ContinuingEducationAdmission, DoctorateAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.form_item import AdmissionFormItemInstantiationFactory, MessageAdmissionFormItemFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import (
    SicManagementRoleFactory,
    CandidateFactory,
    ProgramManagerRoleFactory,
)
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from reference.tests.factories.country import CountryFactory


class TrainingChoiceDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')

        general_entity = EntityVersionFactory().entity
        continuing_entity = EntityVersionFactory().entity
        doctorate_entity = EntityVersionFactory().entity

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=general_entity,
            training__academic_year=academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            admitted=True,
        )

        cls.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=continuing_entity,
            training__academic_year=academic_years[0],
            determined_academic_year=cls.general_admission.determined_academic_year,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )

        cls.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=doctorate_entity,
            training__academic_year=academic_years[0],
            determined_academic_year=cls.general_admission.determined_academic_year,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        cls.specific_questions = [
            AdmissionFormItemInstantiationFactory(
                form_item=MessageAdmissionFormItemFactory(),
                tab=Onglets.CHOIX_FORMATION.name,
                academic_year=cls.general_admission.determined_academic_year,
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=MessageAdmissionFormItemFactory(),
                tab=Onglets.CURRICULUM.name,
                academic_year=cls.general_admission.determined_academic_year,
            ),
        ]

        # Create users
        cls.general_sic_manager_user = SicManagementRoleFactory(entity=general_entity).person.user
        cls.general_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group
        ).person.user

        cls.continuing_sic_manager_user = SicManagementRoleFactory(entity=continuing_entity).person.user
        cls.continuing_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.continuing_admission.training.education_group
        ).person.user

        cls.doctorate_sic_manager_user = SicManagementRoleFactory(entity=doctorate_entity).person.user
        cls.doctorate_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.doctorate_admission.training.education_group
        ).person.user

        cls.general_url = resolve_url('admission:general-education:training-choice', uuid=cls.general_admission.uuid)

        cls.continuing_url = resolve_url(
            'admission:continuing-education:training-choice',
            uuid=cls.continuing_admission.uuid,
        )

        cls.doctorate_url = resolve_url('admission:doctorate:training-choice', uuid=cls.doctorate_admission.uuid)

    def test_general_training_choice_access(self):
        # If the user is not authenticated, they should be redirected to the login page
        response = self.client.get(self.general_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + self.general_url)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(self.general_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.continuing_sic_manager_user)
        response = self.client.get(self.general_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.continuing_program_manager_user)
        response = self.client.get(self.general_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.doctorate_sic_manager_user)
        response = self.client.get(self.general_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.doctorate_program_manager_user)
        response = self.client.get(self.general_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, they should be able to access the page
        self.client.force_login(self.general_sic_manager_user)
        response = self.client.get(self.general_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_login(self.general_sic_manager_user)
        response = self.client.get(self.general_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_general_training_choice(self):
        self.client.force_login(self.general_sic_manager_user)
        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)

        specific_questions: List[QuestionSpecifiqueDTO] = response.context.get('specific_questions', [])
        self.assertEqual(len(specific_questions), 1)
        self.assertEqual(specific_questions[0].uuid, str(self.specific_questions[0].form_item.uuid))

    def test_continuing_training_choice_access(self):
        # If the user is not authenticated, they should be redirected to the login page
        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + self.continuing_url)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.general_sic_manager_user)
        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.general_program_manager_user)
        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.doctorate_sic_manager_user)
        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.doctorate_program_manager_user)
        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, they should be able to access the page
        self.client.force_login(self.continuing_sic_manager_user)
        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_login(self.continuing_program_manager_user)
        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_continuing_training_choice(self):
        self.client.force_login(self.continuing_sic_manager_user)
        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['admission'].uuid, self.continuing_admission.uuid)

        specific_questions: List[QuestionSpecifiqueDTO] = response.context.get('specific_questions', [])
        self.assertEqual(len(specific_questions), 1)
        self.assertEqual(specific_questions[0].uuid, str(self.specific_questions[0].form_item.uuid))

    def test_doctorate_training_choice_access(self):
        # If the user is not authenticated, they should be redirected to the login page
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + self.doctorate_url)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.general_sic_manager_user)
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.general_program_manager_user)
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.continuing_sic_manager_user)
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.continuing_program_manager_user)
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, they should be able to access the page
        self.client.force_login(self.doctorate_sic_manager_user)
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_login(self.doctorate_program_manager_user)
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_doctorate_training_choice(self):
        self.client.force_login(self.doctorate_sic_manager_user)
        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['admission'].uuid, self.doctorate_admission.uuid)

        specific_questions: List[QuestionSpecifiqueDTO] = response.context.get('specific_questions', [])
        self.assertEqual(len(specific_questions), 1)
        self.assertEqual(specific_questions[0].uuid, str(self.specific_questions[0].form_item.uuid))
