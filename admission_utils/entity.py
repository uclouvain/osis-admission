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
from datetime import datetime

from django.db.models import Q

from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import EntityType


def get_faculty_id_from_entity_id(entity_id):
    """
    From an entity id, get the id of the parent faculty (itself if it's a faculty).
    :param entity_id: The id of the entity
    :return: The id of the parent faculty
    """

    cte = EntityVersion.objects.with_children(entity_id=entity_id)

    faculty_id = (
        cte.join(EntityVersion, id=cte.col.id)
        .with_cte(cte)
        .filter(Q(entity_type=EntityType.FACULTY.name))
        .exclude(end_date__lte=datetime.today())
        .values_list('entity_id', flat=True)
    )[:1]

    if faculty_id:
        return faculty_id[0]
