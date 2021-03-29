import datetime
import uuid

from django.test import TestCase
from rest_framework import serializers

from admission.contrib.models import AdmissionType, AdmissionDoctorate
from admission.contrib.serializers import AdmissionDoctorateSerializer
from base.tests.factories.person import PersonFactory


class AdmissionDoctorateSerializerTestCase(TestCase):
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
        cls.admission = AdmissionDoctorate.objects.create(
            **cls.admission_doctorate_data
        )
        cls.serializer = AdmissionDoctorateSerializer(instance=cls.admission)
        cls.serializer_data = {
            "uuid": uuid.uuid4(),
            "url": "http://test.valid.url",
            "type": AdmissionType.PRE_ADMISSION.name,
            "candidate": cls.candidate,
            "author": author,
            "comment": "test admission doctorate serializer",
            "created": datetime.datetime.now(),
            "modified": datetime.datetime.now(),
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
        serializer = AdmissionDoctorateSerializer(data={})
        self.assertFalse(serializer.is_valid())

    def test_serializer_with_incorrect_data(self):
        serializer = AdmissionDoctorateSerializer(data={"candidate": 1})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_serializer_with_correct_data(self):
        serializer = AdmissionDoctorateSerializer(data=self.serializer_data)
        self.assertTrue(serializer.is_valid())
