# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from datetime import date

from django.db import models

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.utils.cte import CTESubquery

__all__ = ['EntityProxy']


class EntityQuerySet(models.QuerySet):
    _last_version_qs = None

    def get_last_version(self):
        """Get the last version subquery for entity version"""
        if self._last_version_qs is None:
            self._last_version_qs = EntityVersion.objects.filter(entity=models.OuterRef('pk')).order_by('-start_date')
        return self._last_version_qs

    def with_title(self):
        return self.annotate(
            title=models.Subquery(self.get_last_version().values('title')[:1]),
        )

    def with_type(self):
        return self.annotate(
            type=models.Subquery(self.get_last_version().values('entity_type')[:1]),
        )

    def with_parent(self):
        return self.annotate(
            parent=models.Subquery(self.get_last_version().values('parent')[:1]),
        )

    def with_acronym(self):
        return self.annotate(
            acronym=models.Subquery(self.get_last_version().values('acronym')[:1]),
        )

    def with_acronym_path(self):
        return self.annotate(
            acronym_path=CTESubquery(
                EntityVersion.objects.with_acronym_path(entity_id=models.OuterRef('pk'),).values(
                    'acronym_path'
                )[:1]
            ),
        )

    def with_path_as_string(self):
        return self.annotate(
            path_as_string=CTESubquery(
                EntityVersion.objects.with_acronym_path(entity_id=models.OuterRef('pk'),).values(
                    'path_as_string'
                )[:1],
                output_field=models.TextField(),
            ),
        )

    def only_roots(self):
        return self.annotate(
            is_root=models.Exists(
                EntityVersion.objects.filter(
                    entity_id=models.OuterRef('pk'),
                )
                .current(date.today())
                .only_roots()
            ),
        ).filter(is_root=True)

    def only_valid(self):
        return self.annotate(
            is_valid=models.Exists(self.get_last_version().exclude(end_date__lte=date.today())),
        ).filter(is_valid=True)


class EntityManager(models.Manager.from_queryset(EntityQuerySet)):
    pass


class EntityProxy(Entity):
    """Proxy model of base.Entity"""

    objects = EntityManager()

    class Meta:
        proxy = True
