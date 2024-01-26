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
from unittest.mock import patch

from django.conf import settings
from django.test import override_settings
from osis_async.models import AsyncTask
from rest_framework.test import APITestCase

from admission.constants import PDF_MIME_TYPE, PNG_MIME_TYPE
from admission.contrib.models import AdmissionTask
from admission.ddd.admission.enums import (
    CleConfigurationItemFormulaire,
    Onglets,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.exceptions import InvalidMimeTypeException, DocumentPostProcessingException
from admission.tasks.merge_admission_documents import general_education_admission_document_merging_from_task
from admission.tests.factories.curriculum import (
    EducationalExperienceYearFactory,
    EducationalExperienceFactory,
    ProfessionalExperienceFactory,
    AdmissionEducationalValuatedExperiencesFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
)
from admission.tests.factories.form_item import DocumentAdmissionFormItemFactory, AdmissionFormItemInstantiationFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.person import CompletePersonFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import Master120TrainingFactory
from osis_document.enums import PostProcessingType
from osis_profile.models.enums.curriculum import TranscriptType


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class MergeAdmissionDocumentsTestCase(APITestCase):
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
        cls.pdf_file_metadata = {
            'name': 'myfile.myext',
            'mimetype': PDF_MIME_TYPE,
            'explicit_name': 'Mon nom de fichier',
            'upload_uuid': uuid.uuid4(),
        }
        cls.image_metadata = {
            **cls.pdf_file_metadata,
            'mimetype': PNG_MIME_TYPE,
        }

        cls.uuid_documents_by_token = {
            'curriculum_file_token': uuid.uuid4(),
            'non_free_specific_question_file_token': uuid.uuid4(),
            'free_file_token': uuid.uuid4(),
            'token-passport': uuid.uuid4(),
            'token-passport-2': uuid.uuid4(),
            'token-id-photo': uuid.uuid4(),
            'pdf_recap_file_token': uuid.uuid4(),
            'certificate': uuid.uuid4(),
            'certificate-2': uuid.uuid4(),
            'transcript': uuid.uuid4(),
            'transcript-2': uuid.uuid4(),
        }

        cls.tokens_by_uuid = {str(document_uuid): token for token, document_uuid in cls.uuid_documents_by_token.items()}
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
        self.metadata_by_token = {token: self.pdf_file_metadata.copy() for token in self.uuid_documents_by_token}

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

        patcher = patch("osis_document.api.utils.declare_remote_files_as_deleted")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_several_remote_metadata",
            side_effect=lambda tokens: {
                token: {"name": "myfile.myext", "mimetype": "application/pdf"} for token in tokens
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: self.uuid_documents_by_token[token],
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.patcher = patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = self.patcher.start()
        patched.side_effect = lambda _, att_values, __: [
            self.uuid_documents_by_token.get(value, value) for value in att_values
        ]
        self.addCleanup(self.patcher.stop)

        patcher = patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {
            document_uuid: self.tokens_by_uuid.get(document_uuid, f'token-{index}')
            for index, document_uuid in enumerate(uuids)
        }
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.get_several_remote_metadata')
        self.get_several_remote_metadata_patched = patcher.start()
        self.get_several_remote_metadata_patched.side_effect = lambda tokens: {
            token: self.metadata_by_token.get(token, self.pdf_file_metadata) for token in tokens
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
                id_photo=[self.uuid_documents_by_token['token-id-photo']],
                passport=[self.uuid_documents_by_token['token-passport']],
            ),
            training=Master120TrainingFactory(),
            status=ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
            curriculum=[self.uuid_documents_by_token['curriculum_file_token']],
            pdf_recap=[self.uuid_documents_by_token['pdf_recap_file_token']],
        )

        self.admission_task = AdmissionTask.objects.create(
            admission=self.admission,
            task=AsyncTask.objects.create(),
            type=AdmissionTask.TaskType.GENERAL_MERGE,
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

    def test_when_no_document_must_be_processed(self):
        # The documents are not processed because they only contain one PDF file except...

        # the id photo which is explicitly defined as a document that must not be processed
        self.metadata_by_token['token-id-photo']['mimetype'] = PNG_MIME_TYPE

        # the recap which is not processed as a system document
        self.metadata_by_token['pdf_recap_file_token']['mimetype'] = PNG_MIME_TYPE

        general_education_admission_document_merging_from_task(
            task_uuid=self.admission_task.task.uuid,
        )

        self.launch_post_processing_patcher.assert_not_called()

    def test_when_an_image_file_must_be_converted(self):
        self.metadata_by_token['token-passport']['mimetype'] = PNG_MIME_TYPE
        self.metadata_by_token['token-passport']['name'] = 'file.1.png'

        general_education_admission_document_merging_from_task(
            task_uuid=self.admission_task.task.uuid,
        )

        self.launch_post_processing_patcher.assert_called_once_with(
            uuid_list=[str(self.uuid_documents_by_token['token-passport'])],
            post_processing_types=[PostProcessingType.CONVERT.name],
            post_process_params={
                PostProcessingType.MERGE.name: {},
                PostProcessingType.CONVERT.name: {
                    'output_filename': 'file.1.pdf',
                },
            },
            async_post_processing=False,
        )

        self.admission.candidate.refresh_from_db()
        self.assertEqual(self.admission.candidate.passport, [self.PDF_CONVERT_UUID])

    def test_when_an_error_occurs_while_converting(self):
        self.admission.candidate.passport = [self.uuid_documents_by_token['token-passport']]
        self.admission.candidate.save()
        self.metadata_by_token['token-passport']['mimetype'] = PNG_MIME_TYPE

        with self.assertRaises(DocumentPostProcessingException):
            self.launch_post_processing_patcher.side_effect = lambda **kwargs: {
                'error': 'An error occurred',
            }
            general_education_admission_document_merging_from_task(
                task_uuid=self.admission_task.task.uuid,
            )

            self.launch_post_processing_patcher.assert_called_once_with(
                uuid_list=[str(self.uuid_documents_by_token['token-passport'])],
                post_processing_types=[PostProcessingType.CONVERT.name],
                post_process_params={
                    PostProcessingType.MERGE.name: {},
                    PostProcessingType.CONVERT.name: {
                        'output_filename': 'file.1.pdf',
                    },
                },
                async_post_processing=False,
            )

            self.admission.candidate.refresh_from_db()
            self.assertEqual(self.admission.candidate.passport, [self.uuid_documents_by_token['token-passport']])

    def test_when_several_pdf_files_must_be_merged(self):
        uuids = [
            self.uuid_documents_by_token['token-passport'],
            self.uuid_documents_by_token['token-passport-2'],
        ]
        self.admission.candidate.passport = uuids
        self.admission.candidate.save(update_fields=['passport'])

        general_education_admission_document_merging_from_task(
            task_uuid=self.admission_task.task.uuid,
        )

        self.launch_post_processing_patcher.assert_called_once_with(
            uuid_list=[str(doc_uuid) for doc_uuid in uuids],
            post_processing_types=[PostProcessingType.MERGE.name],
            post_process_params={
                PostProcessingType.MERGE.name: {
                    'output_filename': 'passeport.pdf',
                },
                PostProcessingType.CONVERT.name: {},
            },
            async_post_processing=False,
        )

        self.admission.candidate.refresh_from_db()
        self.assertEqual(self.admission.candidate.passport, [self.PDF_MERGE_UUID])

    def test_when_several_pdf_and_image_files_must_be_merged(self):
        uuids = [
            self.uuid_documents_by_token['token-passport'],
            self.uuid_documents_by_token['token-passport-2'],
        ]
        self.admission.candidate.passport = uuids
        self.admission.candidate.save(update_fields=['passport'])

        self.metadata_by_token['token-passport']['mimetype'] = PNG_MIME_TYPE

        general_education_admission_document_merging_from_task(
            task_uuid=self.admission_task.task.uuid,
        )

        self.launch_post_processing_patcher.assert_called_once_with(
            uuid_list=[str(doc_uuid) for doc_uuid in uuids],
            post_processing_types=[PostProcessingType.CONVERT.name, PostProcessingType.MERGE.name],
            post_process_params={
                PostProcessingType.MERGE.name: {
                    'output_filename': 'passeport.pdf',
                },
                PostProcessingType.CONVERT.name: {},
            },
            async_post_processing=False,
        )

        self.admission.candidate.refresh_from_db()
        self.assertEqual(self.admission.candidate.passport, [self.PDF_MERGE_UUID])

    def test_when_an_image_file_must_be_converted_for_a_specific_question(self):
        uuids = [
            self.uuid_documents_by_token['non_free_specific_question_file_token'],
        ]
        self.admission.specific_question_answers = {
            str(self.non_free_document.form_item.uuid): uuids,
        }
        self.admission.save()
        self.metadata_by_token['non_free_specific_question_file_token']['mimetype'] = PNG_MIME_TYPE

        general_education_admission_document_merging_from_task(
            task_uuid=self.admission_task.task.uuid,
        )

        self.launch_post_processing_patcher.assert_called_once_with(
            uuid_list=[str(doc_uuid) for doc_uuid in uuids],
            post_processing_types=[PostProcessingType.CONVERT.name],
            post_process_params={
                PostProcessingType.MERGE.name: {},
                PostProcessingType.CONVERT.name: {
                    'output_filename': 'myfile.pdf',
                },
            },
            async_post_processing=False,
        )

        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.specific_question_answers,
            {
                str(self.non_free_document.form_item.uuid): [str(self.PDF_CONVERT_UUID)],
            },
        )

    def test_when_an_image_file_cannot_be_converted_because_pdf_are_not_allowed_for_the_field(self):
        uuids = [
            self.uuid_documents_by_token['non_free_specific_question_file_token'],
        ]
        self.admission.specific_question_answers = {
            str(self.non_free_document.form_item.uuid): uuids,
        }
        self.admission.save()

        # The conversion is not possible because only images are allowed for the specific question
        self.non_free_document.form_item.configuration[CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name] = [
            PNG_MIME_TYPE
        ]
        self.non_free_document.form_item.save()

        self.metadata_by_token['non_free_specific_question_file_token']['mimetype'] = PNG_MIME_TYPE

        with self.assertRaises(InvalidMimeTypeException):
            general_education_admission_document_merging_from_task(
                task_uuid=self.admission_task.task.uuid,
            )

            self.launch_post_processing_patcher.assert_called_once_with(
                uuid_list=[str(doc_uuid) for doc_uuid in uuids],
                post_processing_types=[PostProcessingType.CONVERT.name],
                post_process_params={
                    PostProcessingType.MERGE.name: {},
                    PostProcessingType.CONVERT.name: {
                        'output_filename': 'myfile.pdf',
                    },
                },
                async_post_processing=False,
            )

            self.admission.refresh_from_db()
            self.assertEqual(self.admission.specific_question_answers, {})

    def test_only_cv_experiences_valuated_by_admission_must_be_processed(self):
        other_admission = GeneralEducationAdmissionFactory(
            candidate=self.admission.candidate,
            status=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
        )
        educational_experience = EducationalExperienceFactory(
            person=self.admission.candidate,
            transcript_type=TranscriptType.ONE_A_YEAR.name,
        )
        educational_experience_year = EducationalExperienceYearFactory(
            educational_experience=educational_experience,
            academic_year=self.admission.training.academic_year,
            transcript=[
                self.uuid_documents_by_token['transcript'],
                self.uuid_documents_by_token['transcript-2'],
            ],
        )
        non_educational_experience = ProfessionalExperienceFactory(
            person=self.admission.candidate,
            certificate=[
                self.uuid_documents_by_token['certificate'],
                self.uuid_documents_by_token['certificate-2'],
            ],
        )

        # No valuated experience -> no merge
        general_education_admission_document_merging_from_task(task_uuid=self.admission_task.task.uuid)

        educational_experience_year.refresh_from_db()
        self.assertNotEqual(educational_experience_year.transcript, [self.PDF_MERGE_UUID])

        non_educational_experience.refresh_from_db()
        self.assertNotEqual(non_educational_experience.certificate, [self.PDF_MERGE_UUID])

        # Valuated by another admission -> no merge
        educational_valuation = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=other_admission,
            educationalexperience=educational_experience,
        )

        non_educational_valuation = AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=other_admission,
            professionalexperience=non_educational_experience,
        )

        general_education_admission_document_merging_from_task(task_uuid=self.admission_task.task.uuid)

        educational_experience_year.refresh_from_db()
        self.assertNotEqual(educational_experience_year.transcript, [self.PDF_MERGE_UUID])

        non_educational_experience.refresh_from_db()
        self.assertNotEqual(non_educational_experience.certificate, [self.PDF_MERGE_UUID])

        # Valuated by the current admission -> merge
        self.admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.admission.save()

        educational_valuation.baseadmission = self.admission
        educational_valuation.save()

        non_educational_valuation.baseadmission = self.admission
        non_educational_valuation.save()

        general_education_admission_document_merging_from_task(task_uuid=self.admission_task.task.uuid)

        educational_experience_year.refresh_from_db()
        self.assertEqual(educational_experience_year.transcript, [self.PDF_MERGE_UUID])

        non_educational_experience.refresh_from_db()
        self.assertEqual(non_educational_experience.certificate, [self.PDF_MERGE_UUID])
