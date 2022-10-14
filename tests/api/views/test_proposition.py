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
from django.shortcuts import resolve_url
from rest_framework import status

from admission.contrib.models import GeneralEducationAdmission, ContinuingEducationAdmission
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionFormationGenerale,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionFormationContinue,
)
from admission.tests import CheckActionLinksMixin
from rest_framework.test import APITestCase

from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory
from base.tests.factories.person import PersonFactory


class GeneralPropositionViewSetApiTestCase(CheckActionLinksMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admission = GeneralEducationAdmissionFactory()
        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate = CandidateFactory().person
        cls.no_role_user = PersonFactory().user

        cls.url = resolve_url("admission_api_v1:general_propositions", uuid=str(cls.admission.uuid))

    def test_get_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        json_response = response.json()
        training_json = {
            'sigle': self.admission.training.acronym,
            'annee': self.admission.training.academic_year.year,
            'intitule': self.admission.training.title,
            'campus': self.admission.training.enrollment_campus.name,
        }
        double_degree_scholarship_json = {
            'uuid': str(self.admission.double_degree_scholarship.uuid),
            'nom_court': self.admission.double_degree_scholarship.short_name,
            'nom_long': self.admission.double_degree_scholarship.long_name,
            'type': self.admission.double_degree_scholarship.type,
        }
        international_scholarship_json = {
            'uuid': str(self.admission.international_scholarship.uuid),
            'nom_court': self.admission.international_scholarship.short_name,
            'nom_long': self.admission.international_scholarship.long_name,
            'type': self.admission.international_scholarship.type,
        }
        erasmus_mundus_scholarship_json = {
            'uuid': str(self.admission.erasmus_mundus_scholarship.uuid),
            'nom_court': self.admission.erasmus_mundus_scholarship.short_name,
            'nom_long': self.admission.erasmus_mundus_scholarship.long_name,
            'type': self.admission.erasmus_mundus_scholarship.type,
        }
        self.assertEqual(json_response['uuid'], str(self.admission.uuid))
        self.assertEqual(json_response['formation'], training_json)
        self.assertEqual(json_response['matricule_candidat'], self.admission.candidate.global_id)
        self.assertEqual(json_response['prenom_candidat'], self.admission.candidate.first_name)
        self.assertEqual(json_response['nom_candidat'], self.admission.candidate.last_name)
        self.assertEqual(json_response['statut'], self.admission.status)
        self.assertEqual(json_response['bourse_double_diplome'], double_degree_scholarship_json)
        self.assertEqual(json_response['bourse_internationale'], international_scholarship_json)
        self.assertEqual(json_response['bourse_erasmus_mundus'], erasmus_mundus_scholarship_json)
        self.assertEqual(json_response['erreurs'], [])
        self.assertActionLinks(
            links=json_response['links'],
            allowed_actions=[
                'retrieve_person',
                'retrieve_coordinates',
                'retrieve_secondary_studies',
                'retrieve_curriculum',
                'retrieve_training_choice',
                'update_person',
                'update_coordinates',
                'update_secondary_studies',
                'update_curriculum',
                'update_training_choice',
                'destroy_proposition',
            ],
            forbidden_actions=[],
        )

    def test_get_proposition_other_candidate_is_forbidden(self):
        self.client.force_authenticate(user=self.other_candidate.user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_proposition_no_role_user_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)

        # Create a new admission
        admission = GeneralEducationAdmissionFactory(candidate=self.candidate)
        self.assertEqual(admission.status, ChoixStatutPropositionFormationGenerale.IN_PROGRESS.name)

        # Cancel it
        admission_to_cancel_url = resolve_url("admission_api_v1:general_propositions", uuid=str(admission.uuid))
        response = self.client.delete(admission_to_cancel_url, format="json")

        self.assertEqual(response.json()['uuid'], str(admission.uuid))

        admission = GeneralEducationAdmission.objects.get(pk=admission.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionFormationGenerale.CANCELLED.name)

    def test_delete_proposition_other_candidate_is_forbidden(self):
        self.client.force_authenticate(user=self.other_candidate.user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_proposition_no_role_user_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)


class ContinuingPropositionViewSetApiTestCase(CheckActionLinksMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admission = ContinuingEducationAdmissionFactory()
        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate = CandidateFactory().person
        cls.no_role_user = PersonFactory().user

        cls.url = resolve_url("admission_api_v1:continuing_propositions", uuid=str(cls.admission.uuid))

    def test_get_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        json_response = response.json()
        training_json = {
            'sigle': self.admission.training.acronym,
            'annee': self.admission.training.academic_year.year,
            'intitule': self.admission.training.title,
            'campus': self.admission.training.enrollment_campus.name,
        }
        self.assertEqual(json_response['uuid'], str(self.admission.uuid))
        self.assertEqual(json_response['formation'], training_json)
        self.assertEqual(json_response['matricule_candidat'], self.admission.candidate.global_id)
        self.assertEqual(json_response['prenom_candidat'], self.admission.candidate.first_name)
        self.assertEqual(json_response['nom_candidat'], self.admission.candidate.last_name)
        self.assertEqual(json_response['statut'], self.admission.status)
        self.assertEqual(json_response['erreurs'], [])
        self.assertActionLinks(
            links=json_response['links'],
            allowed_actions=[
                'retrieve_person',
                'retrieve_coordinates',
                'retrieve_secondary_studies',
                'retrieve_curriculum',
                'retrieve_training_choice',
                'update_person',
                'update_coordinates',
                'update_secondary_studies',
                'update_curriculum',
                'update_training_choice',
                'destroy_proposition',
            ],
            forbidden_actions=[],
        )

    def test_get_proposition_other_candidate_is_forbidden(self):
        self.client.force_authenticate(user=self.other_candidate.user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_proposition_no_role_user_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)

        # Create a new admission
        admission = ContinuingEducationAdmissionFactory(candidate=self.candidate)
        self.assertEqual(admission.status, ChoixStatutPropositionFormationContinue.IN_PROGRESS.name)

        # Cancel it
        admission_to_cancel_url = resolve_url("admission_api_v1:continuing_propositions", uuid=str(admission.uuid))
        response = self.client.delete(admission_to_cancel_url, format="json")

        self.assertEqual(response.json()['uuid'], str(admission.uuid))

        admission = ContinuingEducationAdmission.objects.get(pk=admission.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionFormationContinue.CANCELLED.name)

    def test_delete_proposition_other_candidate_is_forbidden(self):
        self.client.force_authenticate(user=self.other_candidate.user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_proposition_no_role_user_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)
