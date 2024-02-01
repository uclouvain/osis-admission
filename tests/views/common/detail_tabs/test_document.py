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
from email import message_from_string
from unittest import mock
from unittest.mock import patch

import freezegun
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification
from rest_framework import status

from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories.person import CompletePersonFactory
from base.forms.utils.choice_field import BLANK_CHOICE
from osis_document.contrib.forms import FileUploadField

from admission.constants import PDF_MIME_TYPE, FIELD_REQUIRED_MESSAGE, IMAGE_MIME_TYPES, SUPPORTED_MIME_TYPES
from admission.contrib.models import GeneralEducationAdmission, AdmissionFormItemInstantiation, AdmissionFormItem
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.enums import TypeItemFormulaire, CritereItemFormulaireFormation, Onglets
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    IdentifiantBaseEmplacementDocument,
    StatutEmplacementDocument,
    EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES,
    EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES,
    OngletsDemande,
    IDENTIFIANT_BASE_EMPLACEMENT_DOCUMENT_LIBRE_PAR_TYPE,
    StatutReclamationEmplacementDocument,
)
from admission.forms import AdmissionFileUploadField
from admission.infrastructure.utils import MODEL_FIELD_BY_FREE_MANAGER_DOCUMENT_TYPE
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DocumentViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(
            entity=cls.first_doctoral_commission,
        )

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.second_sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.second_fac_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group
        ).person.user

        cls.file_uuid = uuid.uuid4()
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.non_free_document_identifier = f'{OngletsDemande.CURRICULUM.name}.CURRICULUM'

    def setUp(self):
        # Mock documents
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('admission.templatetags.admission.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.change_remote_metadata', return_value='foobar')
        self.change_remote_metadata_patcher = patcher.start()
        self.addCleanup(patcher.stop)

        self.file_metadata = {
            'name': 'myfile',
            'mimetype': PDF_MIME_TYPE,
            'explicit_name': 'My file name',
            'author': self.sic_manager_user.person.global_id,
        }

        patcher = patch('admission.templatetags.admission.get_remote_metadata', return_value=self.file_metadata)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.get_remote_metadata', return_value=self.file_metadata)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            'osis_document.api.utils.confirm_remote_upload',
            side_effect=lambda **kwargs: uuid.uuid4(),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            'osis_document.contrib.fields.FileField._confirm_multiple_upload',
            side_effect=lambda _, value, __: [uuid.uuid4()] if value else [],
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {token: self.file_metadata for token in tokens}
        self.addCleanup(patcher.stop)

        # Reset the admission
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
                private_email='candidate@test.be',
            ),
            curriculum=[uuid.uuid4()],
            pdf_recap=[uuid.uuid4()],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

    def _create_a_free_document(self, user: User, document_type: str, url='', data=None, with_file=False):
        """Create a document of a specific type using the given user."""

        if document_type in EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES:
            default_base_url = 'admission:general-education:document:free-candidate-request'
            default_data = {
                'author': user.person.global_id,
                'file_name': 'My file name',
                'reason': 'My reason',
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            }
            if with_file:
                default_data['file_0'] = ['file_0-token']
                default_data['file_name'] += ' with default file'
        elif document_type in EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES:
            default_base_url = 'admission:general-education:document:free-internal-upload'
            default_data = {
                'author': user.person.global_id,
                'file_name': 'My file name',
                'file_0': ['file_0-token'],
            }
        else:
            raise NotImplementedError

        url = resolve_url(url or default_base_url, uuid=self.general_admission.uuid)

        response = self.client.post(
            url,
            data=data or default_data,
            **self.default_headers,
        )

        if response.status_code == 200:
            if document_type in EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES:
                document_uuid = AdmissionFormItem.objects.values('uuid').last()['uuid']
            else:
                self.general_admission.refresh_from_db()
                document_uuid = next(
                    reversed(getattr(self.general_admission, MODEL_FIELD_BY_FREE_MANAGER_DOCUMENT_TYPE[document_type]))
                )
            return f'{IDENTIFIANT_BASE_EMPLACEMENT_DOCUMENT_LIBRE_PAR_TYPE[document_type]}.{document_uuid}'
        return ''

    def init_documents(self, for_fac: bool = False, for_sic: bool = True):
        self.client.force_login(user=self.sic_manager_user)
        default_status = self.general_admission.status
        self.sic_free_non_requestable_internal_document = self._create_a_free_document(
            self.sic_manager_user,
            TypeEmplacementDocument.LIBRE_INTERNE_SIC.name,
        )
        self.sic_free_requestable_candidate_document_with_default_file = self._create_a_free_document(
            self.sic_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
            with_file=True,
        )
        self.sic_free_requestable_document = self._create_a_free_document(
            self.sic_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
        )

        self.client.force_login(user=self.fac_manager_user)
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save(update_fields=['status'])
        self.general_admission.refresh_from_db()
        self.fac_free_non_requestable_internal_document = self._create_a_free_document(
            self.fac_manager_user,
            TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
        )
        self.fac_free_requestable_candidate_document_with_default_file = self._create_a_free_document(
            self.fac_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
            with_file=True,
        )
        self.fac_free_requestable_document = self._create_a_free_document(
            self.fac_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
        )

        if for_fac:
            return

        if for_sic:
            self.general_admission.status = default_status
            self.general_admission.save(update_fields=['status'])
            self.general_admission.refresh_from_db()

    # The manager uploads a free document that only the other managers can view
    @freezegun.freeze_time('2022-01-01')
    def test_general_sic_manager_uploads_free_and_readonly_internal_document(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-internal-upload',
            uuid=self.general_admission.uuid,
        )

        # Retrieve the empty form
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form
        # Empty data
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
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
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            AdmissionFileUploadField.default_error_messages['max_files'],
            response.context['form'].errors.get('file', []),
        )

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'file_name': 'My file name',
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].data, {})

        # Save the file into the admission
        self.general_admission.refresh_from_db()
        self.assertNotEqual(self.general_admission.uclouvain_sic_documents, [])
        self.assertEqual(self.general_admission.uclouvain_fac_documents, [])

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

    @freezegun.freeze_time('2022-01-01')
    def test_general_fac_manager_uploads_free_and_readonly_internal_document(self):
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save(update_fields=['status'])

        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-internal-upload',
            uuid=self.general_admission.uuid,
        )

        # Retrieve the empty form
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form
        # Empty data
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
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
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            AdmissionFileUploadField.default_error_messages['max_files'],
            response.context['form'].errors.get('file', []),
        )

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'file_name': 'My file name',
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].data, {})

        # Save the file into the admission
        self.general_admission.refresh_from_db()
        self.assertNotEqual(self.general_admission.uclouvain_fac_documents, [])
        self.assertEqual(self.general_admission.uclouvain_sic_documents, [])

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

    def _mock_folder_generation(self):
        save_raw_content_remotely_patcher = mock.patch('osis_document.utils.save_raw_content_remotely')
        patched = save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'
        self.addCleanup(save_raw_content_remotely_patcher.stop)

        # Mock weasyprint
        patcher = mock.patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()

        # Mock pikepdf
        patcher = mock.patch('admission.exports.admission_recap.admission_recap.Pdf')
        patched = patcher.start()
        patched.new.return_value = mock.MagicMock(pdf_version=1)
        self.outline_root = (
            patched.new.return_value.open_outline.return_value.__enter__.return_value.root
        ) = mock.MagicMock()
        patched.open.return_value.__enter__.return_value = mock.Mock(pdf_version=1, pages=[None])

        patcher = mock.patch('admission.exports.admission_recap.attachments.get_raw_content_remotely')
        self.get_raw_content_mock = patcher.start()
        self.get_raw_content_mock.return_value = b'some content'

        patcher = mock.patch('admission.exports.admission_recap.admission_recap.save_raw_content_remotely')
        self.save_raw_content_mock = patcher.start()
        self.save_raw_content_mock.return_value = 'pdf-token'

    @freezegun.freeze_time('2022-01-01')
    def test_general_sic_manager_generates_new_analysis_folder(self):
        self._mock_folder_generation()

        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:analysis-folder-generation',
            uuid=self.general_admission.uuid,
        )

        # Submit a valid form
        response = self.client.post(
            url,
            **self.default_headers,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].data, {})

        # Save the file into the admission
        self.general_admission.refresh_from_db()
        self.assertNotEqual(self.general_admission.uclouvain_sic_documents, [])
        self.assertEqual(self.general_admission.uclouvain_fac_documents, [])

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='pdf-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': gettext('Analysis folder'),
            },
        )

    # The manager requests a free document that the candidate must upload
    @freezegun.freeze_time('2022-01-01')
    def test_general_sic_manager_requests_a_free_document(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-request',
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
                'file_name': 'My file name',
                'reason': 'My reason',
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
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
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                'last_action_at': '2022-01-01T00:00:00',
                'deadline_at': '',
                'requested_at': '',
                'status': StatutEmplacementDocument.A_RECLAMER.name,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'automatically_required': False,
            }
        }
        self.assertEqual(form_item_instantiation.admission.requested_documents, desired_result)

        # Check last modification data
        self.assertEqual(form_item_instantiation.admission.modified_at, datetime.datetime.now())
        self.assertEqual(form_item_instantiation.admission.last_update_author, self.sic_manager_user.person)

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
        response = self.client.post(url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'file_name': 'My file name',
                'file_0': ['file_0-token'],
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
    def test_general_fac_manager_requests_a_free_document_immediately(self):
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save(update_fields=['status'])

        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-request',
            uuid=self.general_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form
        response = self.client.post(url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('request_status', []))

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'file_name': 'My file name',
                'reason': 'My reason',
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
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
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
                'last_action_at': '2022-01-01T00:00:00',
                'deadline_at': '',
                'requested_at': '',
                'status': StatutEmplacementDocument.A_RECLAMER.name,
                'automatically_required': False,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            }
        }
        self.assertEqual(form_item_instantiation.admission.requested_documents, desired_result)

        # Check last modification data
        self.assertEqual(form_item_instantiation.admission.modified_at, datetime.datetime.now())
        self.assertEqual(form_item_instantiation.admission.last_update_author, self.fac_manager_user.person)

    @freezegun.freeze_time('2022-01-01')
    def test_general_fac_manager_requests_a_free_document_for_later(self):
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save(update_fields=['status'])

        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-candidate-request',
            uuid=self.general_admission.uuid,
        )

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'file_name': 'My file name',
                'reason': 'My reason',
                'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

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
                'file_name': 'My file name',
                'file_0': ['file_0-token'],
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

    # The manager updates the reason of a free document that the candidate must upload
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_sic_manager_updates_the_request_of_a_free_document(self, frozen_time):
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
                'A SIC user cannot update the document n°%s' % index,
            )

        # Create a requested document
        document_identifier = self._create_a_free_document(
            self.sic_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
        )

        form_item_instantiation = AdmissionFormItemInstantiation.objects.get(
            admission=self.general_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        )

        self.assertEqual(form_item_instantiation.required, False)

        self.client.force_login(user=self.second_sic_manager_user)

        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        frozen_time.move_to('2022-01-03')

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
                'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
                'reason': 'My new reason',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Update the information about the request into the admission
        desired_result = {
            'last_actor': self.second_sic_manager_user.person.global_id,
            'reason': 'My new reason',
            'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
            'last_action_at': '2022-01-03T00:00:00',
            'deadline_at': '',
            'requested_at': '',
            'status': StatutEmplacementDocument.A_RECLAMER.name,
            'automatically_required': False,
            'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
        }
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.requested_documents.get(document_identifier), desired_result)

        # Check the specific question
        form_item_instantiation.refresh_from_db()
        self.assertEqual(form_item_instantiation.required, False)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_sic_manager_user.person)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_fac_manager_updates_the_request_of_a_free_document(self, frozen_time):
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
                # Or created by a sic manager
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
                'A FAC user cannot update the document n°%s' % index,
            )

        # Create a requested document
        document_identifier = self._create_a_free_document(
            self.fac_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
        )

        form_item_instantiation = AdmissionFormItemInstantiation.objects.get(
            admission=self.general_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        )

        self.assertEqual(form_item_instantiation.required, False)

        self.client.force_login(user=self.second_fac_manager_user)

        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        frozen_time.move_to('2022-01-03')

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
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'reason': 'My new reason',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Update the information about the request into the admission
        desired_result = {
            'last_actor': self.second_fac_manager_user.person.global_id,
            'reason': 'My new reason',
            'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
            'last_action_at': '2022-01-03T00:00:00',
            'deadline_at': '',
            'requested_at': '',
            'status': StatutEmplacementDocument.A_RECLAMER.name,
            'automatically_required': False,
            'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
        }
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.requested_documents.get(document_identifier), desired_result)

        # Check the specific question
        form_item_instantiation.refresh_from_db()
        self.assertEqual(form_item_instantiation.required, False)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_fac_manager_user.person)

    # The manager requests a non free document
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_manager_updates_the_request_of_a_non_free_document(self, frozen_time):
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

        # Post a valid form
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

        # Update the information about the request into the admission
        desired_result = {
            'last_actor': self.sic_manager_user.person.global_id,
            'reason': 'My reason',
            'type': TypeEmplacementDocument.NON_LIBRE.name,
            'last_action_at': '2022-01-01T00:00:00',
            'deadline_at': '',
            'requested_at': '',
            'status': StatutEmplacementDocument.A_RECLAMER.name,
            'automatically_required': False,
            'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
        }
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.requested_documents.get(self.non_free_document_identifier),
            desired_result,
        )

        # A second SIC user can update a categorized document
        self.client.force_login(user=self.second_sic_manager_user)

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

        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        frozen_time.move_to('2022-01-02')

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT.name,
                'reason': 'My new reason',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Update the information about the request into the admission
        desired_result = {
            'last_actor': self.second_sic_manager_user.person.global_id,
            'reason': 'My new reason',
            'type': TypeEmplacementDocument.NON_LIBRE.name,
            'last_action_at': '2022-01-02T00:00:00',
            'deadline_at': '',
            'requested_at': '',
            'status': StatutEmplacementDocument.A_RECLAMER.name,
            'automatically_required': False,
            'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT.name,
        }
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.requested_documents.get(self.non_free_document_identifier),
            desired_result,
        )

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
        self.assertEqual(response.context['request_reason'], 'My new reason')
        form = response.context['form']
        self.assertEqual(form.fields['request_status'].required, False)

        frozen_time.move_to('2022-01-03')

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
                'reason': 'My new reason 3',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Update the information about the request into the admission
        desired_result = {
            'last_actor': self.second_sic_manager_user.person.global_id,
            'reason': 'My new reason 3',
            'type': TypeEmplacementDocument.NON_LIBRE.name,
            'last_action_at': '2022-01-03T00:00:00',
            'deadline_at': '',
            'requested_at': '',
            'status': StatutEmplacementDocument.A_RECLAMER.name,
            'automatically_required': True,
            'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
        }
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.requested_documents.get(self.non_free_document_identifier),
            desired_result,
        )

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_sic_manager_user.person)

        # Don't request the document anymore
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'request_status': '',
                'reason': '',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())
        self.general_admission.refresh_from_db()
        self.assertIsNone(self.general_admission.requested_documents.get(self.non_free_document_identifier))

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
                'A SIC user cannot update the document n°%s' % index,
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
                'A FAC user cannot update the document n°%s' % index,
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

    # The manager replaces the document
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_sic_manager_replaces_a_document(self, frozen_time):
        self.init_documents(for_sic=True)

        base_url = 'admission:general-education:document:replace'

        self.client.force_login(user=self.sic_manager_user)

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A SIC manager cannot replace FAC documents
            self.fac_free_non_requestable_internal_document,
            self.fac_free_requestable_candidate_document_with_default_file,
            self.fac_free_requestable_document,
            # Or system ones
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A SIC manager can replace SIC documents
        # Internal document
        self.change_remote_metadata_patcher.reset_mock()
        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        self.general_admission.refresh_from_db()
        old_document_uuid = uuid.UUID(self.sic_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(old_document_uuid, self.general_admission.uclouvain_sic_documents)
        self.assertEqual(len(self.general_admission.uclouvain_sic_documents), 1)
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.sic_free_non_requestable_internal_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.general_admission.refresh_from_db()
        self.assertNotIn(old_document_uuid, self.general_admission.uclouvain_sic_documents)
        self.assertEqual(len(self.general_admission.uclouvain_sic_documents), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Requestable document
        self.change_remote_metadata_patcher.reset_mock()
        specific_question_uuid = str(uuid.UUID(self.sic_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-04')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        old_document_uuid = self.general_admission.requested_documents.get(self.sic_free_requestable_document)
        self.assertIsNotNone(old_document_uuid)

        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.sic_free_requestable_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.general_admission.refresh_from_db()
        self.assertNotEqual(
            self.general_admission.specific_question_answers.get(specific_question_uuid),
            old_document_uuid,
        )
        self.assertEqual(len(self.general_admission.specific_question_answers.get(specific_question_uuid)), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
            },
        )

        # Non free document
        old_document_uuid = [uuid.uuid4()]
        self.general_admission.curriculum = old_document_uuid
        frozen_time.move_to('2022-01-05')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['curriculum', 'last_update_author'])
        self.change_remote_metadata_patcher.reset_mock()

        # Get the form with the right configuration depending on the document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.fields['file'].max_files, 1)
        self.assertEqual(form.fields['file'].min_files, 1)
        self.assertCountEqual(form.fields['file'].mimetypes, [PDF_MIME_TYPE])

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertCountEqual(form.fields['file'].mimetypes, list(IMAGE_MIME_TYPES))

        # Post an invalid form -> at least one file must be specified
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
        self.assertFalse(form.is_valid())
        self.assertIn(FileUploadField.default_error_messages['min_files'], form.errors.get('file', []))

        # Post an invalid form -> only one file must be specified
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'file_0': ['file_0-token'],
                'file_1': ['file_1-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertIn(FileUploadField.default_error_messages['max_files'], form.errors.get('file', []))

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.general_admission.refresh_from_db()
        self.assertNotEqual(self.general_admission.curriculum, old_document_uuid)
        self.assertEqual(len(self.general_admission.curriculum), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
            },
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_fac_manager_replaces_a_document(self, frozen_time):
        self.init_documents(for_fac=True)

        base_url = 'admission:general-education:document:replace'

        self.client.force_login(user=self.fac_manager_user)

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A FAC manager cannot replace SIC documents
            self.sic_free_non_requestable_internal_document,
            self.sic_free_requestable_candidate_document_with_default_file,
            self.sic_free_requestable_document,
            # Or system ones
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A FAC manager can replace FAC documents
        # Internal document
        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        self.general_admission.refresh_from_db()
        self.change_remote_metadata_patcher.reset_mock()
        old_document_uuid = uuid.UUID(self.fac_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(old_document_uuid, self.general_admission.uclouvain_fac_documents)
        self.assertEqual(len(self.general_admission.uclouvain_fac_documents), 1)
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.fac_free_non_requestable_internal_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.general_admission.refresh_from_db()
        self.assertNotIn(old_document_uuid, self.general_admission.uclouvain_fac_documents)
        self.assertEqual(len(self.general_admission.uclouvain_fac_documents), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Requestable document
        self.change_remote_metadata_patcher.reset_mock()
        specific_question_uuid = str(uuid.UUID(self.fac_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        old_document_uuid = self.general_admission.requested_documents.get(self.fac_free_requestable_document)
        self.assertIsNotNone(old_document_uuid)

        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.fac_free_requestable_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.fac_manager_user.person.global_id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.general_admission.refresh_from_db()
        self.assertNotEqual(
            self.general_admission.specific_question_answers.get(specific_question_uuid),
            old_document_uuid,
        )
        self.assertEqual(len(self.general_admission.specific_question_answers.get(specific_question_uuid)), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)

        # Replace a non free document is not allowed for a FAC manager
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 403)

    # The manager uploads the document
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_sic_manager_uploads_a_document(self, frozen_time):
        self.init_documents(for_sic=True)

        base_url = 'admission:general-education:document:upload'

        self.client.force_login(user=self.sic_manager_user)

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A SIC manager cannot upload FAC documents
            self.fac_free_non_requestable_internal_document,
            self.fac_free_requestable_candidate_document_with_default_file,
            self.fac_free_requestable_document,
            # Or system ones
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A SIC manager can upload SIC documents
        # Internal document
        self.change_remote_metadata_patcher.reset_mock()
        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        self.general_admission.refresh_from_db()
        old_document_uuid = uuid.UUID(self.sic_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(old_document_uuid, self.general_admission.uclouvain_sic_documents)
        self.assertEqual(len(self.general_admission.uclouvain_sic_documents), 1)
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.sic_free_non_requestable_internal_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.general_admission.refresh_from_db()
        self.assertNotIn(old_document_uuid, self.general_admission.uclouvain_sic_documents)
        self.assertEqual(len(self.general_admission.uclouvain_sic_documents), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Requestable document
        self.change_remote_metadata_patcher.reset_mock()
        specific_question_uuid = str(uuid.UUID(self.sic_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-04')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        old_document_uuid = self.general_admission.requested_documents.get(self.sic_free_requestable_document)
        self.assertIsNotNone(old_document_uuid)

        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.sic_free_requestable_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.general_admission.refresh_from_db()
        self.assertNotEqual(
            self.general_admission.specific_question_answers.get(specific_question_uuid),
            old_document_uuid,
        )
        self.assertEqual(len(self.general_admission.specific_question_answers.get(specific_question_uuid)), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
            },
        )

        # Non free document
        self.change_remote_metadata_patcher.reset_mock()
        old_document_uuid = [uuid.uuid4()]
        self.general_admission.curriculum = old_document_uuid
        frozen_time.move_to('2022-01-05')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['curriculum', 'last_update_author'])

        # Get the form with the right configuration depending on the document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.fields['file'].max_files, 1)
        self.assertEqual(form.fields['file'].min_files, 1)
        self.assertCountEqual(form.fields['file'].mimetypes, [PDF_MIME_TYPE])

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertCountEqual(form.fields['file'].mimetypes, list(IMAGE_MIME_TYPES))

        # Post an invalid form -> at least one file must be specified
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
        self.assertFalse(form.is_valid())
        self.assertIn(FileUploadField.default_error_messages['min_files'], form.errors.get('file', []))

        # Post an invalid form -> only one file must be specified
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'file_0': ['file_0-token'],
                'file_1': ['file_1-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertIn(FileUploadField.default_error_messages['max_files'], form.errors.get('file', []))

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.general_admission.refresh_from_db()
        self.assertNotEqual(self.general_admission.curriculum, old_document_uuid)
        self.assertEqual(len(self.general_admission.curriculum), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
            },
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_fac_manager_uploads_a_document(self, frozen_time):
        self.init_documents(for_fac=True)

        base_url = 'admission:general-education:document:upload'

        self.client.force_login(user=self.fac_manager_user)

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A FAC manager cannot upload SIC documents
            self.sic_free_non_requestable_internal_document,
            self.sic_free_requestable_candidate_document_with_default_file,
            self.sic_free_requestable_document,
            # Or system ones
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A FAC manager can upload FAC documents
        # Internal document
        self.change_remote_metadata_patcher.reset_mock()
        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        self.general_admission.refresh_from_db()
        old_document_uuid = uuid.UUID(self.fac_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(old_document_uuid, self.general_admission.uclouvain_fac_documents)
        self.assertEqual(len(self.general_admission.uclouvain_fac_documents), 1)
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.fac_free_non_requestable_internal_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        # Check last modification data
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(old_document_uuid, self.general_admission.uclouvain_fac_documents)
        self.assertEqual(len(self.general_admission.uclouvain_fac_documents), 1)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Requestable document
        self.change_remote_metadata_patcher.reset_mock()
        specific_question_uuid = str(uuid.UUID(self.fac_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-04')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        old_document_uuid = self.general_admission.requested_documents.get(self.fac_free_requestable_document)
        self.assertIsNotNone(old_document_uuid)

        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.fac_free_requestable_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.general_admission.refresh_from_db()
        self.assertNotEqual(
            self.general_admission.specific_question_answers.get(specific_question_uuid),
            old_document_uuid,
        )
        self.assertEqual(len(self.general_admission.specific_question_answers.get(specific_question_uuid)), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.fac_manager_user.person.global_id,
            },
        )

        # Replace a non free document is not allowed for a FAC manager
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 403)

    # Lists of documents
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_document_detail_sic_manager(self, frozen_time):
        self.init_documents(for_sic=True)

        self.client.force_login(user=self.second_sic_manager_user)

        url = resolve_url('admission:general-education:documents', uuid=self.general_admission.uuid)

        # Get the list and the request form
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)
        self.assertTrue(len(response.context['documents']) > 0)

        form = response.context['form']
        self.assertEqual(form['deadline'].value(), datetime.date(2022, 1, 16))
        self.assertEqual(
            form['message_object'].value(),
            "Inscription UCLouvain – compléter votre dossier " f"({response.context['admission'].reference})",
        )

        first_field = form.fields.get(self.sic_free_requestable_candidate_document_with_default_file)
        self.assertIsNotNone(first_field)
        self.assertEqual(
            first_field.label,
            '<span class="fa-solid fa-link-slash"></span> My file name with default file',
        )
        self.assertEqual(first_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        second_field = form.fields.get(self.sic_free_requestable_document)
        self.assertIsNotNone(second_field)
        self.assertEqual(
            second_field.label,
            '<span class="fa-solid fa-link-slash"></span> My file name',
        )
        self.assertEqual(second_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        # Custom deadline in the second part of September
        with freezegun.freeze_time('2022-09-20'):
            self.client.force_login(user=self.second_sic_manager_user)

            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)

            form = response.context['form']
            self.assertEqual(form['deadline'].value(), datetime.date(2022, 9, 30))

        # Post an invalid form -> missing fields
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('deadline', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_object', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_content', []))
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        # Post an invalid form -> invalid identifiers
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.fac_free_requestable_document: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])

        # Post a valid form
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.sic_free_requestable_document: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                self.sic_free_requestable_candidate_document_with_default_file: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        self.general_admission.refresh_from_db()

        # Check that the requested documents have been updated
        self.assertEqual(
            self.general_admission.requested_documents[self.sic_free_requestable_document],
            {
                'last_actor': self.second_sic_manager_user.person.global_id,
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                'last_action_at': '2022-01-03T00:00:00',
                'status': StatutEmplacementDocument.RECLAME.name,
                'requested_at': '2022-01-03T00:00:00',
                'deadline_at': '2022-01-15',
                'automatically_required': False,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            },
        )

        # Check that the proposition status has been changed
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_sic_manager_user.person)

        # Check that the email has been sent to the candidate
        self.assertEqual(EmailNotification.objects.count(), 1)
        email_notification: EmailNotification = EmailNotification.objects.first()
        self.assertEqual(email_notification.person, self.general_admission.candidate)
        email_object = message_from_string(email_notification.payload)
        self.assertEqual(email_object['To'], 'candidate@test.be')
        self.assertIn(form.cleaned_data['message_content'], email_notification.payload)
        self.assertIn(form.cleaned_data['message_object'], email_notification.payload)

        # Check history
        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid).count(), 2)
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.general_admission.uuid,
                tags=['proposition', 'message'],
            ).exists()
        )
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.general_admission.uuid,
                tags=['proposition', 'status-changed'],
            ).exists()
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_document_detail_fac_manager(self, frozen_time):
        self.init_documents(for_fac=True)

        self.client.force_login(user=self.second_fac_manager_user)

        url = resolve_url('admission:general-education:documents', uuid=self.general_admission.uuid)

        # Get the list and the request form
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)
        self.assertTrue(len(response.context['documents']) > 0)

        form = response.context['form']
        self.assertEqual(form['deadline'].value(), datetime.date(2022, 1, 16))
        self.assertEqual(
            form['message_object'].value(),
            "Inscription UCLouvain – compléter votre dossier " f"({response.context['admission'].reference})",
        )

        first_field = form.fields.get(self.fac_free_requestable_candidate_document_with_default_file)
        self.assertIsNotNone(first_field)
        self.assertEqual(
            first_field.label,
            '<span class="fa-solid fa-link-slash"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name with default file',
        )
        self.assertEqual(first_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        second_field = form.fields.get(self.fac_free_requestable_document)
        self.assertIsNotNone(second_field)
        self.assertEqual(
            second_field.label,
            '<span class="fa-solid fa-link-slash"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name',
        )
        self.assertEqual(second_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        # Simulate that the field is not missing but still requested
        self.general_admission.refresh_from_db()
        specific_question_uuid = str(uuid.UUID(self.fac_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        self.general_admission.save(update_fields=['specific_question_answers'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        form = response.context['form']

        first_field = form.fields.get(self.fac_free_requestable_candidate_document_with_default_file)
        self.assertIsNotNone(first_field)
        self.assertEqual(
            first_field.label,
            '<span class="fa-solid fa-link-slash"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name with default file',
        )
        self.assertEqual(first_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        second_field = form.fields.get(self.fac_free_requestable_document)
        self.assertIsNotNone(second_field)
        self.assertEqual(
            second_field.label,
            '<span class="fa-solid fa-paperclip"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name',
        )

        self.general_admission.specific_question_answers.pop(specific_question_uuid)
        self.general_admission.save(update_fields=['specific_question_answers'])

        # Post an invalid form -> missing fields
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('deadline', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_object', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_content', []))
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        # Post an invalid form -> invalid identifiers
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.sic_free_requestable_document: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])

        # Post a valid form
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.fac_free_requestable_document: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                self.fac_free_requestable_candidate_document_with_default_file: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        self.general_admission.refresh_from_db()

        # Check that the requested documents have been updated
        self.assertEqual(
            self.general_admission.requested_documents[self.fac_free_requestable_document],
            {
                'last_actor': self.second_fac_manager_user.person.global_id,
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
                'last_action_at': '2022-01-03T00:00:00',
                'status': StatutEmplacementDocument.RECLAME.name,
                'requested_at': '2022-01-03T00:00:00',
                'deadline_at': '2022-01-15',
                'automatically_required': False,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            },
        )

        # Check that the proposition status has been changed
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_fac_manager_user.person)

        # Check that the email has been sent to the candidate
        self.assertEqual(EmailNotification.objects.count(), 1)
        email_notification: EmailNotification = EmailNotification.objects.first()
        self.assertEqual(email_notification.person, self.general_admission.candidate)
        email_object = message_from_string(email_notification.payload)
        self.assertEqual(email_object['To'], 'candidate@test.be')
        self.assertIn(form.cleaned_data['message_content'], email_notification.payload)
        self.assertIn(form.cleaned_data['message_object'], email_notification.payload)

        # Check history
        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid).count(), 2)
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.general_admission.uuid,
                tags=['proposition', 'message'],
            ).exists()
        )
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.general_admission.uuid,
                tags=['proposition', 'status-changed'],
            ).exists()
        )

    def test_document_detail_view(self):
        self.init_documents(for_sic=True)

        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:detail',
            uuid=self.general_admission.uuid,
            identifier=self.sic_free_requestable_document,
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Not filled document
        context = response.context
        self.assertEqual(context['document_identifier'], self.sic_free_requestable_document)
        self.assertEqual(context['document_type'], TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name)
        self.assertEqual(context['requestable_document'], True)
        self.assertEqual(context['editable_document'], True)
        self.assertEqual(context['request_reason'], 'My reason')

        # Check that the forms are well initialized
        self.assertEqual(context['request_form'].fields['request_status'].required, False)
        self.assertEqual(
            context['request_form']['request_status'].value(),
            StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
        )
        self.assertEqual(context['request_form']['reason'].value(), 'My reason')
        self.assertEqual(context['replace_form'].fields['file'].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(context['replace_form']['file'].value(), [])
        self.assertEqual(context['upload_form'].fields['file'].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(context['upload_form']['file'].value(), [])

        # Filled document
        file_uuid = uuid.uuid4()
        specific_question_uuid = str(uuid.UUID(self.sic_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [file_uuid]
        self.general_admission.save(update_fields=['specific_question_answers'])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['document_uuid'], str(file_uuid))
        self.assertEqual(context['document_write_token'], 'foobar')
        self.assertEqual(context['document_metadata'], self.file_metadata)

    # The manager updates the reason of a free document that the candidate must upload
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_sic_manager_updates_the_request_status_of_a_free_document(self, frozen_time):
        self.init_documents(for_sic=True)

        self.client.force_login(user=self.sic_manager_user)
        base_url = 'admission:general-education:document:candidate-request-status'

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
                'A SIC user cannot update the document n°%s' % index,
            )

        # Create a requested document
        document_identifier = self._create_a_free_document(
            self.sic_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
        )

        form_item_instantiation = AdmissionFormItemInstantiation.objects.get(
            admission=self.general_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        )

        self.assertEqual(form_item_instantiation.required, False)

        self.client.force_login(user=self.second_sic_manager_user)

        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])

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
        form = response.context['form']
        self.assertEqual(form.fields[document_identifier].required, False)

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=document_identifier,
            ),
            data={
                document_identifier: StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Update the information about the request into the admission
        desired_result = {
            'last_actor': self.second_sic_manager_user.person.global_id,
            'reason': 'My reason',
            'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
            'last_action_at': '2022-01-03T00:00:00',
            'deadline_at': '',
            'requested_at': '',
            'status': StatutEmplacementDocument.A_RECLAMER.name,
            'automatically_required': False,
            'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
        }
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.requested_documents.get(document_identifier), desired_result)

        # Check the specific question
        form_item_instantiation.refresh_from_db()
        self.assertEqual(form_item_instantiation.required, False)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_sic_manager_user.person)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_fac_manager_updates_the_request_status_of_a_free_document(self, frozen_time):
        self.init_documents(for_fac=True)

        self.client.force_login(user=self.fac_manager_user)
        base_url = 'admission:general-education:document:candidate-request-status'

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
                # Or created by a sic manager
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
                'A FAC user cannot update the document n°%s' % index,
            )

        # Create a requested document
        document_identifier = self._create_a_free_document(
            self.fac_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
        )

        form_item_instantiation = AdmissionFormItemInstantiation.objects.get(
            admission=self.general_admission,
            form_item__uuid=document_identifier.split('.')[-1],
        )

        self.assertEqual(form_item_instantiation.required, False)

        self.client.force_login(user=self.second_fac_manager_user)

        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])

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
        form = response.context['form']
        self.assertEqual(form.fields[document_identifier].required, False)

        # Post an invalid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=document_identifier,
            ),
            data={
                document_identifier: StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT.name,
            },
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=document_identifier,
            ),
            data={
                document_identifier: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Update the information about the request into the admission
        desired_result = {
            'last_actor': self.second_fac_manager_user.person.global_id,
            'reason': 'My reason',
            'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
            'last_action_at': '2022-01-03T00:00:00',
            'deadline_at': '',
            'requested_at': '',
            'status': StatutEmplacementDocument.A_RECLAMER.name,
            'automatically_required': False,
            'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
        }
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.requested_documents.get(document_identifier), desired_result)

        # Check the specific question
        form_item_instantiation.refresh_from_db()
        self.assertEqual(form_item_instantiation.required, False)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_fac_manager_user.person)

    # The manager requests a non free document
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_manager_updates_the_request_status_of_a_non_free_document(self, frozen_time):
        base_url = 'admission:general-education:document:candidate-request-status'

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
        form = response.context['form']
        self.assertEqual(form.fields[self.non_free_document_identifier].required, False)

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                self.non_free_document_identifier: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Update the information about the request into the admission
        desired_result = {
            'last_actor': self.sic_manager_user.person.global_id,
            'reason': '',
            'type': TypeEmplacementDocument.NON_LIBRE.name,
            'last_action_at': '2022-01-01T00:00:00',
            'deadline_at': '',
            'requested_at': '',
            'status': StatutEmplacementDocument.A_RECLAMER.name,
            'automatically_required': False,
            'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
        }
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.requested_documents.get(self.non_free_document_identifier),
            desired_result,
        )

        # A second SIC user can update a categorized document
        self.client.force_login(user=self.second_sic_manager_user)

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.fields[self.non_free_document_identifier].required, False)

        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        frozen_time.move_to('2022-01-02')

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                self.non_free_document_identifier: StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT.name,
                'reason': 'My reason',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Update the information about the request into the admission
        desired_result = {
            'last_actor': self.second_sic_manager_user.person.global_id,
            'reason': '',
            'type': TypeEmplacementDocument.NON_LIBRE.name,
            'last_action_at': '2022-01-02T00:00:00',
            'deadline_at': '',
            'requested_at': '',
            'status': StatutEmplacementDocument.A_RECLAMER.name,
            'automatically_required': False,
            'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT.name,
        }
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.requested_documents.get(self.non_free_document_identifier),
            desired_result,
        )

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
        form = response.context['form']
        self.assertEqual(form.fields[self.non_free_document_identifier].required, False)

        frozen_time.move_to('2022-01-03')

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                self.non_free_document_identifier: StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Update the information about the request into the admission
        desired_result = {
            'last_actor': self.second_sic_manager_user.person.global_id,
            'reason': '',
            'type': TypeEmplacementDocument.NON_LIBRE.name,
            'last_action_at': '2022-01-03T00:00:00',
            'deadline_at': '',
            'requested_at': '',
            'status': StatutEmplacementDocument.A_RECLAMER.name,
            'automatically_required': True,
            'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
        }
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.requested_documents.get(self.non_free_document_identifier),
            desired_result,
        )

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_sic_manager_user.person)

        # Don't request this document anymore
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                self.non_free_document_identifier: '',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())
        self.general_admission.refresh_from_db()
        self.assertIsNone(self.general_admission.requested_documents.get(self.non_free_document_identifier))

    # The manager cancels the request of a document
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_sic_manager_cancels_the_request_status_of_a_free_document(self, frozen_time):
        self.init_documents(for_sic=True)

        self.client.force_login(user=self.sic_manager_user)
        base_url = 'admission:general-education:document:candidate-request-status'

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
                'A SIC user cannot update the document n°%s' % index,
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
        form = response.context['form']
        self.assertEqual(form.fields[document_identifier].required, False)

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=document_identifier,
            ),
            data={
                document_identifier: '',
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
    def test_general_fac_manager_cancels_the_request_status_of_a_free_document(self, frozen_time):
        self.init_documents(for_fac=True)

        self.client.force_login(user=self.fac_manager_user)
        base_url = 'admission:general-education:document:candidate-request-status'

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
                'A FAC user cannot update the document n°%s' % index,
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
        form = response.context['form']
        self.assertEqual(form.fields[document_identifier].required, False)

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
    def test_general_manager_cancels_the_request_status_of_a_non_free_document(self, frozen_time):
        base_url = 'admission:general-education:document:candidate-request-status'

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
        form = response.context['form']
        self.assertEqual(form.fields[self.non_free_document_identifier].required, False)

        # Request the document
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                self.non_free_document_identifier: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
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

        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])

        # A SIC manager can cancel the request
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                self.non_free_document_identifier: '',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(form.is_valid())

        # Remove the information about the request into the admission
        self.general_admission.refresh_from_db()
        self.assertIsNone(self.general_admission.requested_documents.get(self.non_free_document_identifier))

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Request the document
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                self.non_free_document_identifier: StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
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
        form = response.context['form']
        self.assertEqual(form.fields[self.non_free_document_identifier].required, False)
        self.assertIn(BLANK_CHOICE[0], form.fields[self.non_free_document_identifier].choices)

        frozen_time.move_to('2022-01-04')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])

        # Don't request the document anymore
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

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

    # The details page is different when the application is in progress
    @freezegun.freeze_time('2022-01-01')
    def test_general_document_detail_sic_manager_when_in_progress(self):
        self.general_admission.status = ChoixStatutPropositionGenerale.EN_BROUILLON.name
        self.general_admission.save(update_fields=['status'])

        url = resolve_url('admission:general-education:documents', uuid=self.general_admission.uuid)

        self.client.force_login(user=self.second_sic_manager_user)

        # Get the list and the request form
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertInHTML(
            gettext('Until the application is submitted, you can generate a recap of the application on this page.'),
            response.content.decode('utf-8'),
        )

    def test_general_sic_manage_generated_in_progress_analysis_folder(self):
        self._mock_folder_generation()

        url = resolve_url(
            'admission:general-education:document:in-progress-analysis-folder-generation',
            uuid=self.general_admission.uuid,
        )

        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.general_admission.status = ChoixStatutPropositionGenerale.EN_BROUILLON.name
        self.general_admission.save(update_fields=['status'])

        response = self.client.get(url)

        self.assertRedirects(
            response=response,
            expected_url='http://dummyurl/file/pdf-token',
            fetch_redirect_response=False,
        )
