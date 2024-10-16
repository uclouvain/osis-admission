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

from admission.admission_utils.list import (
    list_to_dict_with_prev_and_next_elements,
)


class ListTestCase(TestCase):
    def test_list_to_dict_with_prev_and_next_elements_with_objects(self):
        self.assertEqual(
            list_to_dict_with_prev_and_next_elements(
                list_to_process=[],
                id_attribute='id',
            ),
            {},
        )
        self.assertEqual(
            list_to_dict_with_prev_and_next_elements(
                list_to_process=[MagicMock(id='1')],
                id_attribute='id',
            ),
            {
                '1': {'previous': None, 'next': None},
            },
        )
        self.assertEqual(
            list_to_dict_with_prev_and_next_elements(
                list_to_process=[MagicMock(id='1'), MagicMock(id='2')],
                id_attribute='id',
            ),
            {
                '1': {'previous': None, 'next': '2'},
                '2': {'previous': '1', 'next': None},
            },
        )
        self.assertEqual(
            list_to_dict_with_prev_and_next_elements(
                list_to_process=[MagicMock(id='1'), MagicMock(id='2'), MagicMock(id='3')],
                id_attribute='id',
            ),
            {
                '1': {'previous': None, 'next': '2'},
                '2': {'previous': '1', 'next': '3'},
                '3': {'previous': '2', 'next': None},
            },
        )

    def test_list_to_dict_with_prev_and_next_elements_with_simple_values(self):
        self.assertEqual(
            list_to_dict_with_prev_and_next_elements(
                list_to_process=[],
            ),
            {},
        )
        self.assertEqual(
            list_to_dict_with_prev_and_next_elements(
                list_to_process=['1'],
            ),
            {
                '1': {'previous': None, 'next': None},
            },
        )
        self.assertEqual(
            list_to_dict_with_prev_and_next_elements(
                list_to_process=['1', '2'],
            ),
            {
                '1': {'previous': None, 'next': '2'},
                '2': {'previous': '1', 'next': None},
            },
        )
        self.assertEqual(
            list_to_dict_with_prev_and_next_elements(
                list_to_process=['1', '2', '3'],
            ),
            {
                '1': {'previous': None, 'next': '2'},
                '2': {'previous': '1', 'next': '3'},
                '3': {'previous': '2', 'next': None},
            },
        )
