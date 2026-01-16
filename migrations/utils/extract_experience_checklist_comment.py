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
from django.contrib.postgres.fields import ArrayField
from django.db import transaction
from django.db.models import Exists, OuterRef, F, Q, Func, Subquery, Value
from django.db.models.fields import UUIDField, CharField
from django.db.models.functions import Length, Cast
from django.utils.translation import gettext


class ArrayReplace(Func):
    function = "array_replace"
    output_field = ArrayField(base_field=CharField(max_length=50))

@transaction.atomic
def extract_experience_checklist_comment(comment_model, base_admission_model):
    experience_condition = Q(
        tags__0='parcours_anterieur',
        tags_1_len=36,
    )
    high_school_diploma_condition = Q(
        tags__0='parcours_anterieur',
        tags__1='ETUDES_SECONDAIRES',
    )

    # Update the object uuid to specify the experience uuid instead of the admission uuid
    comment_model.objects.annotate(
        tags_1_len=Length('tags__1'),
    ).filter(experience_condition).update(object_uuid=Cast(F('tags__1'), output_field=UUIDField()))

    # Update the object uuid to specify the secondary studies uuid instead of the admission uuid
    matching_admission = base_admission_model.objects.filter(uuid=OuterRef('object_uuid'), candidate__highschooldiploma__isnull=False)
    comment_model.objects.filter(high_school_diploma_condition).annotate(
        high_school_diploma_uuid=Subquery(matching_admission.values('candidate__highschooldiploma__uuid')[:1]),
    ).filter(high_school_diploma_uuid__isnull=False).update(
        object_uuid=F('high_school_diploma_uuid'),
        tags=ArrayReplace('tags', Value('ETUDES_SECONDAIRES'), Cast(F('high_school_diploma_uuid'), output_field=CharField())),
    )

    # Now we can have several comments by object uuid by tags but we want only unique comments so we merge them
    duplicate_comments = (
        comment_model.objects.annotate(tags_1_len=Length('tags__1')).filter(experience_condition | high_school_diploma_condition)
        .filter(
            Exists(
                comment_model.objects.filter(
                    tags=OuterRef('tags'),
                    object_uuid=OuterRef('object_uuid'),
                ).exclude(uuid=OuterRef('uuid'))
            )
        )
        .select_related('author')
    )

    comments_to_create_by_object_uuid = {}
    unknown_author = gettext('Unknown author')

    for comment in duplicate_comments:
        comment_author = f'{comment.author.first_name} {comment.author.last_name}' if comment.author else unknown_author
        comment_content = (
            f'{comment_author} ({comment.modified_at:"%H:%M")} - '
            f'{comment.modified_at:"%d/%m/%Y"}) : {comment.content}\n'
        )

        if comment.object_uuid in comments_to_create_by_object_uuid:
            comments_to_create_by_object_uuid[comment.object_uuid].content += comment_content
        else:
            comments_to_create_by_object_uuid[comment.object_uuid] = comment_model(
                tags=comment.tags,
                content=comment_content,
                object_uuid=comment.object_uuid,
            )

    duplicate_comments.delete()
    comment_model.objects.bulk_create(objs=comments_to_create_by_object_uuid.values())
