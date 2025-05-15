# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import json
import uuid

import mock
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from admission.tests.factories.general_education import GeneralEducationAdmissionFactory


class DocumentTypesForSwappingAutocompleteTestCase(TestCase):
    def setUp(self):
        self.documents = [
            mock.Mock(
                identifiant='id-11',
                requis_automatiquement=True,
                nom_onglet='tab-1',
                document_uuids=self.document_uuids,
                libelle='doc-11',
            ),
            mock.Mock(
                identifiant='id-12',
                requis_automatiquement=False,
                nom_onglet='tab-1',
                document_uuids=self.document_uuids,
                libelle='doc-12',
            ),
            mock.Mock(
                identifiant='id-21',
                requis_automatiquement=False,
                nom_onglet='tab-2',
                document_uuids=[],
                libelle='doc-21',
            ),
        ]
        self.patch_message_bus = mock.patch(
            'infrastructure.messages_bus.message_bus_instance.invoke',
            side_effect=lambda *args, **kwargs: self.documents,
        )
        self.message_bus_mocked = self.patch_message_bus.start()
        self.addCleanup(self.patch_message_bus.stop)

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        cls.admission = GeneralEducationAdmissionFactory()
        cls.admission_uuid = str(cls.admission.uuid)
        cls.document_uuids = [str(uuid.uuid4())]

        cls.data = {
            'forward': json.dumps({'display_study_type': True}),
        }

        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )

        cls.url = reverse('admission:autocomplete:document-types-swap')

    def test_retrieve_documents_by_category(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            data={
                'forward': json.dumps(
                    {
                        'document_identifier': 'id-11',
                        'admission_uuid': self.admission_uuid,
                    },
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [
                    {
                        'text': 'tab-1',
                        'children': [
                            {
                                'id': 'id-11',
                                'text': '<i class="fa-solid fa-paperclip"></i> doc-11',
                                'disabled': True,  # The document cannot be swapped with itself
                            },
                            {
                                'id': 'id-12',
                                'text': '<i class="fa-solid fa-paperclip"></i> doc-12',
                                'disabled': False,
                            },
                        ],
                    },
                    {
                        'text': 'tab-2',
                        'children': [
                            {
                                'id': 'id-21',
                                'text': '<i class="fa-solid fa-link-slash"></i> doc-21',
                                'disabled': False,
                            },
                        ],
                    },
                ],
            },
        )

    def test_filter_documents_by_name(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            data={
                'forward': json.dumps(
                    {
                        'document_identifier': 'id-11',
                        'admission_uuid': self.admission_uuid,
                    },
                ),
                'q': 'doc-12',
            },
        )

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [
                    {
                        'text': 'tab-1',
                        'children': [
                            {
                                'id': 'id-12',
                                'text': '<i class="fa-solid fa-paperclip"></i> doc-12',
                                'disabled': False,
                            },
                        ],
                    },
                ],
            },
        )
