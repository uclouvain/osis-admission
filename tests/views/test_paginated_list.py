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

from unittest import TestCase
from unittest.mock import MagicMock

from admission.views import PaginatedList


class PaginatedListTestCase(TestCase):
    def test_paginated_list_with_initial_ids(self):
        elts = [1, 2, 3]
        paginated_list = PaginatedList(
            complete_list=elts,
        )

        self.assertEqual(paginated_list.total_count, len(elts))

        self.assertEqual(paginated_list.sorted_elements, {
            1: {
                'previous': None,
                'next': 2,
            },
            2: {
                'previous': 1,
                'next': 3,
            },
            3: {
                'previous': 2,
                'next': None,
            },
        })

    def test_paginated_list_with_dynamic_ids(self):
        paginated_list = PaginatedList()

        self.assertEqual(paginated_list.total_count, 0)

        self.assertEqual(paginated_list.sorted_elements, {})

        paginated_list.append(1)
        paginated_list.append(2)
        paginated_list.append(3)

        self.assertEqual(paginated_list.total_count, 3)

        self.assertEqual(paginated_list.sorted_elements, {
            1: {
                'previous': None,
                'next': 2,
            },
            2: {
                'previous': 1,
                'next': 3,
            },
            3: {
                'previous': 2,
                'next': None,
            },
        })

    def test_paginated_list_with_dynamic_ids_and_a_specified_id_attribute(self):
        paginated_list = PaginatedList(id_attribute='id')

        self.assertEqual(paginated_list.total_count, 0)

        self.assertEqual(paginated_list.sorted_elements, {})

        paginated_list.append(MagicMock(id=1))
        paginated_list.append(MagicMock(id=2))
        paginated_list.append(MagicMock(id=3))

        self.assertEqual(paginated_list.total_count, 3)

        self.assertEqual(paginated_list.sorted_elements, {
            1: {
                'previous': None,
                'next': 2,
            },
            2: {
                'previous': 1,
                'next': 3,
            },
            3: {
                'previous': 2,
                'next': None,
            },
        })