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

from admission.contrib.models.base import admission_directory_path
from admission.tests.factories import DoctorateAdmissionFactory


class BaseTestCase(TestCase):

    def setUp(self):
        self.base_admission = DoctorateAdmissionFactory()

    def test_valid_upload_to(self):
        self.assertEqual(
            admission_directory_path(self.base_admission, 'my_file.pdf'),
            'admission/{}/{}/my_file.pdf'.format(self.base_admission.candidate.uuid, self.base_admission.uuid)
        )
