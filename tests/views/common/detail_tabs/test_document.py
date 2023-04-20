# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid
from unittest.mock import patch, ANY

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from admission.constants import PDF_MIME_TYPE, FIELD_REQUIRED_MESSAGE
from admission.contrib.models import GeneralEducationAdmission, AdmissionFormItem, AdmissionFormItemInstantiation
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.enums import TypeItemFormulaire, CritereItemFormulaireFormation, Onglets
from admission.ddd.admission.enums.document import TypeDocument
from admission.forms import AdmissionFileUploadField
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DocumentViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(
            entity=first_doctoral_commission,
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
        )

        cls.file_uuid = uuid.uuid4()

    def setUp(self):
        # Mock documents
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            'osis_document.api.utils.change_remote_metadata',
            return_value='foobar',
        )
        self.change_remote_metadata_patcher = patcher.start()
        self.addCleanup(patcher.stop)

        file_metadata = {
            'name': 'myfile',
            'mimetype': PDF_MIME_TYPE,
            'explicit_name': 'My file',
            'author': self.sic_manager_user.username,
        }

        patcher = patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value=file_metadata,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            'osis_document.api.utils.confirm_remote_upload',
            side_effect=lambda token, upload_to: self.file_uuid,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            'admission.infrastructure.admission.domain.service.recuperer_documents_demande.get_remote_tokens'
        )
        patched = patcher.start()
        patched.side_effect = lambda uuids: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = patch(
            'admission.infrastructure.admission.domain.service.recuperer_documents_demande.get_several_remote_metadata'
        )
        patched = patcher.start()
        patched.side_effect = lambda tokens: {token: file_metadata for token in tokens}
        self.addCleanup(patcher.stop)

    def test_general_document_detail_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url('admission:general-education:document:document', uuid=self.general_admission.uuid)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)
        self.assertTrue(len(response.context['documents']) > 0)

    def test_general_document_upload_free_candidate_document_on_get(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-upload',
            uuid=self.general_admission.uuid,
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)

    def test_general_document_upload_free_candidate_document_on_post_invalid_form(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-upload',
            uuid=self.general_admission.uuid,
        )

        # Empty data
        response = self.client.post(
            url,
            data={},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))
        self.assertIn(
            AdmissionFileUploadField.default_error_messages['min_files'],
            response.context['form'].errors.get('file', []),
        )

        # Too much files
        response = self.client.post(
            url,
            data={
                'file_0': ['file_0-token'],
                'file_1': ['file_1-token'],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            AdmissionFileUploadField.default_error_messages['max_files'],
            response.context['form'].errors.get('file', []),
        )

    def test_general_document_upload_free_candidate_document_on_post_valid_form(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-upload',
            uuid=self.general_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'file_name': 'My file name',
                'file_0': ['file_0-token'],
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)
        self.assertEqual(response.context['form'].data, {})

        # Save the file into the admission
        admission: GeneralEducationAdmission = GeneralEducationAdmission.objects.get(uuid=self.general_admission.uuid)
        self.assertEqual(admission.sic_documents, [self.file_uuid])

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.username,
                'explicit_name': 'My file name',
            },
        )

    def test_general_document_request_free_candidate_document_on_get(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-request',
            uuid=self.general_admission.uuid,
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)

    def test_general_document_request_free_candidate_document_on_post_invalid_form(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-request',
            uuid=self.general_admission.uuid,
        )
        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('reason', []))

    def test_general_document_request_free_candidate_document_on_post_valid_form(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-request',
            uuid=self.general_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'file_name': 'My file name',
                'reason': 'My reason',
            },
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
        self.assertEqual(form_item_instantiation.required, True)
        self.assertEqual(
            form_item_instantiation.display_according_education,
            CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name,
        )
        self.assertEqual(form_item_instantiation.tab, Onglets.DOCUMENTS.name)

        # Save information about the request into the admission
        self.assertEqual(
            form_item_instantiation.admission.requested_documents,
            {
                f'DOCUMENTS_ADDITIONNELS.QUESTION_SPECIFIQUE.{form_item_instantiation.form_item.uuid}': {
                    'author': self.sic_manager_user.username,
                    'reason': 'My reason',
                    'type': TypeDocument.CANDIDAT_SIC.name,
                    'last_action_at': ANY,
                }
            },
        )
