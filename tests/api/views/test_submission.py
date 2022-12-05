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

import freezegun
from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.test import APITestCase

from admission.calendar.admission_calendar import *
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutProposition
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.person import IncompletePersonForBachelorFactory, IncompletePersonForIUFCFactory
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory


@freezegun.freeze_time("1980-03-25")
class GeneralPropositionSubmissionTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Validation errors
        cls.candidate_errors = IncompletePersonForBachelorFactory()
        cls.admission = GeneralEducationAdmissionFactory(
            candidate=cls.candidate_errors,
            # force type to have access conditions
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__academic_year__current=True,
        )
        cls.error_url = resolve_url("admission_api_v1:submit-general-proposition", uuid=cls.admission.uuid)

        AcademicYearFactory.produce(number_future=6)
        for pool in [
            DoctorateAdmissionCalendar,
            ContinuingEducationAdmissionCalendar,
            AdmissionPoolExternalEnrollmentChangeCalendar,
            AdmissionPoolExternalReorientationCalendar,
            AdmissionPoolVipCalendar,
            AdmissionPoolHueUclPathwayChangeCalendar,
            AdmissionPoolInstituteChangeCalendar,
            AdmissionPoolUe5BelgianCalendar,
            AdmissionPoolUe5NonBelgianCalendar,
            AdmissionPoolHue5BelgiumResidencyCalendar,
            AdmissionPoolHue5ForeignResidencyCalendar,
            AdmissionPoolNonResidentQuotaCalendar,
        ]:
            pool.ensure_consistency_until_n_plus_6()

        # Validation ok
        cls.admission_ok = GeneralEducationAdmissionFactory(
            training__academic_year__current=True,
            bachelor_with_access_conditions_met=True,
        )
        cls.candidate_ok = cls.admission_ok.candidate
        cls.ok_url = resolve_url("admission_api_v1:submit-general-proposition", uuid=cls.admission_ok.uuid)
        # Ensure we have this training available for the next acad
        GeneralEducationTrainingFactory(
            academic_year__year=1980,
            education_group_type=cls.admission_ok.training.education_group_type,
            acronym=cls.admission_ok.training.acronym,
            partial_acronym=cls.admission_ok.training.partial_acronym,
        )

    def test_general_proposition_verification_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        response = self.client.get(self.error_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("ADMISSION-2", [e["status_code"] for e in response.json()])

    def test_general_proposition_submission_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        response = self.client.post(self.error_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_general_proposition_verification_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        response = self.client.get(self.ok_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_general_proposition_submission_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        self.assertEqual(self.admission_ok.status, ChoixStatutProposition.IN_PROGRESS.name)
        response = self.client.post(self.ok_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.admission_ok.refresh_from_db()
        self.assertEqual(self.admission_ok.status, ChoixStatutProposition.SUBMITTED.name)


class ContinuingPropositionSubmissionTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Validation errors
        cls.candidate_errors = IncompletePersonForIUFCFactory()
        cls.admission = ContinuingEducationAdmissionFactory(
            candidate=cls.candidate_errors,
            # force type to have access conditions
            training__education_group_type__name=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
        )
        cls.error_url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=cls.admission.uuid)

        # Validation ok
        cls.admission_ok = ContinuingEducationAdmissionFactory(with_access_conditions_met=True)
        cls.candidate_ok = cls.admission_ok.candidate
        cls.ok_url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=cls.admission_ok.uuid)

    def test_continuing_proposition_verification_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        response = self.client.get(self.error_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = response.json()
        self.assertEqual(len(json_content), 1, "Should have errors")
        self.assertDictEqual(
            json_content[0],
            {"status_code": "ADMISSION-2", "detail": _("Admission conditions not met.")},
        )

    def test_continuing_proposition_submission_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        response = self.client.post(self.error_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_continuing_proposition_verification_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        response = self.client.get(self.ok_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_continuing_proposition_submission_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        self.assertEqual(self.admission_ok.status, ChoixStatutProposition.IN_PROGRESS.name)
        response = self.client.post(self.ok_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admission_ok.refresh_from_db()
        self.assertEqual(self.admission_ok.status, ChoixStatutProposition.SUBMITTED.name)
