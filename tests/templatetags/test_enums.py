##############################################################################
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
##############################################################################
import unittest

from admission.templatetags.enums import enum_display
from base.models.utils.utils import ChoiceEnum


class CustomChoiceEnum(ChoiceEnum):
    FIRST_CHOICE = 1
    SECOND_CHOICE = 2


class EnumTemplateTagTestCase(unittest.TestCase):
    def test_enum_return_right_value(self):
        value = enum_display('FIRST_CHOICE', 'CustomChoiceEnum')
        self.assertEqual(value, 1)

    def test_enum_return_key_with_unknown_enum(self):
        value = enum_display('FIRST_CHOICE', 'UnknownChoiceEnum')
        self.assertEqual(value, 'FIRST_CHOICE')

    def test_enum_return_empty_string_with_none_key(self):
        value = enum_display(None, 'UnknownChoiceEnum')
        self.assertEqual(value, '')
