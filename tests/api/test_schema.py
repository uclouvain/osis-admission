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
import filecmp
import sys
import unittest
from unittest import SkipTest

from django.core.files.temp import NamedTemporaryFile
from django.core.management import ManagementUtility, call_command
from django.test import TestCase


class ApiSchemaTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # Only execute if tests are launched globally
        argv = sys.argv
        utility = ManagementUtility(argv)
        test_command = utility.fetch_command('test')
        parser = test_command.create_parser(argv[0], argv[1])

        options = parser.parse_args(argv[2:])
        if not options.args or options.args[0].split('.')[0] != 'admission':
            raise SkipTest("Not testing admission directly, do not test schema")
        super().setUpClass()

    @unittest.skip
    def test_api_schema_matches_generation(self):
        with NamedTemporaryFile(mode='w+') as temp:
            call_command(
                'compilemessages',
                verbosity=0,
                locale='fr_BE',
                ignore_patterns=[
                    '.git',
                    '*/.git',
                    '.*',
                    '*/.*',
                    '__pycache__',
                    'node_modules',
                    'uploads',
                    'ddd',
                    '*/ddd',
                    'infrastructure',
                    '*/infrastructure',
                    '*/migrations',
                    '*/static',
                    '*/tests',
                    '*/templates',
                ],
            )
            call_command(
                'generateschema',
                urlconf='admission.api.url_v1',
                generator_class='admission.api.schema.AdmissionSchemaGenerator',
                file=temp.name,
            )
            self.assertTrue(filecmp.cmp('admission/schema.yml', temp.name), msg="Schema has not been re-generated")
