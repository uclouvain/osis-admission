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

import freezegun
from django.shortcuts import resolve_url
from django.test import override_settings

from admission.tests.views.common.detail_tabs.test_document import BaseDocumentViewTestCase


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class RetypeDocumentTestCase(BaseDocumentViewTestCase):
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_sic_manager_retypes_a_document(self, frozen_time):
        self.init_documents(for_sic=True)

        base_url = 'admission:general-education:document:retype'

        self.client.force_login(user=self.sic_manager_user)

        with self.subTest('Unknown document'):
            response = self.client.get(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier='unknown',
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 404)

        with self.subTest('Post a valid form'):
            other_doc = self.sic_free_requestable_document.split('.')[-1]
            self.general_admission.specific_question_answers[other_doc] = ['uuid-doc']
            self.general_admission.save()

            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=self.non_free_document_identifier,
                ),
                data={
                    'identifier': self.sic_free_requestable_document,
                },
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 200)

            self.general_admission.refresh_from_db()

            # Check last modification data
            self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
            self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        with ((self.subTest('Post a valid form to empty doc'))):
            other_doc = self.sic_free_requestable_document.split('.')[-1]
            self.general_admission.specific_question_answers[other_doc] = []
            self.general_admission.save()

            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=self.non_free_document_identifier,
                ),
                data={
                    'identifier': self.sic_free_requestable_document,
                },
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 200)

            self.general_admission.refresh_from_db()

            # Check last modification data
            self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
            self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_doctorate_sic_manager_retypes_a_document(self, frozen_time):
        self.init_documents(for_sic=True, admission=self.doctorate_admission)

        base_url = 'admission:doctorate:document:retype'

        self.client.force_login(user=self.sic_manager_user)

        with self.subTest('Unknown document'):
            response = self.client.get(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier='unknown',
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 404)

        with self.subTest('Post a valid form'):
            other_doc = self.sic_free_requestable_document.split('.')[-1]
            self.doctorate_admission.specific_question_answers[other_doc] = ['uuid-doc']
            self.doctorate_admission.save()

            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=self.non_free_document_identifier,
                ),
                data={
                    'identifier': self.sic_free_requestable_document,
                },
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 200)

            self.doctorate_admission.refresh_from_db()

            # Check last modification data
            self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
            self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)

        with self.subTest('Post a valid form to empty doc'):
            other_doc = self.sic_free_requestable_document.split('.')[-1]
            self.doctorate_admission.specific_question_answers[other_doc] = []
            self.doctorate_admission.save()

            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=self.non_free_document_identifier,
                ),
                data={
                    'identifier': self.sic_free_requestable_document,
                },
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 200)

            self.doctorate_admission.refresh_from_db()

            # Check last modification data
            self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
            self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)
