# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

from django.db.models import QuerySet
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models import GeneralEducationAdmission, ContinuingEducationAdmission
from admission.ddd.admission.domain.validator.exceptions import BourseNonTrouveeException
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutProposition
from admission.ddd.admission.formation_continue.domain.validator.exceptions import FormationNonTrouveeException
from admission.tests.factories.continuing_education import ContinuingEducationTrainingFactory
from admission.tests.factories.scholarship import (
    ErasmusMundusScholarship,
    InternationalScholarship,
    DoubleDegreeScholarship,
)
from base.tests.factories.education_group_year import Master120TrainingFactory

from base.tests.factories.person import PersonFactory


class GeneralEducationAdmissionTrainingChoiceInitializationApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        cls.training = Master120TrainingFactory()
        cls.erasmus_mundus_scholarship = ErasmusMundusScholarship()
        cls.international_scholarship = InternationalScholarship()
        cls.double_degree_scholarship = DoubleDegreeScholarship()

        cls.create_data = {
            'sigle_formation': cls.training.acronym,
            'annee_formation': cls.training.academic_year.year,
            'matricule_candidat': cls.candidate.global_id,
            'bourse_erasmus_mundus': str(cls.erasmus_mundus_scholarship.uuid),
            'bourse_internationale': str(cls.international_scholarship.uuid),
            'bourse_double_diplome': str(cls.double_degree_scholarship.uuid),
        }

        cls.url = resolve_url('admission_api_v1:general_training_choice')

    def test_training_choice_initialization_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        admissions: QuerySet[GeneralEducationAdmission] = GeneralEducationAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)

        admission = admissions.get(uuid=response.data['uuid'])
        self.assertEqual(admission.training_id, self.training.pk)
        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.international_scholarship_id, self.international_scholarship.pk)
        self.assertEqual(admission.erasmus_mundus_scholarship_id, self.erasmus_mundus_scholarship.pk)
        self.assertEqual(admission.double_degree_scholarship_id, self.double_degree_scholarship.pk)
        self.assertEqual(admission.status, ChoixStatutProposition.IN_PROGRESS.name)

    def test_training_choice_initialization_using_api_candidate_with_wrong_training(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, 'sigle_formation': 'UNKONWN'}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            FormationNonTrouveeException.status_code,
        )

    def test_training_choice_initialization_using_api_candidate_with_wrong_scholarship(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, 'bourse_erasmus_mundus': str(uuid.uuid4())}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], BourseNonTrouveeException.status_code)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ContinuingEducationAdmissionTrainingChoiceInitializationApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        cls.training = ContinuingEducationTrainingFactory()
        cls.create_data = {
            'sigle_formation': cls.training.acronym,
            'annee_formation': cls.training.academic_year.year,
            'matricule_candidat': cls.candidate.global_id,
        }

        cls.url = resolve_url('admission_api_v1:continuing_training_choice')

    def test_training_choice_initialization_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        admissions: QuerySet[ContinuingEducationAdmission] = ContinuingEducationAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)

        admission = admissions.get(uuid=response.data['uuid'])
        self.assertEqual(admission.training_id, self.training.pk)
        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.status, ChoixStatutProposition.IN_PROGRESS.name)

    def test_training_choice_initialization_using_api_candidate_with_wrong_training(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, 'sigle_formation': 'UNKONWN'}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            FormationNonTrouveeException.status_code,
        )

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
