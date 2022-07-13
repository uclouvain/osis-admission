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
from rest_framework.test import APITestCase

from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import CategorieActivite
from admission.tests import QueriesAssertionsMixin
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.activity import ActivityFactory, ConferenceFactory, ServiceFactory
from admission.tests.factories.roles import CandidateFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class TrainingApiTestCase(QueriesAssertionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.commission = EntityVersionFactory(
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.admission = DoctorateAdmissionFactory(
            doctorate__management_entity=cls.commission,
            admitted=True,
        )
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory(person__first_name="Jim").person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user
        cls.url = resolve_url("admission_api_v1:doctoral-training", uuid=cls.admission.uuid)
        cls.activity = ConferenceFactory(doctorate=cls.admission)
        cls.activity_url = resolve_url(
            "admission_api_v1:doctoral-training",
            uuid=cls.admission.uuid,
            activity_id=cls.activity.uuid,
        )

    def test_user_not_logged_assert_not_authorized(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'patch', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_training_get_with_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.url)
        activities = response.json()
        self.assertEqual(len(activities), 1)

    def test_training_get_with_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_training_get_with_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_training_create_with_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        data = {
            'object_type': 'Conference',
            'ects': "0.0",
            'category': 'CONFERENCE',
            'parent': None,
            'type': 'A great conference',
            'title': '',
            'participating_proof': [],
            'comment': '',
            'start_date': None,
            'end_date': None,
            'participating_days': 0.0,
            'is_online': False,
            'country': None,
            'city': '',
            'organizing_institution': '',
            'website': '',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())

        # Child activity
        data = {
            'object_type': 'ConferenceCommunication',
            'ects': 0,
            'category': 'COMMUNICATION',
            'parent': self.activity.uuid,
            'type': 'A great communication',
            'title': '',
            'committee': '',
            'dial_reference': '',
            'comment': '',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())

    def test_training_get_detail_with_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.activity_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        subactivity = ActivityFactory(
            doctorate=self.admission,
            category=CategorieActivite.COMMUNICATION.name,
            parent=self.activity,
        )
        activity_url = resolve_url(
            "admission_api_v1:doctoral-training",
            uuid=self.admission.uuid,
            activity_id=subactivity.uuid,
        )
        response = self.client.get(activity_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_training_update_with_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        data = {
            'object_type': 'Conference',
            'ects': "0.0",
            'category': 'CONFERENCE',
            'parent': None,
            'type': 'A great conference',
            'title': '',
            'participating_proof': [],
            'comment': '',
            'start_date': None,
            'end_date': None,
            'participating_days': 0.0,
            'is_online': False,
            'country': None,
            'city': '',
            'organizing_institution': '',
            'website': '',
        }
        response = self.client.put(self.activity_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_training_config(self):
        self.client.force_authenticate(user=self.candidate.user)
        config_url = resolve_url("admission_api_v1:doctoral-training-config", uuid=self.admission.uuid)
        response = self.client.get(config_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_training_submit(self):
        service = ServiceFactory(doctorate=self.admission)
        self.client.force_authenticate(user=self.candidate.user)
        submit_url = resolve_url("admission_api_v1:doctoral-training-submit", uuid=self.admission.uuid)
        response = self.client.post(submit_url, {'activity_uuids': [service.uuid]})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_training_submit_with_error(self):
        self.client.force_authenticate(user=self.candidate.user)
        service = ServiceFactory(doctorate=self.admission, title="")
        submit_url = resolve_url("admission_api_v1:doctoral-training-submit", uuid=self.admission.uuid)
        response = self.client.post(submit_url, {'activity_uuids': [service.uuid]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
