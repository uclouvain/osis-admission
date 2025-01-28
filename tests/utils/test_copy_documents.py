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

from django.test import TestCase

from admission.admission_utils.copy_documents import copy_documents
from admission.tests.factories.curriculum import EducationalExperienceFactory, ProfessionalExperienceFactory
from base.tests.factories.person import PersonFactory


class CopyDocumentsTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_files = [uuid.uuid4() for _ in range(5)]
        self.duplicate_files = [uuid.uuid4() for _ in self.original_files]
        self.original_files_str = [str(original_file) for original_file in self.original_files]
        self.duplicate_files_str = [str(duplicate_file) for duplicate_file in self.duplicate_files]

    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.get_several_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        self.get_several_remote_metadata_patched = self.get_several_remote_metadata_patcher.start()
        self.get_several_remote_metadata_patched.return_value = {
            f'token{index}': {'name': f'test{index}.pdf', 'size': 1}
            for index, original_file_uuid in enumerate(self.original_files_str)
        }
        self.addCleanup(self.get_several_remote_metadata_patcher.stop)

        self.get_remote_tokens_patcher = mock.patch('osis_document.api.utils.get_remote_tokens')
        self.get_remote_tokens_patched = self.get_remote_tokens_patcher.start()
        self.get_remote_tokens_patched.return_value = {
            original_file_uuid: f'token{index}' for index, original_file_uuid in enumerate(self.original_files_str)
        }
        self.addCleanup(self.get_remote_tokens_patcher.stop)

        self.documents_remote_duplicate_patcher = mock.patch('osis_document.api.utils.documents_remote_duplicate')
        self.documents_remote_duplicate_patched = self.documents_remote_duplicate_patcher.start()
        self.documents_remote_duplicate_patched.return_value = {
            original_file_uuid: self.duplicate_files_str[index]
            for index, original_file_uuid in enumerate(self.original_files_str)
        }
        self.addCleanup(self.documents_remote_duplicate_patcher.stop)

    def test_copy_documents_of_one_object_with_several_documents(self):
        educational_experience = EducationalExperienceFactory(
            transcript=[self.original_files[0], self.original_files[3]],
            transcript_translation=[self.original_files[2], self.original_files[1]],
            dissertation_summary=[],
            graduate_degree=[],
            graduate_degree_translation=[],
            person=self.person,
        )

        copy_documents(objs=[educational_experience])

        self.assertCountEqual(educational_experience.transcript, [self.duplicate_files[0], self.duplicate_files[3]])
        self.assertCountEqual(
            educational_experience.transcript_translation,
            [self.duplicate_files[2], self.duplicate_files[1]],
        )
        self.assertEqual(educational_experience.dissertation_summary, [])
        self.assertEqual(educational_experience.graduate_degree, [])
        self.assertEqual(educational_experience.graduate_degree_translation, [])

        self.documents_remote_duplicate_patched.assert_called_once()
        call_args = self.documents_remote_duplicate_patched.call_args[1]
        self.assertCountEqual(
            call_args.get('uuids', []),
            self.original_files[:4],
        )
        self.assertTrue(call_args.get('with_modified_upload'))

        self.assertEqual(
            call_args.get('upload_path_by_uuid'),
            {
                self.original_files_str[0]: f'{self.person.uuid}/curriculum/test0.pdf',
                self.original_files_str[1]: f'{self.person.uuid}/curriculum/test1.pdf',
                self.original_files_str[2]: f'{self.person.uuid}/curriculum/test2.pdf',
                self.original_files_str[3]: f'{self.person.uuid}/curriculum/test3.pdf',
            },
        )

    def test_copy_documents_with_unknown_files(self):
        unknown_file = uuid.uuid4()
        unknown_file_str = str(unknown_file)
        second_unknown_file = uuid.uuid4()
        second_unknown_file_str = str(second_unknown_file)

        educational_experience = EducationalExperienceFactory(
            transcript=[None, self.original_files[0]],
            transcript_translation=[self.original_files[2], unknown_file],
            dissertation_summary=[None],
            graduate_degree=[second_unknown_file],
            graduate_degree_translation=[],
            person=self.person,
        )

        copy_documents(objs=[educational_experience])

        self.assertEqual(educational_experience.transcript, [self.duplicate_files[0]])
        self.assertEqual(educational_experience.transcript_translation, [self.duplicate_files[2]])

        self.documents_remote_duplicate_patched.assert_called_once()

        call_args = self.documents_remote_duplicate_patched.call_args[1]

        self.assertCountEqual(
            call_args.get('uuids', []),
            [self.original_files[0], self.original_files[2], unknown_file, second_unknown_file],
        )
        self.assertTrue(call_args.get('with_modified_upload'))
        self.assertEqual(
            call_args.get('upload_path_by_uuid'),
            {
                self.original_files_str[0]: f'{self.person.uuid}/curriculum/test0.pdf',
                self.original_files_str[2]: f'{self.person.uuid}/curriculum/test2.pdf',
                unknown_file_str: f'{self.person.uuid}/curriculum/file',
                second_unknown_file_str: f'{self.person.uuid}/curriculum/file',
            },
        )

    def test_copy_documents_with_file_without_token(self):
        self.get_several_remote_metadata_patched.return_value = {}

        professional_experience = ProfessionalExperienceFactory(
            person=self.person,
            certificate=[self.original_files[0]],
        )

        copy_documents(objs=[professional_experience])

        self.assertEqual(professional_experience.certificate, [self.duplicate_files[0]])

        self.documents_remote_duplicate_patched.assert_called_once_with(
            uuids=[self.original_files[0]],
            with_modified_upload=True,
            upload_path_by_uuid={
                self.original_files_str[0]: f'{self.person.uuid}/curriculum/file',
            },
        )

    def test_copy_documents_with_file_without_metadata(self):
        self.get_several_remote_metadata_patched.return_value = {}

        professional_experience = ProfessionalExperienceFactory(
            person=self.person,
            certificate=[self.original_files[0]],
        )

        copy_documents(objs=[professional_experience])

        self.assertEqual(professional_experience.certificate, [self.duplicate_files[0]])

        self.documents_remote_duplicate_patched.assert_called_once_with(
            uuids=[self.original_files[0]],
            with_modified_upload=True,
            upload_path_by_uuid={
                self.original_files_str[0]: f'{self.person.uuid}/curriculum/file',
            },
        )

    def test_copy_documents_with_file_without_metadata_name(self):
        self.get_several_remote_metadata_patched.return_value = {
            'token0': {'name': ''},
        }

        professional_experience = ProfessionalExperienceFactory(
            person=self.person,
            certificate=[self.original_files[0]],
        )

        copy_documents(objs=[professional_experience])

        self.assertEqual(professional_experience.certificate, [self.duplicate_files[0]])

        self.documents_remote_duplicate_patched.assert_called_once_with(
            uuids=[self.original_files[0]],
            with_modified_upload=True,
            upload_path_by_uuid={
                self.original_files_str[0]: f'{self.person.uuid}/curriculum/file',
            },
        )

    def test_copy_documents_of_several_objects(self):
        educational_experience = EducationalExperienceFactory(
            transcript=[self.original_files[0], self.original_files[3]],
            transcript_translation=[self.original_files[2], self.original_files[1]],
            dissertation_summary=[],
            graduate_degree=[],
            graduate_degree_translation=[],
            person=self.person,
        )
        professional_experience = ProfessionalExperienceFactory(
            person=self.person,
            certificate=[self.original_files[4]],
        )

        copy_documents(objs=[educational_experience, professional_experience])

        self.assertCountEqual(educational_experience.transcript, [self.duplicate_files[0], self.duplicate_files[3]])
        self.assertCountEqual(
            educational_experience.transcript_translation,
            [self.duplicate_files[2], self.duplicate_files[1]],
        )
        self.assertEqual(educational_experience.dissertation_summary, [])
        self.assertEqual(educational_experience.graduate_degree, [])
        self.assertEqual(educational_experience.graduate_degree_translation, [])

        self.assertCountEqual(professional_experience.certificate, [self.duplicate_files[4]])
