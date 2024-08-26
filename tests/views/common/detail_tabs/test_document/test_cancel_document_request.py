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

from admission.contrib.models import AdmissionFormItemInstantiation
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    IdentifiantBaseEmplacementDocument,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.tests.views.common.detail_tabs.test_document import BaseDocumentViewTestCase


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class CancelDocumentRequestTestCase(BaseDocumentViewTestCase):

    # The manager cancels the request of a document
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_sic_manager_cancels_the_request_of_a_free_document(self, frozen_time):
        self.init_documents(for_sic=True)

        self.client.force_login(user=self.sic_manager_user)
        base_url = 'admission:general-education:document:candidate-request'

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier='UNKNOWN',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        # Some documents cannot be requested
        for index, identifier in enumerate(
            [
                # Because they are read only
                self.sic_free_non_requestable_internal_document,
                # Or created by a fac manager
                self.fac_free_non_requestable_internal_document,
                self.fac_free_requestable_candidate_document_with_default_file,
                self.fac_free_requestable_document,
                # Or created by the system
                f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
            ]
        ):
            response = self.client.get(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(
                response.status_code,
                403,
                'A SIC user cannot cancel the document n°%s' % index,
            )

        # Create a requested document
        document_identifier = self._create_a_free_document(
            self.sic_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
        )

        # The admission contains the information about this request
        self.general_admission.refresh_from_db()
        self.assertIsNotNone(self.general_admission.requested_documents.get(document_identifier))

        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])

        # A specific question has been created
        related_specific_question_exists = AdmissionFormItemInstantiation.objects.filter(
            admission=self.general_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        ).exists()
        self.assertTrue(related_specific_question_exists)

        self.client.force_login(user=self.second_sic_manager_user)

        # Get the editing form
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['request_reason'], 'My reason')
        form = response.context['form']
        self.assertEqual(form.fields['request_status'].required, False)

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=document_identifier,
            ),
            data={
                'request_status': '',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Remove the information about the request into the admission
        self.general_admission.refresh_from_db()
        self.assertIsNone(self.general_admission.requested_documents.get(document_identifier))

        # Remove the related specific question
        related_specific_question_exists = AdmissionFormItemInstantiation.objects.filter(
            admission=self.general_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        ).exists()
        self.assertFalse(related_specific_question_exists)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_sic_manager_user.person)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_fac_manager_cancels_the_request_of_a_free_document(self, frozen_time):
        self.init_documents(for_fac=True)

        self.client.force_login(user=self.fac_manager_user)
        base_url = 'admission:general-education:document:candidate-request'

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier='UNKNOWN',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        # Some documents cannot be requested
        for index, identifier in enumerate(
            [
                # Because they are read only
                self.fac_free_non_requestable_internal_document,
                # Or created by a fac manager
                self.sic_free_non_requestable_internal_document,
                self.sic_free_requestable_candidate_document_with_default_file,
                self.sic_free_requestable_document,
                # Or created by the system
                f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
            ]
        ):
            response = self.client.get(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(
                response.status_code,
                403,
                'A FAC user cannot cancel the document n°%s' % index,
            )

        # Create a requested document
        document_identifier = self._create_a_free_document(
            self.fac_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
        )

        # The admission contains the information about this request
        self.general_admission.refresh_from_db()
        self.assertIsNotNone(self.general_admission.requested_documents.get(document_identifier))

        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])

        # A specific question has been created
        related_specific_question_exists = AdmissionFormItemInstantiation.objects.filter(
            admission=self.general_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        ).exists()
        self.assertTrue(related_specific_question_exists)

        self.client.force_login(user=self.second_fac_manager_user)

        # Get the editing form
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['request_reason'], 'My reason')
        form = response.context['form']
        self.assertEqual(form.fields['request_status'].required, False)

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=document_identifier,
            ),
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Remove the information about the request into the admission
        self.general_admission.refresh_from_db()
        self.assertIsNone(self.general_admission.requested_documents.get(document_identifier))

        # Remove the related specific question
        related_specific_question_exists = AdmissionFormItemInstantiation.objects.filter(
            admission=self.general_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        ).exists()
        self.assertFalse(related_specific_question_exists)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_fac_manager_user.person)

    # The manager cancel the requests of a non free document
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_manager_cancels_the_request_of_a_non_free_document(self, frozen_time):
        base_url = 'admission:general-education:document:candidate-request'

        # A FAC user cannot request a categorized document
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save(update_fields=['status'])
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 403)

        # A SIC user can request a categorized document
        self.general_admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.general_admission.save(update_fields=['status'])
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['request_reason'], '')
        form = response.context['form']
        self.assertEqual(form.fields['request_status'].required, False)

        # Request the document
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'reason': 'My reason',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        self.general_admission.refresh_from_db()
        self.assertIsNotNone(self.general_admission.requested_documents.get(self.non_free_document_identifier))

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # A SIC manager can cancel the request
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'request_status': '',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['request_reason'], '')
        self.assertTrue(form.is_valid())

        # Remove the information about the request into the admission
        self.general_admission.refresh_from_db()
        self.assertIsNone(self.general_admission.requested_documents.get(self.non_free_document_identifier))

        # Request the document
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
                'reason': 'My reason',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        self.general_admission.refresh_from_db()
        self.assertIsNotNone(self.general_admission.requested_documents.get(self.non_free_document_identifier))

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # We indicate that a field has been automatically required by the system
        self.general_admission.requested_documents[self.non_free_document_identifier]['automatically_required'] = True
        self.general_admission.save(update_fields=['requested_documents'])

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['request_reason'], 'My reason')
        form = response.context['form']
        self.assertEqual(form.fields['request_status'].required, False)

        # Don't request this document anymore
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())
        self.general_admission.refresh_from_db()
        self.assertIsNone(self.general_admission.requested_documents.get(self.non_free_document_identifier))

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_doctorate_sic_manager_cancels_the_request_of_a_free_document(self, frozen_time):
        self.init_documents(for_sic=True, admission=self.doctorate_admission)

        self.client.force_login(user=self.sic_manager_user)
        base_url = 'admission:doctorate:document:candidate-request'

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier='UNKNOWN',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        # Some documents cannot be requested
        for index, identifier in enumerate(
            [
                # Because they are read only
                self.sic_free_non_requestable_internal_document,
                self.fac_free_non_requestable_internal_document,
                # Or created by the system
                f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
            ]
        ):
            response = self.client.get(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(
                response.status_code,
                403,
                'A SIC user cannot cancel the document n°%s' % index,
            )

        # SIC user can cancel FAC documents
        for identifier in [
            self.fac_free_requestable_candidate_document_with_default_file,
            self.fac_free_requestable_document,
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                data={
                    'request_status': '',
                },
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 200)

        # Create a requested document
        document_identifier = self._create_a_free_document(
            self.sic_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
            admission=self.doctorate_admission,
        )

        # The admission contains the information about this request
        self.doctorate_admission.refresh_from_db()
        self.assertIsNotNone(self.doctorate_admission.requested_documents.get(document_identifier))

        frozen_time.move_to('2022-01-03')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['last_update_author'])

        # A specific question has been created
        related_specific_question_exists = AdmissionFormItemInstantiation.objects.filter(
            admission=self.doctorate_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        ).exists()
        self.assertTrue(related_specific_question_exists)

        self.client.force_login(user=self.second_sic_manager_user)

        # Get the editing form
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['request_reason'], 'My reason')
        form = response.context['form']
        self.assertEqual(form.fields['request_status'].required, False)

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=document_identifier,
            ),
            data={
                'request_status': '',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Remove the information about the request into the admission
        self.doctorate_admission.refresh_from_db()
        self.assertIsNone(self.doctorate_admission.requested_documents.get(document_identifier))

        # Remove the related specific question
        related_specific_question_exists = AdmissionFormItemInstantiation.objects.filter(
            admission=self.doctorate_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        ).exists()
        self.assertFalse(related_specific_question_exists)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.second_sic_manager_user.person)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_doctorate_fac_manager_cancels_the_request_of_a_free_document(self, frozen_time):
        self.init_documents(for_fac=True, admission=self.doctorate_admission)

        self.client.force_login(user=self.doctorate_fac_manager_user)
        base_url = 'admission:doctorate:document:candidate-request'

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier='UNKNOWN',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        # Some documents cannot be requested
        for index, identifier in enumerate(
            [
                # Because they are read only
                self.fac_free_non_requestable_internal_document,
                self.sic_free_non_requestable_internal_document,
                # Or created by the system
                f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
            ]
        ):
            response = self.client.get(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(
                response.status_code,
                403,
                'A FAC user cannot cancel the document n°%s' % index,
            )

        # FAC manager can cancel SIC documents
        for index, identifier in enumerate(
            [
                self.sic_free_requestable_candidate_document_with_default_file,
                self.sic_free_requestable_document,
            ]
        ):
            response = self.client.get(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 200)

        # Create a requested document
        document_identifier = self._create_a_free_document(
            self.doctorate_fac_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
            admission=self.doctorate_admission,
        )

        # The admission contains the information about this request
        self.doctorate_admission.refresh_from_db()
        self.assertIsNotNone(self.doctorate_admission.requested_documents.get(document_identifier))

        frozen_time.move_to('2022-01-03')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['last_update_author'])

        # A specific question has been created
        related_specific_question_exists = AdmissionFormItemInstantiation.objects.filter(
            admission=self.doctorate_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        ).exists()
        self.assertTrue(related_specific_question_exists)

        self.client.force_login(user=self.second_doctorate_fac_manager_user)

        # Get the editing form
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['request_reason'], 'My reason')
        form = response.context['form']
        self.assertEqual(form.fields['request_status'].required, False)

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=document_identifier,
            ),
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Remove the information about the request into the admission
        self.doctorate_admission.refresh_from_db()
        self.assertIsNone(self.doctorate_admission.requested_documents.get(document_identifier))

        # Remove the related specific question
        related_specific_question_exists = AdmissionFormItemInstantiation.objects.filter(
            admission=self.doctorate_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        ).exists()
        self.assertFalse(related_specific_question_exists)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.second_doctorate_fac_manager_user.person)

    # The manager cancel the requests of a non free document
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_doctorate_manager_cancels_the_request_of_a_non_free_document(self, frozen_time):
        base_url = 'admission:doctorate:document:candidate-request'

        # A FAC user can request a categorized document
        self.doctorate_admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.doctorate_admission.save(update_fields=['status'])
        self.client.force_login(user=self.doctorate_fac_manager_user)

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        # A SIC user can request a categorized document
        self.doctorate_admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.doctorate_admission.save(update_fields=['status'])
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['request_reason'], '')
        form = response.context['form']
        self.assertEqual(form.fields['request_status'].required, False)

        # Request the document
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'reason': 'My reason',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        self.doctorate_admission.refresh_from_db()
        self.assertIsNotNone(self.doctorate_admission.requested_documents.get(self.non_free_document_identifier))

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)

        # A SIC manager can cancel the request
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'request_status': '',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['request_reason'], '')
        self.assertTrue(form.is_valid())

        # Remove the information about the request into the admission
        self.doctorate_admission.refresh_from_db()
        self.assertIsNone(self.doctorate_admission.requested_documents.get(self.non_free_document_identifier))

        # Request the document
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
                'reason': 'My reason',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        self.doctorate_admission.refresh_from_db()
        self.assertIsNotNone(self.doctorate_admission.requested_documents.get(self.non_free_document_identifier))

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)

        # We indicate that a field has been automatically required by the system
        self.doctorate_admission.requested_documents[self.non_free_document_identifier]['automatically_required'] = True
        self.doctorate_admission.save(update_fields=['requested_documents'])

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['request_reason'], 'My reason')
        form = response.context['form']
        self.assertEqual(form.fields['request_status'].required, False)

        # Don't request this document anymore
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())
        self.doctorate_admission.refresh_from_db()
        self.assertIsNone(self.doctorate_admission.requested_documents.get(self.non_free_document_identifier))
