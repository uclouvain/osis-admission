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
import uuid

from django.test import TestCase

from admission.utils import get_uuid_value


class UtilsTestCase(TestCase):
    def test_get_uuid_returns_uuid_if_value_if_uuid(self):
        uuid_value = uuid.uuid4()
        self.assertEqual(get_uuid_value(str(uuid_value)), uuid_value)

    def test_get_uuid_returns_input_value_if_not_uuid(self):
        other_value = 'abcdef'
        self.assertEqual(get_uuid_value(other_value), other_value)
