# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from base.models.entity_version import EntityVersion

__all__ = [
    'EntityAutocomplete',
]

__namespace__ = False


class EntityAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    url_patterns = 'entities'

    def get_result_value(self, result):
        return result.uuid

    def get_result_label(self, result):
        return '{title} ({acronym})'.format(title=result.title, acronym=result.acronym)

    def get_queryset(self):
        qs = EntityVersion.objects.all()

        # Filter by organisation type
        organization_type = self.forwarded.get('organization_type')
        if organization_type:
            qs = EntityVersion.objects.filter(entity__organization__type=organization_type)

        # Filter by entity type
        entity_type = self.forwarded.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        # Filter by title or acronym
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(acronym__icontains=q))

        qs = qs.only(
            'uuid',
            'title',
            'acronym',
        ).order_by('acronym')

        return qs
