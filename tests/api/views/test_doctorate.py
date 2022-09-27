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
from typing import Optional

from django.contrib.auth.models import User
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.admission.projet_doctoral.preparation.domain.model._enums import (
    ChoixStatutProposition,
)

from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.supervision import PromoterFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class DoctorateAPIViewTestCase(APITestCase):
    admission: Optional[DoctorateAdmissionFactory] = None
    doctorate: Optional[DoctorateAdmissionFactory] = None
    other_doctorate: Optional[DoctorateAdmissionFactory] = None
    commission: Optional[EntityVersionFactory] = None
    sector: Optional[EntityVersionFactory] = None
    student: Optional[CandidateFactory] = None
    other_student: Optional[CandidateFactory] = None
    no_role_user: Optional[User] = None
    doctorate_url: Optional[str] = None
    admission_url: Optional[str] = None
    other_doctorate_url: Optional[str] = None

    @classmethod
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()

        # Create doctorate management entity
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.doctorate = DoctorateAdmissionFactory(
            status=ChoixStatutProposition.ENROLLED.name,
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
            doctorate__management_entity=cls.commission,
            supervision_group=promoter.process,
        )
        cls.admission = DoctorateAdmissionFactory(
            doctorate__management_entity=cls.commission,
            candidate=cls.doctorate.candidate,
        )
        cls.other_doctorate = DoctorateAdmissionFactory(
            status=ChoixStatutProposition.ENROLLED.name,
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
            doctorate__management_entity=cls.commission,
        )
        # Users
        cls.student = cls.doctorate.candidate
        cls.other_student = cls.other_doctorate.candidate
        cls.no_role_user = PersonFactory().user

        cls.doctorate_url = resolve_url('admission_api_v1:doctorate', uuid=cls.doctorate.uuid)
        cls.other_doctorate_url = resolve_url('admission_api_v1:doctorate', uuid=cls.other_doctorate.uuid)
        cls.admission_url = resolve_url('admission_api_v1:doctorate', uuid=cls.admission.uuid)

    def test_get_doctorate_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.doctorate_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        # Check doctorate links
        self.assertTrue('links' in json_response)
        allowed_actions = [
            'retrieve_cotutelle',
            'retrieve_supervision',
            'retrieve_proposition',
            'retrieve_confirmation',
            'update_confirmation',
            'retrieve_training',
            'add_training',
            'update_confirmation_extension',
        ]
        self.assertCountEqual(
            json_response['links'],
            allowed_actions,
        )
        for action in allowed_actions:
            # Check the url
            self.assertTrue('url' in json_response['links'][action], '{} is not allowed'.format(action))
            # Check the method type
            self.assertTrue('method' in json_response['links'][action])

        # Check doctorate properties
        self.assertEqual(json_response['uuid'], str(self.doctorate.uuid))
        self.assertEqual(json_response['reference'], self.doctorate.reference)
        self.assertEqual(json_response['statut'], self.doctorate.post_enrolment_status)
        self.assertEqual(json_response['sigle_formation'], self.doctorate.doctorate.acronym)
        self.assertEqual(json_response['annee_formation'], self.doctorate.doctorate.academic_year.year)
        self.assertEqual(json_response['intitule_formation'], self.doctorate.doctorate.title)
        self.assertEqual(json_response['matricule_doctorant'], self.doctorate.candidate.global_id)
        self.assertEqual(json_response['prenom_doctorant'], self.doctorate.candidate.first_name)
        self.assertEqual(json_response['nom_doctorant'], self.doctorate.candidate.last_name)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'put',
            'patch',
            'post',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.doctorate_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_doctorate_invalid_status(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.admission_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], DoctoratNonTrouveException.status_code)

    def test_get_doctorate_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.admission_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
