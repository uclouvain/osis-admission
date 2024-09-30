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
from django.utils.translation import gettext

from admission.contrib.models import AdmissionFormItemInstantiation
from admission.ddd.admission.enums import TypeItemFormulaire, CritereItemFormulaireFormation, Onglets
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    IdentifiantBaseEmplacementDocument,
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    OngletsChecklist as OngletsChecklistGenerale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist as OngletsChecklistDoctorale,
)
from admission.tests.factories.categorized_free_document import CategorizedFreeDocumentFactory
from admission.tests.views.common.detail_tabs.test_document import BaseDocumentViewTestCase
from base.forms.utils import FIELD_REQUIRED_MESSAGE


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DocumentRequestWithDefaultFileTestCase(BaseDocumentViewTestCase):
    # The manager requests a free document that the candidate must upload
    @freezegun.freeze_time('2022-01-01')
    def test_general_sic_manager_requests_a_free_document_with_a_default_file(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-request-with-default-file',
            uuid=self.general_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form

        # With no data
        response = self.client.post(url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'free-document-request-with-default-file-form-file_name': 'My file name',
                'free-document-request-with-default-file-form-file_0': ['file_0-token'],
                'free-document-request-with-default-file-form-document_type': '',
                'free-document-request-with-default-file-form-checklist_tab': OngletsChecklistGenerale.assimilation.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        # Create a specific question linked to the admission
        form_item_instantiation: AdmissionFormItemInstantiation = (
            AdmissionFormItemInstantiation.objects.select_related('form_item', 'admission')
            .filter(
                admission=self.general_admission,
            )
            .first()
        )
        self.assertIsNotNone(form_item_instantiation)

        self.assertEqual(form_item_instantiation.form_item.type, TypeItemFormulaire.DOCUMENT.name)
        self.assertEqual(
            form_item_instantiation.form_item.title,
            {
                'en': 'My file name',
                'fr-be': 'My file name',
            },
        )

        self.assertEqual(form_item_instantiation.admission_id, self.general_admission.pk)
        self.assertEqual(form_item_instantiation.academic_year_id, self.general_admission.determined_academic_year_id)
        self.assertEqual(form_item_instantiation.required, False)
        self.assertEqual(
            form_item_instantiation.display_according_education,
            CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name,
        )
        self.assertEqual(form_item_instantiation.tab, Onglets.DOCUMENTS.name)

        # Save information about the request into the admission
        desired_result = {
            f'{IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name}.{form_item_instantiation.form_item.uuid}': {
                'last_actor': self.sic_manager_user.person.global_id,
                'reason': '',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                'last_action_at': '2022-01-01T00:00:00',
                'deadline_at': '',
                'requested_at': '',
                'status': StatutEmplacementDocument.VALIDE.name,
                'automatically_required': False,
                'request_status': '',
                'related_checklist_tab': OngletsChecklistGenerale.assimilation.name,
            }
        }
        self.assertEqual(form_item_instantiation.admission.requested_documents, desired_result)

        # Check that a default answer to the specific question has been specified
        self.assertEqual(
            len(
                form_item_instantiation.admission.specific_question_answers.get(
                    str(form_item_instantiation.form_item.uuid), []
                ),
            ),
            1,
        )

        # Check last modification data
        self.assertEqual(form_item_instantiation.admission.modified_at, datetime.datetime.now())
        self.assertEqual(form_item_instantiation.admission.last_update_author, self.sic_manager_user.person)

    @freezegun.freeze_time('2022-01-01')
    def test_general_sic_manager_requests_a_free_document_with_a_default_file_and_a_predefined_configuration(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-request-with-default-file',
            uuid=self.general_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form

        # With no data
        response = self.client.post(url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))

        # With invalid chosen predefined file
        categorized_document = CategorizedFreeDocumentFactory(
            checklist_tab=OngletsChecklistGenerale.parcours_anterieur.name,
            with_academic_year=False,
        )
        response = self.client.post(
            url,
            data={
                'free-document-request-with-default-file-form-file_name': 'My file name',
                'free-document-request-with-default-file-form-request_status': (
                    StatutReclamationEmplacementDocument.IMMEDIATEMENT.name
                ),
                'free-document-request-with-default-file-form-checklist_tab': OngletsChecklistGenerale.assimilation.name,
                'free-document-request-with-default-file-form-document_type': categorized_document.pk,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        # Because the selected checklist tab and the selected document checklist tab must be the same
        self.assertIn(
            gettext('The document must be related to the specified checklist tab'),
            response.context['form'].errors.get('checklist_tab', []),
        )
        self.assertNotIn('academic_year', response.context['form'].errors)

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'free-document-request-with-default-file-form-file_name': 'My file name',
                'free-document-request-with-default-file-form-file_0': ['file_0-token'],
                'free-document-request-with-default-file-form-document_type': categorized_document.pk,
                'free-document-request-with-default-file-form-checklist_tab': OngletsChecklistGenerale.parcours_anterieur.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        # Create a specific question linked to the admission
        form_item_instantiation: AdmissionFormItemInstantiation = (
            AdmissionFormItemInstantiation.objects.select_related('form_item', 'admission')
            .filter(
                admission=self.general_admission,
            )
            .first()
        )
        self.assertIsNotNone(form_item_instantiation)

        self.assertEqual(form_item_instantiation.form_item.type, TypeItemFormulaire.DOCUMENT.name)
        self.assertEqual(
            form_item_instantiation.form_item.title,
            {
                'en': categorized_document.long_label_en,
                'fr-be': categorized_document.long_label_fr,
            },
        )

        self.assertEqual(form_item_instantiation.admission_id, self.general_admission.pk)
        self.assertEqual(form_item_instantiation.academic_year_id, self.general_admission.determined_academic_year_id)
        self.assertEqual(form_item_instantiation.required, False)
        self.assertEqual(
            form_item_instantiation.display_according_education,
            CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name,
        )
        self.assertEqual(form_item_instantiation.tab, Onglets.DOCUMENTS.name)

        # Save information about the request into the admission
        desired_result = {
            f'{IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name}.{form_item_instantiation.form_item.uuid}': {
                'last_actor': self.sic_manager_user.person.global_id,
                'reason': '',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                'last_action_at': '2022-01-01T00:00:00',
                'deadline_at': '',
                'requested_at': '',
                'status': StatutEmplacementDocument.VALIDE.name,
                'automatically_required': False,
                'request_status': '',
                'related_checklist_tab': OngletsChecklistGenerale.parcours_anterieur.name,
            }
        }
        self.assertEqual(form_item_instantiation.admission.requested_documents, desired_result)

        # Check that a default answer to the specific question has been specified
        self.assertEqual(
            len(
                form_item_instantiation.admission.specific_question_answers.get(
                    str(form_item_instantiation.form_item.uuid), []
                ),
            ),
            1,
        )

        # Check last modification data
        self.assertEqual(form_item_instantiation.admission.modified_at, datetime.datetime.now())
        self.assertEqual(form_item_instantiation.admission.last_update_author, self.sic_manager_user.person)

    @freezegun.freeze_time('2022-01-01')
    def test_general_fac_manager_requests_a_free_document_with_a_default_file(self):
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save(update_fields=['status'])

        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-request-with-default-file',
            uuid=self.general_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form
        response = self.client.post(url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'free-document-request-with-default-file-form-file_name': 'My file name',
                'free-document-request-with-default-file-form-file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        # Create a specific question linked to the admission
        form_item_instantiation: AdmissionFormItemInstantiation = (
            AdmissionFormItemInstantiation.objects.select_related('form_item', 'admission')
            .filter(
                admission=self.general_admission,
            )
            .first()
        )
        self.assertIsNotNone(form_item_instantiation)

        self.assertEqual(form_item_instantiation.form_item.type, TypeItemFormulaire.DOCUMENT.name)
        self.assertEqual(
            form_item_instantiation.form_item.title,
            {
                'en': 'My file name',
                'fr-be': 'My file name',
            },
        )

        self.assertEqual(form_item_instantiation.admission_id, self.general_admission.pk)
        self.assertEqual(form_item_instantiation.academic_year_id, self.general_admission.determined_academic_year_id)
        self.assertEqual(form_item_instantiation.required, False)
        self.assertEqual(
            form_item_instantiation.display_according_education,
            CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name,
        )
        self.assertEqual(form_item_instantiation.tab, Onglets.DOCUMENTS.name)

        # Save information about the request into the admission
        desired_result = {
            f'{IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name}.{form_item_instantiation.form_item.uuid}': {
                'last_actor': self.fac_manager_user.person.global_id,
                'reason': '',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
                'last_action_at': '2022-01-01T00:00:00',
                'deadline_at': '',
                'requested_at': '',
                'status': StatutEmplacementDocument.VALIDE.name,
                'request_status': '',
                'automatically_required': False,
                'related_checklist_tab': '',
            }
        }
        self.assertEqual(form_item_instantiation.admission.requested_documents, desired_result)

        # Check that a default answer to the specific question has been specified
        self.assertEqual(
            len(
                form_item_instantiation.admission.specific_question_answers.get(
                    str(form_item_instantiation.form_item.uuid), []
                ),
            ),
            1,
        )

        # Check last modification data
        self.assertEqual(form_item_instantiation.admission.modified_at, datetime.datetime.now())
        self.assertEqual(form_item_instantiation.admission.last_update_author, self.fac_manager_user.person)

    @freezegun.freeze_time('2022-01-01')
    def test_doctorate_sic_manager_requests_a_free_document_with_a_default_file(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:doctorate:document:free-candidate-request-with-default-file',
            uuid=self.doctorate_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form

        # With no data
        response = self.client.post(url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'free-document-request-with-default-file-form-file_name': 'My file name',
                'free-document-request-with-default-file-form-file_0': ['file_0-token'],
                'free-document-request-with-default-file-form-document_type': '',
                'free-document-request-with-default-file-form-checklist_tab': OngletsChecklistDoctorale.assimilation.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        # Create a specific question linked to the admission
        form_item_instantiation: AdmissionFormItemInstantiation = (
            AdmissionFormItemInstantiation.objects.select_related('form_item', 'admission')
            .filter(
                admission=self.doctorate_admission,
            )
            .first()
        )
        self.assertIsNotNone(form_item_instantiation)

        self.assertEqual(form_item_instantiation.form_item.type, TypeItemFormulaire.DOCUMENT.name)
        self.assertEqual(
            form_item_instantiation.form_item.title,
            {
                'en': 'My file name',
                'fr-be': 'My file name',
            },
        )

        self.assertEqual(form_item_instantiation.admission_id, self.doctorate_admission.pk)
        self.assertEqual(form_item_instantiation.academic_year_id, self.doctorate_admission.determined_academic_year_id)
        self.assertEqual(form_item_instantiation.required, False)
        self.assertEqual(
            form_item_instantiation.display_according_education,
            CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name,
        )
        self.assertEqual(form_item_instantiation.tab, Onglets.DOCUMENTS.name)

        # Save information about the request into the admission
        desired_result = {
            f'{IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name}.{form_item_instantiation.form_item.uuid}': {
                'last_actor': self.sic_manager_user.person.global_id,
                'reason': '',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                'last_action_at': '2022-01-01T00:00:00',
                'deadline_at': '',
                'requested_at': '',
                'status': StatutEmplacementDocument.VALIDE.name,
                'automatically_required': False,
                'request_status': '',
                'related_checklist_tab': OngletsChecklistDoctorale.assimilation.name,
            }
        }
        self.assertEqual(form_item_instantiation.admission.requested_documents, desired_result)

        # Check that a default answer to the specific question has been specified
        self.assertEqual(
            len(
                form_item_instantiation.admission.specific_question_answers.get(
                    str(form_item_instantiation.form_item.uuid), []
                ),
            ),
            1,
        )

        # Check last modification data
        self.assertEqual(form_item_instantiation.admission.modified_at, datetime.datetime.now())
        self.assertEqual(form_item_instantiation.admission.last_update_author, self.sic_manager_user.person)

    @freezegun.freeze_time('2022-01-01')
    def test_doctorate_sic_manager_requests_a_free_document_with_a_default_file_and_a_predefined_configuration(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:doctorate:document:free-candidate-request-with-default-file',
            uuid=self.doctorate_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form

        # With no data
        response = self.client.post(url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))

        # With invalid chosen predefined file
        categorized_document = CategorizedFreeDocumentFactory(
            checklist_tab=OngletsChecklistDoctorale.parcours_anterieur.name,
            with_academic_year=False,
        )
        response = self.client.post(
            url,
            data={
                'free-document-request-with-default-file-form-file_name': 'My file name',
                'free-document-request-with-default-file-form-request_status': (
                    StatutReclamationEmplacementDocument.IMMEDIATEMENT.name
                ),
                'free-document-request-with-default-file-form-checklist_tab': OngletsChecklistDoctorale.assimilation.name,
                'free-document-request-with-default-file-form-document_type': categorized_document.pk,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        # Because the selected checklist tab and the selected document checklist tab must be the same
        self.assertIn(
            gettext('The document must be related to the specified checklist tab'),
            response.context['form'].errors.get('checklist_tab', []),
        )
        self.assertNotIn('academic_year', response.context['form'].errors)

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'free-document-request-with-default-file-form-file_name': 'My file name',
                'free-document-request-with-default-file-form-file_0': ['file_0-token'],
                'free-document-request-with-default-file-form-document_type': categorized_document.pk,
                'free-document-request-with-default-file-form-checklist_tab': OngletsChecklistDoctorale.parcours_anterieur.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        # Create a specific question linked to the admission
        form_item_instantiation: AdmissionFormItemInstantiation = (
            AdmissionFormItemInstantiation.objects.select_related('form_item', 'admission')
            .filter(
                admission=self.doctorate_admission,
            )
            .first()
        )
        self.assertIsNotNone(form_item_instantiation)

        self.assertEqual(form_item_instantiation.form_item.type, TypeItemFormulaire.DOCUMENT.name)
        self.assertEqual(
            form_item_instantiation.form_item.title,
            {
                'en': categorized_document.long_label_en,
                'fr-be': categorized_document.long_label_fr,
            },
        )

        self.assertEqual(form_item_instantiation.admission_id, self.doctorate_admission.pk)
        self.assertEqual(form_item_instantiation.academic_year_id, self.doctorate_admission.determined_academic_year_id)
        self.assertEqual(form_item_instantiation.required, False)
        self.assertEqual(
            form_item_instantiation.display_according_education,
            CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name,
        )
        self.assertEqual(form_item_instantiation.tab, Onglets.DOCUMENTS.name)

        # Save information about the request into the admission
        desired_result = {
            f'{IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name}.{form_item_instantiation.form_item.uuid}': {
                'last_actor': self.sic_manager_user.person.global_id,
                'reason': '',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                'last_action_at': '2022-01-01T00:00:00',
                'deadline_at': '',
                'requested_at': '',
                'status': StatutEmplacementDocument.VALIDE.name,
                'automatically_required': False,
                'request_status': '',
                'related_checklist_tab': OngletsChecklistDoctorale.parcours_anterieur.name,
            }
        }
        self.assertEqual(form_item_instantiation.admission.requested_documents, desired_result)

        # Check that a default answer to the specific question has been specified
        self.assertEqual(
            len(
                form_item_instantiation.admission.specific_question_answers.get(
                    str(form_item_instantiation.form_item.uuid), []
                ),
            ),
            1,
        )

        # Check last modification data
        self.assertEqual(form_item_instantiation.admission.modified_at, datetime.datetime.now())
        self.assertEqual(form_item_instantiation.admission.last_update_author, self.sic_manager_user.person)

    @freezegun.freeze_time('2022-01-01')
    def test_doctorate_fac_manager_requests_a_free_document_with_a_default_file(self):
        self.doctorate_admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.doctorate_admission.save(update_fields=['status'])

        self.client.force_login(user=self.doctorate_fac_manager_user)

        url = resolve_url(
            'admission:doctorate:document:free-candidate-request-with-default-file',
            uuid=self.doctorate_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form
        response = self.client.post(url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'free-document-request-with-default-file-form-file_name': 'My file name',
                'free-document-request-with-default-file-form-file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        # Create a specific question linked to the admission
        form_item_instantiation: AdmissionFormItemInstantiation = (
            AdmissionFormItemInstantiation.objects.select_related('form_item', 'admission')
            .filter(
                admission=self.doctorate_admission,
            )
            .first()
        )
        self.assertIsNotNone(form_item_instantiation)

        self.assertEqual(form_item_instantiation.form_item.type, TypeItemFormulaire.DOCUMENT.name)
        self.assertEqual(
            form_item_instantiation.form_item.title,
            {
                'en': 'My file name',
                'fr-be': 'My file name',
            },
        )

        self.assertEqual(form_item_instantiation.admission_id, self.doctorate_admission.pk)
        self.assertEqual(form_item_instantiation.academic_year_id, self.doctorate_admission.determined_academic_year_id)
        self.assertEqual(form_item_instantiation.required, False)
        self.assertEqual(
            form_item_instantiation.display_according_education,
            CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name,
        )
        self.assertEqual(form_item_instantiation.tab, Onglets.DOCUMENTS.name)

        # Save information about the request into the admission
        desired_result = {
            f'{IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name}.{form_item_instantiation.form_item.uuid}': {
                'last_actor': self.doctorate_fac_manager_user.person.global_id,
                'reason': '',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
                'last_action_at': '2022-01-01T00:00:00',
                'deadline_at': '',
                'requested_at': '',
                'status': StatutEmplacementDocument.VALIDE.name,
                'request_status': '',
                'automatically_required': False,
                'related_checklist_tab': '',
            }
        }
        self.assertEqual(form_item_instantiation.admission.requested_documents, desired_result)

        # Check that a default answer to the specific question has been specified
        self.assertEqual(
            len(
                form_item_instantiation.admission.specific_question_answers.get(
                    str(form_item_instantiation.form_item.uuid), []
                ),
            ),
            1,
        )

        # Check last modification data
        self.assertEqual(form_item_instantiation.admission.modified_at, datetime.datetime.now())
        self.assertEqual(form_item_instantiation.admission.last_update_author, self.doctorate_fac_manager_user.person)
