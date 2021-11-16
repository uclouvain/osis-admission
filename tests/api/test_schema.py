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
from django.core.files.temp import NamedTemporaryFile
from django.core.management import call_command
from django.test import TestCase


class ApiSchemaTestCase(TestCase):
    def test_api_schema_matches_generation(self):
        with NamedTemporaryFile(mode='w+') as temp:
            call_command(
                'generateschema',
                urlconf='admission.api.url_v1',
                generator_class='admission.api.schema.AdmissionSchemaGenerator',
                file=temp.name,
            )
            with open('admission/schema.yml') as f:
                self.assertEqual(f.read(), temp.read(), msg="Schema has not been re-generated")
