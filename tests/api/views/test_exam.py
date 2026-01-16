# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid
from unittest import mock

import freezegun
from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.translation import gettext
from rest_framework import status
from rest_framework.test import APITestCase

from admission.models.exam import AdmissionExam
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory
from base.tests.factories.academic_year import AcademicYearFactory
from osis_profile.models import Exam
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience, \
    EtatAuthentificationParcours
from osis_profile.tests.factories.exam import ExamFactory, ExamTypeFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
@freezegun.freeze_time('2020-11-01')
class GeneralExamViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        cls.admission = GeneralEducationAdmissionFactory()

        cls.other_candidate = CandidateFactory().person

        cls.academic_years = {
            str(academic_year.year): academic_year
            for academic_year in AcademicYearFactory.produce(2020, number_past=2, number_future=2)
        }

        # Target url
        cls.url = resolve_url('general_exam', uuid=cls.admission.uuid)

        AdmissionAcademicCalendarFactory.produce_all_required()

    def setUp(self):
        # Mock files
        patcher = mock.patch(
            'osis_document_components.services.get_remote_token',
            side_effect=lambda value, **kwargs: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'osis_document_components.services.get_remote_metadata',
            return_value={'name': 'myfile', "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'osis_document_components.services.confirm_remote_upload',
            side_effect=lambda token, *args, **kwargs: token,
        )
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document_components.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: value if value else []
        self.addCleanup(patcher.stop)


    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_other_candidate_assert_not_authorized(self):
        self.client.force_authenticate(user=self.other_candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        methods_not_allowed = [
            'patch',
            'post',
            'delete',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_with_no_exam(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        # Without an exam type
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        self.assertEqual(
            response.json(),
            {
                'required': False,
                'title_fr': '',
                'title_en': '',
                'certificate': [],
                'year': None,
                'is_valuated': False,
            },
        )

        # With an exam type
        exam_type = ExamTypeFactory(education_group_years=[self.admission.training])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        self.assertEqual(
            response.json(),
            {
                'required': True,
                'title_fr': f'Attestation de réussite pour {exam_type.label_fr}',
                'title_en': f'Certificate of success for {exam_type.label_en}',
                'certificate': [],
                'year': None,
                'is_valuated': False,
            },
        )

    def test_get_with_exam(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        exam = ExamFactory(
            person=self.admission.candidate,
            type__education_group_years=[self.admission.training],
            year=self.academic_years['2020'],
        )

        admission_exam = AdmissionExam.objects.create(
            admission=self.admission,
            exam=exam,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


        # Check response data
        self.assertEqual(
            response.json(),
            {
                'required': True,
                'title_fr': f'Attestation de réussite pour {exam.type.label_fr}',
                'title_en': f'Certificate of success for {exam.type.label_en}',
                'certificate': [],
                'year': 2020,
                'is_valuated': False,
            },
        )

    def test_create_exam(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        exam_type = ExamTypeFactory(
            education_group_years=[self.admission.training],
        )

        certificate = [uuid.uuid4()]

        response = self.client.put(
            self.url,
            data={
                'certificate': certificate,
                'year': self.academic_years['2020'].year,
            },
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()

        self.assertEqual(
            json_response,
            {
                'required': True,
                'title_fr': f'Attestation de réussite pour {exam_type.label_fr}',
                'title_en': f'Certificate of success for {exam_type.label_en}',
                'certificate': [str(certificate[0])],
                'year': 2020,
                'is_valuated': False,
            },
        )

        # Check saved data
        admission_exams = AdmissionExam.objects.filter(
            admission=self.admission,
        ).select_related('exam')

        self.assertEqual(len(admission_exams), 1)

        self.assertEqual(admission_exams[0].exam.year, self.academic_years['2020'])
        self.assertEqual(admission_exams[0].exam.person, self.admission.candidate)
        self.assertEqual(admission_exams[0].exam.type, exam_type)
        self.assertEqual(admission_exams[0].exam.certificate, certificate)
        self.assertEqual(admission_exams[0].exam.validation_status, ChoixStatutValidationExperience.EN_BROUILLON.name)
        self.assertEqual(admission_exams[0].exam.authentication_status, EtatAuthentificationParcours.NON_CONCERNE.name)

    def test_update_exam(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        exam_type = ExamTypeFactory(
            education_group_years=[self.admission.training],
        )

        exam = ExamFactory(
            person=self.admission.candidate,
            type=exam_type,
            certificate=[],
            validation_status=ChoixStatutValidationExperience.AVIS_EXPERT.name,
            authentication_status=EtatAuthentificationParcours.VRAI.name,
            year=self.academic_years['2020'],
        )

        admission_exam = AdmissionExam.objects.create(
            admission=self.admission,
            exam=exam,
        )

        certificate = [uuid.uuid4()]

        response = self.client.put(
            self.url,
            data={
                'certificate': certificate,
                'year': self.academic_years['2021'].year,
            },
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()

        self.assertEqual(
            json_response,
            {
                'required': True,
                'title_fr': f'Attestation de réussite pour {exam_type.label_fr}',
                'title_en': f'Certificate of success for {exam_type.label_en}',
                'certificate': [str(certificate[0])],
                'year': 2021,
                'is_valuated': False,
            },
        )

        # Check saved data
        admission_exams = AdmissionExam.objects.filter(
            admission=self.admission,
        ).select_related('exam')

        self.assertEqual(len(admission_exams), 1)

        self.assertEqual(admission_exams[0].exam.year, self.academic_years['2021'])
        self.assertEqual(admission_exams[0].exam.person, self.admission.candidate)
        self.assertEqual(admission_exams[0].exam.type, exam_type)
        self.assertEqual(admission_exams[0].exam.certificate, certificate)
        self.assertEqual(admission_exams[0].exam.validation_status, ChoixStatutValidationExperience.AVIS_EXPERT.name)
        self.assertEqual(admission_exams[0].exam.authentication_status, EtatAuthentificationParcours.VRAI.name)
