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
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext


@transaction.atomic
def extract_personal_data_checklist_comment(comment_model, base_admission_model):
    tags = ['donnees_personnelles']

    # Update the object uuid to specify the person uuid instead on the admission uuid
    matching_admission = base_admission_model.objects.filter(uuid=OuterRef('object_uuid'))

    comment_model.objects.filter(tags=tags).filter(Exists(matching_admission)).update(
        object_uuid=matching_admission.values('candidate__uuid')[:1]
    )

    # Now we can have several comments by object uuid by tags but we want only unique comments so we merge them
    duplicate_comments = (
        comment_model.objects.filter(tags=tags)
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
            f'{comment_author} ({comment.modified_at.strftime("%H:%M")} - '
            f'{comment.modified_at.strftime("%d/%m/%Y")}) : {comment.content}\n'
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
