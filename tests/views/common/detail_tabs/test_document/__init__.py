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

import uuid
from unittest import mock
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from admission.contrib.models import (
    GeneralEducationAdmission,
    AdmissionFormItem,
    ContinuingEducationAdmission,
)
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES,
    EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES,
    OngletsDemande,
    IDENTIFIANT_BASE_EMPLACEMENT_DOCUMENT_LIBRE_PAR_TYPE,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.infrastructure.utils import MODEL_FIELD_BY_FREE_MANAGER_DOCUMENT_TYPE
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
    ContinuingEducationTrainingFactory,
)
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class BaseDocumentViewTestCase(TestCase):
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

        cls.continuing_training = ContinuingEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.second_sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.continuing_fac_manager_user = ProgramManagerRoleFactory(
            education_group=cls.continuing_training.education_group
        ).person.user
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
        self.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training=self.continuing_training,
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
                private_email='candidate@test.be',
            ),
            curriculum=[uuid.uuid4()],
            pdf_recap=[uuid.uuid4()],
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )

    def _create_a_free_document(
        self,
        user: User,
        document_type: str,
        url='',
        data=None,
        with_file=False,
        admission=None,
    ):
        """Create a document of a specific type using the given user."""

        if not admission:
            admission = self.general_admission

        if admission.admission_context == 'continuing-education':
            document_type = document_type.replace('SIC', 'FAC')

        if document_type in EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES:
            default_base_url = f'admission:{admission.admission_context}:document:free-candidate-request'
            default_data = {
                'free-document-request-form-author': user.person.global_id,
                'free-document-request-form-file_name': 'My file name',
                'free-document-request-form-reason': 'My reason',
                'free-document-request-form-request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            }
            if with_file:
                default_data['free-document-request-form-file_0'] = ['file_0-token']
                default_data['free-document-request-form-file_name'] += ' with default file'
        elif document_type in EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES:
            default_base_url = f'admission:{admission.admission_context}:document:free-internal-upload'
            default_data = {
                'upload-free-internal-document-form-author': user.person.global_id,
                'upload-free-internal-document-form-file_name': 'My file name',
                'upload-free-internal-document-form-file_0': ['file_0-token'],
            }
        else:
            raise NotImplementedError

        url = resolve_url(url or default_base_url, uuid=admission.uuid)

        response = self.client.post(
            url,
            data=data or default_data,
            **self.default_headers,
        )

        if response.status_code == 200:
            if document_type in EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES:
                document_uuid = AdmissionFormItem.objects.values('uuid').last()['uuid']
            else:
                admission.refresh_from_db()
                document_uuid = next(
                    reversed(getattr(admission, MODEL_FIELD_BY_FREE_MANAGER_DOCUMENT_TYPE[document_type]))
                )
            return f'{IDENTIFIANT_BASE_EMPLACEMENT_DOCUMENT_LIBRE_PAR_TYPE[document_type]}.{document_uuid}'
        return ''

    def init_documents(self, for_fac: bool = False, for_sic: bool = True, admission=None):
        if admission is None:
            admission = self.general_admission

        self.client.force_login(user=self.sic_manager_user)
        default_status = admission.status
        self.sic_free_non_requestable_internal_document = self._create_a_free_document(
            self.sic_manager_user,
            TypeEmplacementDocument.LIBRE_INTERNE_SIC.name,
            admission=admission,
        )
        self.sic_free_requestable_candidate_document_with_default_file = self._create_a_free_document(
            self.sic_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
            with_file=True,
            admission=admission,
        )
        self.sic_free_requestable_document = self._create_a_free_document(
            self.sic_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
            admission=admission,
        )

        if admission.admission_context == 'continuing-education':
            fac_manager_user = self.continuing_fac_manager_user
            admission.status = ChoixStatutPropositionContinue.CONFIRMEE.name
        else:
            fac_manager_user = self.fac_manager_user
            admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name

        self.client.force_login(user=fac_manager_user)
        admission.save(update_fields=['status'])
        admission.refresh_from_db()
        self.fac_free_non_requestable_internal_document = self._create_a_free_document(
            fac_manager_user,
            TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
            admission=admission,
        )
        self.fac_free_requestable_candidate_document_with_default_file = self._create_a_free_document(
            fac_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
            admission=admission,
            with_file=True,
        )
        self.fac_free_requestable_document = self._create_a_free_document(
            fac_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
            admission=admission,
        )

        if for_fac:
            return

        if for_sic:
            admission.status = default_status
            admission.save(update_fields=['status'])
            admission.refresh_from_db()

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
