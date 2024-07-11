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

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count


def remove_duplicate_candidates(candidate_model):
    """Remove the candidate having the same person_id"""

    # Group by the candidates by person_id
    duplicate_candidates = (
        candidate_model.objects.all()
        .values('person_id')
        .alias(count=Count('person_id'))
        .annotate(candidates_pks=ArrayAgg('pk'))
        .filter(count__gt=1)
    )

    # Get a list of the duplicate candidates to delete
    candidate_to_delete_ids = []
    for duplicate_candidate in duplicate_candidates:
        candidate_to_delete_ids += duplicate_candidate['candidates_pks'][1:]

    # Delete the duplicate candidates
    candidate_model.objects.filter(id__in=candidate_to_delete_ids).delete()
