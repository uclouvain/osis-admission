# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.enums import Onglets
from admission.tests.factories.form_item import AdmissionFormItemInstantiationFactory, MessageAdmissionFormItemFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import (
    SicManagementRoleFactory,
    CandidateFactory,
    ProgramManagerRoleFactory,
)
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from reference.tests.factories.country import CountryFactory


class TrainingChoiceDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')

        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(
            entity=first_doctoral_commission,
        )

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            admitted=True,
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
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group
        ).person.user

        cls.url = resolve_url('admission:general-education:training-choice', uuid=cls.general_admission.uuid)

    def test_general_training_choice_access(self):
        # If the user is not authenticated, they should be redirected to the login page
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + self.url)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, they should be able to access the page
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_general_training_choice(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)

        specific_questions: List[QuestionSpecifiqueDTO] = response.context.get('specific_questions', [])
        self.assertEqual(len(specific_questions), 1)
        self.assertEqual(specific_questions[0].uuid, str(self.specific_questions[0].form_item.uuid))
