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
import uuid

import freezegun
from django.shortcuts import resolve_url
from django.test import override_settings

from admission.ddd.admission.enums.emplacement_document import (
    IdentifiantBaseEmplacementDocument,
)
from admission.tests.views.common.detail_tabs.test_document import BaseDocumentViewTestCase


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DeleteDocumentTestCase(BaseDocumentViewTestCase):
    # The manager deletes a document
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_sic_manager_deletes_a_document(self, frozen_time):
        self.init_documents(for_sic=True)

        base_url = 'admission:general-education:document:delete'

        self.client.force_login(user=self.sic_manager_user)

        # Unknown document
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A SIC manager cannot delete FAC documents
            self.fac_free_non_requestable_internal_document,
            self.fac_free_requestable_candidate_document_with_default_file,
            self.fac_free_requestable_document,
            # A manager cannot delete a system document
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.delete(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A SIC manager can delete SIC documents
        # Internal document
        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        self.general_admission.refresh_from_db()
        document_uuid = uuid.UUID(self.sic_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(document_uuid, self.general_admission.uclouvain_sic_documents)
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.sic_free_non_requestable_internal_document,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 204)
        self.general_admission.refresh_from_db()
        self.assertNotIn(document_uuid, self.general_admission.uclouvain_sic_documents)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Requestable document
        specific_question_uuid = str(uuid.UUID(self.sic_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-04')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        self.assertIsNotNone(self.general_admission.requested_documents.get(self.sic_free_requestable_document))

        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.sic_free_requestable_document,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 204)
        self.general_admission.refresh_from_db()
        self.assertIsNotNone(self.general_admission.requested_documents.get(self.sic_free_requestable_document))
        self.assertIsNone(self.general_admission.specific_question_answers.get(specific_question_uuid))

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Non free document
        self.general_admission.curriculum = [uuid.uuid4()]
        frozen_time.move_to('2022-01-05')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['curriculum', 'last_update_author'])

        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 204)

        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.curriculum, [])

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_fac_manager_deletes_a_document(self, frozen_time):
        self.init_documents(for_fac=True)

        base_url = 'admission:general-education:document:delete'

        self.client.force_login(user=self.fac_manager_user)

        # Unknown document
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A FAC manager cannot delete SIC documents
            self.sic_free_non_requestable_internal_document,
            self.sic_free_requestable_candidate_document_with_default_file,
            self.sic_free_requestable_document,
            # A manager cannot delete a system document
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.delete(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A FAC manager can delete FAC documents
        # Internal document
        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        self.general_admission.refresh_from_db()
        document_uuid = uuid.UUID(self.fac_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(document_uuid, self.general_admission.uclouvain_fac_documents)
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.fac_free_non_requestable_internal_document,
            ),
        )

        self.assertEqual(response.status_code, 204)
        self.general_admission.refresh_from_db()
        self.assertNotIn(document_uuid, self.general_admission.uclouvain_fac_documents)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)

        # Requestable document
        specific_question_uuid = str(uuid.UUID(self.fac_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-04')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        self.assertIsNotNone(self.general_admission.requested_documents.get(self.fac_free_requestable_document))

        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.fac_free_requestable_document,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 204)
        self.general_admission.refresh_from_db()
        self.assertIsNotNone(self.general_admission.requested_documents.get(self.fac_free_requestable_document))
        self.assertIsNone(self.general_admission.specific_question_answers.get(specific_question_uuid))

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)

        # Non free document
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_continuing_sic_manager_deletes_a_document(self, frozen_time):
        self.init_documents(for_sic=True, admission=self.continuing_admission)

        base_url = 'admission:continuing-education:document:delete'

        self.client.force_login(user=self.sic_manager_user)

        # Unknown document
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.continuing_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A manager cannot delete a system document
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.delete(
                resolve_url(
                    base_url,
                    uuid=self.continuing_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A SIC manager can delete FAC and SIC documents
        for identifier in [
            self.fac_free_requestable_candidate_document_with_default_file,
            self.fac_free_requestable_document,
            self.fac_free_non_requestable_internal_document,
            self.sic_free_requestable_document,
            self.non_free_document_identifier,
        ]:
            response = self.client.delete(
                resolve_url(
                    base_url,
                    uuid=self.continuing_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 204)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_continuing_fac_manager_deletes_a_document(self, frozen_time):
        self.init_documents(for_fac=True, admission=self.continuing_admission)

        base_url = 'admission:continuing-education:document:delete'

        self.client.force_login(user=self.continuing_fac_manager_user)

        # Unknown document
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.continuing_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A manager cannot delete a system document
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.delete(
                resolve_url(
                    base_url,
                    uuid=self.continuing_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A FAC manager can delete SIC and FAC documents
        for identifier in [
            self.sic_free_requestable_document,
            self.sic_free_requestable_candidate_document_with_default_file,
            self.non_free_document_identifier,
            self.fac_free_non_requestable_internal_document,
            self.fac_free_requestable_document,
        ]:
            response = self.client.delete(
                resolve_url(
                    base_url,
                    uuid=self.continuing_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 204)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_doctorate_sic_manager_deletes_a_document(self, frozen_time):
        self.init_documents(for_sic=True, admission=self.doctorate_admission)

        base_url = 'admission:doctorate:document:delete'

        self.client.force_login(user=self.sic_manager_user)

        # Unknown document
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A manager cannot delete a system document
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.delete(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A SIC manager can delete FAC documents
        for identifier in [
            self.fac_free_non_requestable_internal_document,
            self.fac_free_requestable_candidate_document_with_default_file,
            self.fac_free_requestable_document,
        ]:
            response = self.client.delete(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 204)

        # A SIC manager can delete SIC documents
        # Internal document
        frozen_time.move_to('2022-01-03')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['last_update_author'])
        self.doctorate_admission.refresh_from_db()
        document_uuid = uuid.UUID(self.sic_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(document_uuid, self.doctorate_admission.uclouvain_sic_documents)
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.sic_free_non_requestable_internal_document,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 204)
        self.doctorate_admission.refresh_from_db()
        self.assertNotIn(document_uuid, self.doctorate_admission.uclouvain_sic_documents)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)

        # Requestable document
        specific_question_uuid = str(uuid.UUID(self.sic_free_requestable_document.split('.')[-1]))
        self.doctorate_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-04')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        self.assertIsNotNone(self.doctorate_admission.requested_documents.get(self.sic_free_requestable_document))

        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.sic_free_requestable_document,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 204)
        self.doctorate_admission.refresh_from_db()
        self.assertIsNotNone(self.doctorate_admission.requested_documents.get(self.sic_free_requestable_document))
        self.assertIsNone(self.doctorate_admission.specific_question_answers.get(specific_question_uuid))

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)

        # Non free document
        self.doctorate_admission.curriculum = [uuid.uuid4()]
        frozen_time.move_to('2022-01-05')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['curriculum', 'last_update_author'])

        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 204)

        self.doctorate_admission.refresh_from_db()
        self.assertEqual(self.doctorate_admission.curriculum, [])

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_doctorate_fac_manager_deletes_a_document(self, frozen_time):
        self.init_documents(for_fac=True, admission=self.doctorate_admission)

        base_url = 'admission:doctorate:document:delete'

        self.client.force_login(user=self.doctorate_fac_manager_user)

        # Unknown document
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A manager cannot delete a system document
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.delete(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        for identifier in [
            # A FAC manager can delete SIC documents
            self.sic_free_non_requestable_internal_document,
            self.sic_free_requestable_candidate_document_with_default_file,
            self.sic_free_requestable_document,
        ]:
            response = self.client.delete(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 204)

        # A FAC manager can delete FAC documents
        # Internal document
        frozen_time.move_to('2022-01-03')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['last_update_author'])
        self.doctorate_admission.refresh_from_db()
        document_uuid = uuid.UUID(self.fac_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(document_uuid, self.doctorate_admission.uclouvain_fac_documents)
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.fac_free_non_requestable_internal_document,
            ),
        )

        self.assertEqual(response.status_code, 204)
        self.doctorate_admission.refresh_from_db()
        self.assertNotIn(document_uuid, self.doctorate_admission.uclouvain_fac_documents)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.doctorate_fac_manager_user.person)

        # Requestable document
        specific_question_uuid = str(uuid.UUID(self.fac_free_requestable_document.split('.')[-1]))
        self.doctorate_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-04')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        self.assertIsNotNone(self.doctorate_admission.requested_documents.get(self.fac_free_requestable_document))

        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.fac_free_requestable_document,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 204)
        self.doctorate_admission.refresh_from_db()
        self.assertIsNotNone(self.doctorate_admission.requested_documents.get(self.fac_free_requestable_document))
        self.assertIsNone(self.doctorate_admission.specific_question_answers.get(specific_question_uuid))

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.doctorate_fac_manager_user.person)

        # Non free document
        response = self.client.delete(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 204)
