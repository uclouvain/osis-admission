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

import freezegun
from django.test import TestCase
from osis_comment.models import CommentEntry

from admission.migrations.utils.extract_experience_checklist_comment import extract_experience_checklist_comment
from admission.models import GeneralEducationAdmission
from admission.models.base import BaseAdmission
from admission.models.exam import AdmissionExam
from admission.tests.factories.comment import CommentEntryFactory
from admission.tests.factories.curriculum import EducationalExperienceFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from osis_profile.tests.factories.exam import ExamFactory
from osis_profile.tests.factories.high_school_diploma import HighSchoolDiplomaFactory


class ExtractExperienceChecklistCommentTestCase(TestCase):
    def extract_experience_checklist_comment(self):
        return extract_experience_checklist_comment(
            comment_model=CommentEntry,
            base_admission_model=BaseAdmission,
        )

    @classmethod
    def setUpTestData(cls):
        cls.first_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory()
        cls.second_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=cls.first_admission.candidate
        )
        cls.other_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory()
        cls.default_datetime = datetime.datetime(2020, 2, 1, 11, 30)

    def test_with_educational_experience_comment(self):
        experience = EducationalExperienceFactory(person=self.first_admission.candidate)
        experience_uuid_str = str(experience.uuid)

        with freezegun.freeze_time(self.default_datetime):
            general_experience_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.first_admission.uuid,
                tags=['parcours_anterieur', experience_uuid_str],
                content='The comment',
            )
            authentication_experience_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.first_admission.uuid,
                tags=['parcours_anterieur', experience_uuid_str, 'authentication'],
                content='The authentication comment',
            )

        self.extract_experience_checklist_comment()

        comments_related_to_experience = CommentEntry.objects.filter(object_uuid=experience.uuid)
        comments_related_to_admission = CommentEntry.objects.filter(object_uuid=self.first_admission.uuid)

        self.assertEqual(comments_related_to_experience.count(), 2)
        self.assertEqual(comments_related_to_admission.count(), 0)

        general_experience_comment.refresh_from_db()
        authentication_experience_comment.refresh_from_db()

        self.assertEqual(general_experience_comment.object_uuid, experience.uuid)
        self.assertEqual(general_experience_comment.tags, ['parcours_anterieur', experience_uuid_str])
        self.assertEqual(general_experience_comment.content, 'The comment')

        self.assertEqual(authentication_experience_comment.object_uuid, experience.uuid)
        self.assertEqual(
            authentication_experience_comment.tags, ['parcours_anterieur', experience_uuid_str, 'authentication']
        )
        self.assertEqual(authentication_experience_comment.content, 'The authentication comment')

    def test_with_secondary_studies_comment(self):
        high_school_diploma = HighSchoolDiplomaFactory(person=self.first_admission.candidate)

        experience_uuid_str = str(high_school_diploma.uuid)

        with freezegun.freeze_time(self.default_datetime):
            general_experience_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.first_admission.uuid,
                tags=['parcours_anterieur', 'ETUDES_SECONDAIRES'],
                content='The comment',
            )
            authentication_experience_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.first_admission.uuid,
                tags=['parcours_anterieur', 'ETUDES_SECONDAIRES', 'authentication'],
                content='The authentication comment',
            )

        self.extract_experience_checklist_comment()

        comments_related_to_experience = CommentEntry.objects.filter(object_uuid=high_school_diploma.uuid)
        comments_related_to_admission = CommentEntry.objects.filter(object_uuid=self.first_admission.uuid)

        self.assertEqual(comments_related_to_experience.count(), 2)
        self.assertEqual(comments_related_to_admission.count(), 0)

        general_experience_comment.refresh_from_db()
        authentication_experience_comment.refresh_from_db()

        self.assertEqual(general_experience_comment.object_uuid, high_school_diploma.uuid)
        self.assertEqual(general_experience_comment.tags, ['parcours_anterieur', experience_uuid_str])
        self.assertEqual(general_experience_comment.content, 'The comment')

        self.assertEqual(authentication_experience_comment.object_uuid, high_school_diploma.uuid)
        self.assertEqual(
            authentication_experience_comment.tags, ['parcours_anterieur', experience_uuid_str, 'authentication']
        )
        self.assertEqual(authentication_experience_comment.content, 'The authentication comment')

    def test_with_old_exam_comment(self):
        exam = ExamFactory(person=self.first_admission.candidate)
        AdmissionExam.objects.create(admission=self.first_admission, exam=exam)

        experience_uuid_str = str(exam.uuid)

        with freezegun.freeze_time(self.default_datetime):
            general_experience_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.first_admission.uuid,
                tags=['parcours_anterieur', 'EXAMS'],
                content='The comment',
            )
            authentication_experience_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.first_admission.uuid,
                tags=['parcours_anterieur', 'EXAMS', 'authentication'],
                content='The authentication comment',
            )

        self.extract_experience_checklist_comment()

        comments_related_to_experience = CommentEntry.objects.filter(object_uuid=exam.uuid)
        comments_related_to_admission = CommentEntry.objects.filter(object_uuid=self.first_admission.uuid)

        self.assertEqual(comments_related_to_experience.count(), 2)
        self.assertEqual(comments_related_to_admission.count(), 0)

        general_experience_comment.refresh_from_db()
        authentication_experience_comment.refresh_from_db()

        self.assertEqual(general_experience_comment.object_uuid, exam.uuid)
        self.assertEqual(general_experience_comment.tags, ['parcours_anterieur', experience_uuid_str])
        self.assertEqual(general_experience_comment.content, 'The comment')

        self.assertEqual(authentication_experience_comment.object_uuid, exam.uuid)
        self.assertEqual(
            authentication_experience_comment.tags, ['parcours_anterieur', experience_uuid_str, 'authentication']
        )
        self.assertEqual(authentication_experience_comment.content, 'The authentication comment')

    def test_with_comments_linked_to_unknown_admission(self):
        default_uuid = uuid.uuid4()

        experience = EducationalExperienceFactory(person=self.first_admission.candidate)
        experience_uuid_str = str(experience.uuid)

        high_school_diploma = HighSchoolDiplomaFactory(person=self.first_admission.candidate)

        with freezegun.freeze_time(self.default_datetime):
            experience_comment: CommentEntry = CommentEntryFactory(
                object_uuid=default_uuid,
                tags=['parcours_anterieur', experience_uuid_str],
                content='The experience comment',
            )
            high_school_diploma_comment: CommentEntry = CommentEntryFactory(
                object_uuid=default_uuid,
                tags=['parcours_anterieur', 'ETUDES_SECONDAIRES'],
                content='The high school diploma comment',
            )

        self.extract_experience_checklist_comment()

        comments_related_to_unknown_uuid = CommentEntry.objects.filter(object_uuid=default_uuid)
        comments_related_to_experience = CommentEntry.objects.filter(object_uuid=experience.uuid)
        comments_related_to_high_school_diploma = CommentEntry.objects.filter(object_uuid=high_school_diploma.uuid)

        self.assertEqual(len(comments_related_to_unknown_uuid), 1)
        self.assertEqual(len(comments_related_to_experience), 1)
        self.assertEqual(comments_related_to_high_school_diploma.count(), 0)

        self.assertEqual(comments_related_to_unknown_uuid[0].uuid, high_school_diploma_comment.uuid)
        self.assertEqual(comments_related_to_experience[0].uuid, experience_comment.uuid)

    def test_with_several_experience_comments_linked_to_known_admissions(self):
        experience = EducationalExperienceFactory(person=self.first_admission.candidate)
        experience_uuid_str = str(experience.uuid)

        with freezegun.freeze_time(self.default_datetime):
            first_admission_experience_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.first_admission.uuid,
                tags=['parcours_anterieur', experience_uuid_str],
                content='The comment 1',
                author__first_name='John',
                author__last_name='Doe',
            )
            other_admission_experience_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.other_admission.uuid,
                tags=['parcours_anterieur', experience_uuid_str, 'authentication'],
                content='The comment 3',
            )
        with freezegun.freeze_time(self.default_datetime + datetime.timedelta(days=1)):
            second_admission_experience_comment: CommentEntry = CommentEntryFactory(
                object_uuid=self.second_admission.uuid,
                tags=['parcours_anterieur', experience_uuid_str],
                content='The comment 2',
                author__first_name='Jane',
                author__last_name='Poe',
            )

        self.extract_experience_checklist_comment()

        # Several comments are linked to the same experience -> the comments are merged
        comments_related_to_experience = CommentEntry.objects.filter(object_uuid=experience.uuid)

        self.assertEqual(len(comments_related_to_experience), 2)

        self.assertFalse(CommentEntry.objects.filter(object_uuid=self.first_admission.uuid).exists())
        self.assertFalse(CommentEntry.objects.filter(object_uuid=self.second_admission.uuid).exists())
        self.assertFalse(CommentEntry.objects.filter(object_uuid=self.other_admission.uuid).exists())

        self.assertFalse(CommentEntry.objects.filter(uuid=first_admission_experience_comment.uuid).exists())
        self.assertFalse(CommentEntry.objects.filter(uuid=second_admission_experience_comment.uuid).exists())
        self.assertTrue(CommentEntry.objects.filter(uuid=other_admission_experience_comment.uuid).exists())

        general_comment = next(
            (c for c in comments_related_to_experience if c.pk != other_admission_experience_comment.pk), None
        )
        authentication_comment = next(
            (c for c in comments_related_to_experience if c.pk == other_admission_experience_comment.pk), None
        )

        self.assertIsNotNone(general_comment)
        self.assertIsNotNone(authentication_comment)

        self.assertEqual(general_comment.author, None)
        self.assertEqual(general_comment.tags, ['parcours_anterieur', experience_uuid_str])
        self.assertEqual(general_comment.object_uuid, experience.uuid)
        self.assertEqual(
            general_comment.content,
            'Jane Poe (11:30 - 02/02/2020) : The comment 2\nJohn Doe (11:30 - 01/02/2020) : The comment 1\n',
        )

        self.assertEqual(authentication_comment.uuid, other_admission_experience_comment.uuid)
        self.assertEqual(authentication_comment.object_uuid, experience.uuid)
        self.assertEqual(authentication_comment.modified_at, self.default_datetime)
        self.assertEqual(authentication_comment.content, 'The comment 3')
