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
import datetime
import uuid
from unittest import mock
from unittest.mock import patch, call

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from admission.constants import PDF_MIME_TYPE, SUPPORTED_MIME_TYPES, PNG_MIME_TYPE
from admission.ddd.admission.domain.validator.exceptions import DocumentsCompletesDifferentsDesReclamesException
from admission.ddd.admission.enums import (
    CleConfigurationItemFormulaire,
    Onglets,
    CritereItemFormulaireFormation,
    TypeItemFormulaire,
)
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    OngletsDemande,
    IdentifiantBaseEmplacementDocument,
    StatutEmplacementDocument,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.tests.factories.form_item import DocumentAdmissionFormItemFactory, AdmissionFormItemInstantiationFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.person import CompletePersonFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import Master120TrainingFactory
from base.tests.factories.person import PersonFactory
from osis_document.enums import PostProcessingType


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class GeneralAdmissionRequestedDocumentListApiTestCase(APITestCase):
    PDF_MERGE_UUID = uuid.uuid4()
    PDF_CONVERT_UUID = uuid.uuid4()

    @classmethod
    def setUpTestData(cls):
        cls.manuel_required_params = {
            'automatically_required': False,
            'last_action_at': '2023-01-01T00:00:00',
            'last_actor': '0123456',
            'deadline_at': '2023-01-16',
            'reason': 'Ma raison',
            'requested_at': '2023-01-01T00:00:00',
            'status': 'RECLAME',
            'type': 'NON_LIBRE',
        }
        cls.file_metadata = {
            'name': 'myfile.myext',
            'mimetype': PDF_MIME_TYPE,
            'explicit_name': 'Mon nom de fichier',
            'upload_uuid': uuid.uuid4(),
        }

        cls.uuid_documents_by_token = {
            'curriculum_file_token': uuid.uuid4(),
            'non_free_specific_question_file_token': uuid.uuid4(),
            'free_file_token': uuid.uuid4(),
        }
        AcademicYearFactory(year=2019)

    @classmethod
    def _simulate_post_processing(cls, **kwargs):
        post_processing_types = kwargs.get('post_processing_types', [])
        output = {
            PostProcessingType.MERGE.name: {
                'input': [],
                'output': []
                if PostProcessingType.MERGE.name not in post_processing_types
                else {
                    'upload_objects': [str(cls.PDF_MERGE_UUID)],
                    'post_processing_objects': [str(uuid.uuid4())],
                },
            },
            PostProcessingType.CONVERT.name: {
                'input': [],
                'output': []
                if PostProcessingType.CONVERT.name not in post_processing_types
                else {
                    'upload_objects': [str(cls.PDF_CONVERT_UUID)],
                    'post_processing_objects': [str(uuid.uuid4())],
                },
            },
        }
        return output

    def setUp(self) -> None:
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="a-token")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile.myext", "mimetype": "application/pdf"},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, upload_to: self.uuid_documents_by_token[token],
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {
            document_uuid: f'token-{index}' for index, document_uuid in enumerate(uuids)
        }
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.get_several_remote_metadata')
        self.get_several_remote_metadata_patched = patcher.start()
        self.get_several_remote_metadata_patched.side_effect = lambda tokens: {
            token: self.file_metadata for token in tokens
        }
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.utils.save_raw_content_remotely')
        patched = patcher.start()
        patched.return_value = 'a-token'
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.change_remote_metadata')
        self.change_remote_metadata_patcher = patcher.start()
        self.change_remote_metadata_patcher.return_value = 'a-token'
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.launch_post_processing')
        self.launch_post_processing_patcher = patcher.start()
        self.launch_post_processing_patcher.side_effect = self._simulate_post_processing
        self.addCleanup(patcher.stop)

        self.admission = GeneralEducationAdmissionFactory(
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
            ),
            training=Master120TrainingFactory(),
            status=ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
        )

        self.free_document = AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(),
            admission=self.admission,
            academic_year=self.admission.determined_academic_year or self.admission.training.academic_year,
            tab=Onglets.DOCUMENTS.name,
            display_according_education=CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name,
        )

        self.non_free_document = AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                configuration={
                    CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name: [PDF_MIME_TYPE],
                    CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name: 4,
                }
            ),
            academic_year=self.admission.determined_academic_year or self.admission.training.academic_year,
            tab=Onglets.CHOIX_FORMATION.name,
        )

        self.admission.requested_documents = {
            'CURRICULUM.CURRICULUM': self.manuel_required_params,
            f'CHOIX_FORMATION.QUESTION_SPECIFIQUE.{self.non_free_document.form_item.uuid}': self.manuel_required_params,
            f'LIBRE_CANDIDAT.{self.free_document.form_item.uuid}': {
                **self.manuel_required_params,
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
            },
        }

        self.admission.save(update_fields=['requested_documents'])

        self.url = resolve_url('admission_api_v1:general_documents', uuid=self.admission.uuid)

    def test_retrieve_requested_documents(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()

        self.assertEqual(len(response_data), 3)

        # Simulate configurations of specific questions

        # Of a non free document based on a specific question
        self.assertEqual(
            response_data[0]['uuid'],
            f'CHOIX_FORMATION.QUESTION_SPECIFIQUE.{self.non_free_document.form_item.uuid}',
        )
        self.assertEqual(response_data[0]['type'], TypeItemFormulaire.DOCUMENT.name)
        self.assertEqual(
            response_data[0]['title'][settings.LANGUAGE_CODE_FR],
            'Champ document',
        )
        self.assertEqual(response_data[0]['text'][settings.LANGUAGE_CODE_FR], 'Ma raison')
        self.assertEqual(response_data[0]['help_text'], {})
        self.assertEqual(
            response_data[0]['configuration'][CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name],
            [PDF_MIME_TYPE],
        )
        self.assertEqual(response_data[0]['configuration'][CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name], 4)
        self.assertEqual(response_data[0]['values'], [])
        self.assertEqual(response_data[0]['tab'], OngletsDemande.CHOIX_FORMATION.name)
        self.assertEqual(response_data[0]['tab_name'], OngletsDemande.CHOIX_FORMATION.value)
        self.assertEqual(response_data[0]['required'], True)

        # Of a non free document based on a model field
        self.assertEqual(response_data[1]['uuid'], 'CURRICULUM.CURRICULUM')
        self.assertEqual(response_data[1]['type'], TypeItemFormulaire.DOCUMENT.name)
        self.assertEqual(
            response_data[1]['title'][settings.LANGUAGE_CODE_FR],
            'Curriculum vitae détaillé, daté et signé',
        )
        self.assertEqual(response_data[1]['text'][settings.LANGUAGE_CODE_FR], 'Ma raison')
        self.assertEqual(response_data[1]['help_text'], {})
        self.assertCountEqual(
            response_data[1]['configuration'][CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name],
            list(SUPPORTED_MIME_TYPES),
        )
        self.assertEqual(response_data[1]['values'], [])
        self.assertEqual(response_data[1]['tab'], OngletsDemande.CURRICULUM.name)
        self.assertEqual(response_data[1]['tab_name'], OngletsDemande.CURRICULUM.value)
        self.assertEqual(response_data[1]['required'], True)
        self.assertEqual(response_data[1]['configuration'][CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name], 1)

        # Of a free document
        self.assertEqual(response_data[2]['uuid'], f'LIBRE_CANDIDAT.{self.free_document.form_item.uuid}')
        self.assertEqual(response_data[2]['type'], TypeItemFormulaire.DOCUMENT.name)
        self.assertEqual(
            response_data[2]['title'][settings.LANGUAGE_CODE_FR],
            'Champ document',
        )
        self.assertEqual(response_data[2]['text'][settings.LANGUAGE_CODE_FR], 'Ma raison')
        self.assertEqual(response_data[2]['help_text'], {})
        self.assertCountEqual(
            response_data[2]['configuration'][CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name],
            list(SUPPORTED_MIME_TYPES),
        )
        self.assertIsNone(response_data[2]['configuration'][CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name])
        self.assertEqual(response_data[2]['values'], [])
        self.assertEqual(response_data[2]['tab'], IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name)
        self.assertEqual(response_data[2]['tab_name'], IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.value)
        self.assertEqual(response_data[2]['required'], True)

    def test_retrieve_requested_documents_with_not_candidate_user_is_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=PersonFactory().user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @freezegun.freeze_time('2020-01-02')
    def test_post_requested_documents(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        curriculum_file = ['curriculum_file_token']
        non_free_specific_question_file = ['non_free_specific_question_file_token']
        several_non_free_specific_question_files = [
            'non_free_specific_question_file_token-1',
            'non_free_specific_question_file_token-2',
        ]
        free_file = ['free_file_token']

        json_error = {
            'non_field_errors': [
                {
                    'status_code': DocumentsCompletesDifferentsDesReclamesException.status_code,
                    'detail': 'Les documents complétés sont différents de ceux qui sont réclamés.',
                }
            ]
        }

        # No submitted files
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # No all requested files are specified
        response = self.client.post(
            self.url,
            {
                'reponses_documents_a_completer': {
                    'CURRICULUM.CURRICULUM': [],
                    f'CHOIX_FORMATION.QUESTION_SPECIFIQUE.{self.non_free_document.form_item.uuid}': (
                        non_free_specific_question_file
                    ),
                    f'LIBRE_CANDIDAT.{self.free_document.form_item.uuid}': free_file,
                },
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json(), json_error)

        # All requested files are specified but some are empty
        response = self.client.post(
            self.url,
            {
                'reponses_documents_a_completer': {
                    'CURRICULUM.CURRICULUM': [],
                    f'CHOIX_FORMATION.QUESTION_SPECIFIQUE.{self.non_free_document.form_item.uuid}': (
                        non_free_specific_question_file
                    ),
                    f'LIBRE_CANDIDAT.{self.free_document.form_item.uuid}': free_file,
                },
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json(), json_error)

        # > Some files must be converted
        with mock.patch('osis_document.api.utils.get_several_remote_metadata') as get_several_remote_metadata_patcher:
            get_several_remote_metadata_patcher.side_effect = lambda tokens: {
                token: {
                    **self.file_metadata,
                    'mimetype': PNG_MIME_TYPE,
                    'upload_uuid': f'{token}-uuid',
                }
                for token in tokens
            }
            self.launch_post_processing_patcher.reset_mock()

            response = self.client.post(
                self.url,
                {
                    'reponses_documents_a_completer': {
                        'CURRICULUM.CURRICULUM': [],
                        f'CHOIX_FORMATION.QUESTION_SPECIFIQUE.{self.non_free_document.form_item.uuid}': (
                            non_free_specific_question_file
                        ),
                        f'LIBRE_CANDIDAT.{self.free_document.form_item.uuid}': [],
                    },
                },
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            self.launch_post_processing_patcher.assert_called_once_with(
                uuid_list=['non_free_specific_question_file_token-uuid'],
                post_processing_types=[PostProcessingType.CONVERT.name],
                post_process_params={
                    PostProcessingType.MERGE.name: {},
                    PostProcessingType.CONVERT.name: {
                        'output_filename': 'myfile.pdf',
                    },
                },
                async_post_processing=False,
            )

            self.launch_post_processing_patcher.reset_mock()

            # > Some files must be converted and then be merged
            response = self.client.post(
                self.url,
                {
                    'reponses_documents_a_completer': {
                        'CURRICULUM.CURRICULUM': [],
                        f'CHOIX_FORMATION.QUESTION_SPECIFIQUE.{self.non_free_document.form_item.uuid}': several_non_free_specific_question_files,
                        f'LIBRE_CANDIDAT.{self.free_document.form_item.uuid}': [],
                    },
                },
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            self.launch_post_processing_patcher.assert_called_once_with(
                uuid_list=[
                    'non_free_specific_question_file_token-1-uuid',
                    'non_free_specific_question_file_token-2-uuid',
                ],
                post_processing_types=[PostProcessingType.CONVERT.name, PostProcessingType.MERGE.name],
                post_process_params={
                    PostProcessingType.MERGE.name: {
                        'output_filename': 'champ-document.pdf',
                    },
                    PostProcessingType.CONVERT.name: {},
                },
                async_post_processing=False,
            )

        with mock.patch('osis_document.api.utils.get_several_remote_metadata') as get_several_remote_metadata_patcher:
            get_several_remote_metadata_patcher.side_effect = lambda tokens: {
                token: {
                    **self.file_metadata,
                    'upload_uuid': f'{token}-uuid',
                }
                for token in tokens
            }

            self.launch_post_processing_patcher.reset_mock()

            # Some files must be merged
            response = self.client.post(
                self.url,
                {
                    'reponses_documents_a_completer': {
                        'CURRICULUM.CURRICULUM': [],
                        f'CHOIX_FORMATION.QUESTION_SPECIFIQUE.{self.non_free_document.form_item.uuid}': several_non_free_specific_question_files,
                        f'LIBRE_CANDIDAT.{self.free_document.form_item.uuid}': [],
                    },
                },
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            self.launch_post_processing_patcher.assert_called_once_with(
                uuid_list=[
                    'non_free_specific_question_file_token-1-uuid',
                    'non_free_specific_question_file_token-2-uuid',
                ],
                post_processing_types=[PostProcessingType.MERGE.name],
                post_process_params={
                    PostProcessingType.MERGE.name: {
                        'output_filename': 'champ-document.pdf',
                    },
                    PostProcessingType.CONVERT.name: {},
                },
                async_post_processing=False,
            )

        response = self.client.post(
            self.url,
            {
                'reponses_documents_a_completer': {
                    'CURRICULUM.CURRICULUM': curriculum_file,
                    f'CHOIX_FORMATION.QUESTION_SPECIFIQUE.{self.non_free_document.form_item.uuid}': (
                        non_free_specific_question_file
                    ),
                    f'LIBRE_CANDIDAT.{self.free_document.form_item.uuid}': free_file,
                },
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['uuid'], str(self.admission.uuid))

        # Check admission status and last modification data
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.admission.last_update_author, self.admission.candidate)

        # Check updates of the documents
        self.assertEqual(
            self.admission.requested_documents['CURRICULUM.CURRICULUM'],
            {
                **self.manuel_required_params,
                'status': StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION.name,
            },
        )

        self.assertEqual(
            self.admission.requested_documents[
                f'CHOIX_FORMATION.QUESTION_SPECIFIQUE.{self.non_free_document.form_item.uuid}'
            ],
            {
                **self.manuel_required_params,
                'status': StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION.name,
            },
        )

        self.assertEqual(
            self.admission.requested_documents[f'LIBRE_CANDIDAT.{self.free_document.form_item.uuid}'],
            {
                **self.manuel_required_params,
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                'status': StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION.name,
            },
        )

        # Check the metadata of the submitted files
        self.change_remote_metadata_patcher.assert_has_calls(
            [
                call(
                    token=curriculum_file[0],
                    metadata={'author': self.admission.candidate.global_id},
                ),
                call(
                    token=non_free_specific_question_file[0],
                    metadata={'author': self.admission.candidate.global_id},
                ),
                call(
                    token=free_file[0],
                    metadata={'author': self.admission.candidate.global_id},
                ),
            ],
            any_order=True,
        )

        # Check the updates of the files
        self.assertEqual(self.admission.curriculum, [self.uuid_documents_by_token[curriculum_file[0]]])
        self.assertEqual(
            self.admission.specific_question_answers,
            {
                str(self.non_free_document.form_item.uuid): [
                    str(self.uuid_documents_by_token[non_free_specific_question_file[0]]),
                ],
                str(self.free_document.form_item.uuid): [str(self.uuid_documents_by_token[free_file[0]])],
            },
        )
