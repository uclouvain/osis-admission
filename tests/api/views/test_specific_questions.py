# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.tests import QueriesAssertionsMixin
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.form_item import (
    MessageAdmissionFormItemFactory,
    TextAdmissionFormItemFactory,
    DocumentAdmissionFormItemFactory,
)
from admission.tests.factories.roles import CandidateFactory, CddManagerFactory
from admission.tests.factories.supervision import PromoterFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class SpecificQuestionApiTestCase(QueriesAssertionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        commission = EntityVersionFactory(
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        promoter = PromoterFactory(actor_ptr__person__first_name="Joe")
        admission = DoctorateAdmissionFactory(
            doctorate__management_entity=commission,
            supervision_group=promoter.actor_ptr.process,
        )
        MessageAdmissionFormItemFactory(
            uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
            education=admission.doctorate,
            weight=3,
            internal_label='message_item',
            text={'en': 'My very short message.', 'fr-be': 'Mon très court message.'},
            config={},
        )
        TextAdmissionFormItemFactory(
            uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da552'),
            education=admission.doctorate,
            weight=1,
            required=True,
            internal_label='text_item',
            title={'en': 'Text field', 'fr-be': 'Champ texte'},
            text={'en': 'Detailed data.', 'fr-be': 'Données détaillées.'},
            help_text={'en': 'Write here', 'fr-be': 'Ecrivez ici'},
            config={},
        )
        DocumentAdmissionFormItemFactory(
            uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da553'),
            education=admission.doctorate,
            weight=2,
            internal_label='document_item',
            deleted=True,
            title={'en': 'Document field', 'fr-be': 'Champ document'},
            text={'en': 'Detailed data.', 'fr-be': 'Données détaillées.'},
            config={},
        )
        cls.admission = admission

        # Users
        cls.candidate = admission.candidate
        cls.other_candidate_user = CandidateFactory(person__first_name="Jim").person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user
        cls.cdd_manager_user = CddManagerFactory(entity=commission).person.user
        cls.other_cdd_manager_user = CddManagerFactory().person.user

        # Target url
        cls.url = resolve_url("admission_api_v1:specific-questions", uuid=admission.uuid)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'patch', 'post', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_with_other_candidate_user(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_with_valid_candidate_user(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    'uuid': 'fe254203-17c7-47d6-95e4-3c5c532da552',
                    'type': 'TEXTE',
                    'required': True,
                    'title': {'en': 'Text field', 'fr-be': 'Champ texte'},
                    'text': {'en': 'Detailed data.', 'fr-be': 'Données détaillées.'},
                    'help_text': {'en': 'Write here', 'fr-be': 'Ecrivez ici'},
                    'config': {},
                },
                {
                    'uuid': 'fe254203-17c7-47d6-95e4-3c5c532da551',
                    'type': 'MESSAGE',
                    'required': False,
                    'title': {},
                    'text': {'en': 'My very short message.', 'fr-be': 'Mon très court message.'},
                    'help_text': {},
                    'config': {},
                },
            ],
        )
