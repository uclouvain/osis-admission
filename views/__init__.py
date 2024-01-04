# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, TypeVar

from django.core import paginator
from django.utils.functional import cached_property


T = TypeVar('T')


class PaginatedList(List[T]):
    def __init__(self, total_count=0, *args, **kwargs):
        self.total_count = total_count
        super().__init__(*args, **kwargs)


class ListPaginator(paginator.Paginator):
    """object_list must be a PaginatedList instance."""

    def page(self, number):
        number = self.validate_number(number)
        top = self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return self._get_page(self.object_list[0:top], number, self)

    @cached_property
    def count(self):
        return getattr(self.object_list, 'total_count', len(self.object_list))
