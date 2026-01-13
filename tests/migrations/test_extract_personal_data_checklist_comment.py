# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial

import freezegun
from django.test import TestCase
from osis_comment.models import CommentEntry

from admission.migrations.utils.extract_personal_data_checklist_comment import (
    extract_personal_data_checklist_comment as extract_personal_data_checklist_comment_method,
)
from admission.models import GeneralEducationAdmission
from admission.models.base import BaseAdmission
from admission.tests.factories.comment import CommentEntryFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory

extract_personal_data_checklist_comment = partial(
    extract_personal_data_checklist_comment_method,
    comment_model=CommentEntry,
    base_admission_model=BaseAdmission,
)


class ExtractPersonalDataChecklistCommentTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory()
        cls.second_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=cls.first_admission.candidate
        )
        cls.other_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory()
        cls.default_datetime = datetime.datetime(2020, 2, 1, 11, 30)
        cls.tags = ['donnees_personnelles']

    def test_with_assimilation_comment_linked_to_known_admission(self):
        with freezegun.freeze_time(self.default_datetime):
            created_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.first_admission.uuid,
                tags=['assimilation'],
                content='The comment',
            )
        extract_personal_data_checklist_comment()

        comments_related_to_candidate = CommentEntry.objects.filter(object_uuid=self.first_admission.candidate.uuid)
        comments_related_to_admission = CommentEntry.objects.filter(object_uuid=self.first_admission.uuid)

        self.assertEqual(len(comments_related_to_candidate), 0)
        self.assertEqual(len(comments_related_to_admission), 1)

        self.assertEqual(comments_related_to_admission[0].uuid, created_comment.uuid)

    def test_with_personal_data_comment_linked_to_unknown_admission(self):
        default_uuid = uuid.uuid4()
        with freezegun.freeze_time(self.default_datetime):
            created_comment: CommentEntry = CommentEntryFactory(
                object_uuid=default_uuid,
                tags=self.tags,
                content='The comment',
            )
        extract_personal_data_checklist_comment()

        comments_related_to_unknown_uuid = CommentEntry.objects.filter(object_uuid=default_uuid)

        self.assertEqual(len(comments_related_to_unknown_uuid), 1)

        self.assertEqual(comments_related_to_unknown_uuid[0].uuid, created_comment.uuid)

    def test_with_personal_data_comment_linked_to_known_admission(self):
        with freezegun.freeze_time(self.default_datetime):
            created_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.first_admission.uuid,
                tags=self.tags,
                content='The comment',
            )
        extract_personal_data_checklist_comment()

        comments_related_to_candidate = CommentEntry.objects.filter(object_uuid=self.first_admission.candidate.uuid)
        comments_related_to_admission = CommentEntry.objects.filter(object_uuid=self.first_admission.uuid)

        self.assertEqual(len(comments_related_to_candidate), 1)
        self.assertEqual(len(comments_related_to_admission), 0)

        self.assertEqual(comments_related_to_candidate[0].uuid, created_comment.uuid)
        self.assertEqual(comments_related_to_candidate[0].modified_at, self.default_datetime)
        self.assertEqual(comments_related_to_candidate[0].content, 'The comment')
        self.assertEqual(comments_related_to_candidate[0].object_uuid, self.first_admission.candidate.uuid)

    def test_with_several_personal_data_comments_linked_to_known_admissions(self):
        with freezegun.freeze_time(self.default_datetime):
            first_admission_personal_data_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.first_admission.uuid,
                tags=self.tags,
                content='The comment 1',
                author__first_name='John',
                author__last_name='Doe',
            )
            other_admission_personal_data_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.other_admission.uuid,
                tags=self.tags,
                content='The comment 3',
            )
        with freezegun.freeze_time(self.default_datetime + datetime.timedelta(days=1)):
            second_admission_personal_data_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.second_admission.uuid,
                tags=self.tags,
                content='The comment 2',
                author__first_name='Jane',
                author__last_name='Poe',
            )

        extract_personal_data_checklist_comment()

        # Several admissions are linked to the same candidate -> the comments are merged
        comments_related_to_first_candidate = CommentEntry.objects.filter(
            object_uuid=self.first_admission.candidate.uuid
        )
        comments_related_to_first_admission = CommentEntry.objects.filter(object_uuid=self.first_admission.uuid)
        comments_related_to_second_admission = CommentEntry.objects.filter(object_uuid=self.first_admission.uuid)

        self.assertEqual(len(comments_related_to_first_candidate), 1)
        self.assertEqual(len(comments_related_to_first_admission), 0)
        self.assertEqual(len(comments_related_to_second_admission), 0)

        self.assertFalse(CommentEntry.objects.filter(uuid=first_admission_personal_data_comment.uuid).exists())
        self.assertFalse(CommentEntry.objects.filter(uuid=second_admission_personal_data_comment.uuid).exists())

        self.assertEqual(comments_related_to_first_candidate[0].author, None)
        self.assertEqual(comments_related_to_first_candidate[0].tags, self.tags)
        self.assertEqual(
            comments_related_to_first_candidate[0].content,
            'Jane Poe (11:30 - 02/02/2020) : The comment 2\nJohn Doe (11:30 - 01/02/2020) : The comment 1\n',
        )

        comments_related_to_other_candidate = CommentEntry.objects.filter(
            object_uuid=self.other_admission.candidate.uuid
        )
        comments_related_to_other_admission = CommentEntry.objects.filter(object_uuid=self.other_admission.uuid)

        self.assertEqual(len(comments_related_to_other_candidate), 1)
        self.assertEqual(len(comments_related_to_other_admission), 0)

        self.assertEqual(comments_related_to_other_candidate[0].uuid, other_admission_personal_data_comment.uuid)
        self.assertEqual(comments_related_to_other_candidate[0].modified_at, self.default_datetime)
        self.assertEqual(comments_related_to_other_candidate[0].content, 'The comment 3')
