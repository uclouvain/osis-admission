# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase

from admission.utils import takewhile_return_attribute_values, format_academic_year


class UtilsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.array = [
            {'a': 1, 'b': 'First element'},
            {'a': 1, 'b': 'Second element'},
            {'a': 1, 'b': 'Third element'},
            {'a': 2, 'b': 2},
            {'a': 3, 'b': 2},
        ]

    def test_takewhile_return_attribute_values_with_checked_predicate(self):
        self.assertEqual(
            list(takewhile_return_attribute_values(lambda obj: obj['a'] == 1, self.array, 'b')),
            ['First element', 'Second element', 'Third element'],
        )

    def test_takewhile_return_attribute_values_with_unchecked_predicate(self):
        self.assertEqual(
            list(takewhile_return_attribute_values(lambda obj: obj['a'] == 5, self.array, 'b')),
            [],
        )

    def test_format_academic_year_with_empty_year(self):
        self.assertEqual(format_academic_year(''), '')

    def test_format_academic_year_with_year_as_int(self):
        self.assertEqual(format_academic_year(2020), '2020-2021')

    def test_format_academic_year_with_year_as_str(self):
        self.assertEqual(format_academic_year('2020'), '2020-2021')

    def test_format_academic_year_with_year_as_float(self):
        self.assertEqual(format_academic_year(2020.0), '2020-2021')
