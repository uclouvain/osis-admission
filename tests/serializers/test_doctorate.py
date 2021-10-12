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

from django.test import TestCase
from rest_framework import serializers

from admission.contrib.models import AdmissionType, DoctorateAdmission
from admission.contrib.serializers import DoctorateAdmissionReadSerializer
from base.tests.factories.person import PersonFactory


class DoctorateAdmissionSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        author = PersonFactory()
        cls.admission_doctorate_data = {
            "type": AdmissionType.ADMISSION.name,
            "candidate": cls.candidate,
            "author": author,
            "comment": "test admission doctorate serializer",
        }
        cls.admission = DoctorateAdmission.objects.create(
            **cls.admission_doctorate_data
        )
        cls.serializer = DoctorateAdmissionReadSerializer(instance=cls.admission)
        cls.serializer_data = {
            "type_select": AdmissionType.PRE_ADMISSION.name,
            "candidate_write": cls.candidate.pk,
            "comment": "test admission doctorate serializer",
        }

    def test_serializer_contains_expected_field(self):
        self.assertCountEqual(
            self.serializer.data.keys(),
            [
                "uuid",
                "url",
                "type",
                "candidate",
                "comment",
                "author",
                "created",
                "modified",
            ],
        )

    def test_serializer_without_required_data_is_not_valid(self):
        serializer = DoctorateAdmissionReadSerializer(data={})
        self.assertFalse(serializer.is_valid())

    def test_serializer_with_incorrect_data(self):
        serializer = DoctorateAdmissionReadSerializer(data={"candidate": 1})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_serializer_with_correct_data(self):
        serializer = DoctorateAdmissionReadSerializer(data=self.serializer_data)
        self.assertTrue(serializer.is_valid())
