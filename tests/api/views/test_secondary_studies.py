# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

import datetime
from unittest.mock import patch
from uuid import UUID

import freezegun
from django.shortcuts import resolve_url
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models.base import BaseAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.secondary_studies import (
    BelgianHighSchoolDiplomaFactory,
    ForeignHighSchoolDiplomaFactory,
    HighSchoolDiplomaAlternativeFactory,
)
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory
from base.models.enums.got_diploma import GotDiploma
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version_address import EntityVersionAddressFactory
from base.tests.factories.person import PersonFactory
from osis_profile.models import (
    BelgianHighSchoolDiploma,
    ForeignHighSchoolDiploma,
    HighSchoolDiplomaAlternative,
)
from osis_profile.models.enums.education import EducationalType
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.high_school import HighSchoolFactory
from reference.tests.factories.language import LanguageFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
@freezegun.freeze_time('2023-01-01')
class BelgianHighSchoolDiplomaTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        AdmissionAcademicCalendarFactory.produce_all_required(cls.academic_year.year)
        cls.high_school = HighSchoolFactory()

        EntityVersionAddressFactory(entity_version__entity=EntityFactory(organization=cls.high_school))

        cls.agnostic_url = resolve_url("secondary-studies")
        cls.diploma_data = {
            "graduated_from_high_school": GotDiploma.YES.name,
            "belgian_diploma": {
                "institute": cls.high_school.uuid,
                "academic_graduation_year": cls.academic_year.year,
                "educational_type": "TEACHING_OF_GENERAL_EDUCATION",
            },
            "specific_question_answers": {
                "fe254203-17c7-47d6-95e4-3c5c532da551": "My answer !",
            },
        }
        cls.diploma_updated_data = {
            "graduated_from_high_school": GotDiploma.YES.name,
            "belgian_diploma": {
                "institute": cls.high_school.uuid,
                "academic_graduation_year": cls.academic_year.year,
            },
        }
        doctoral_commission = EntityFactory()

        # Users
        promoter = PromoterFactory()
        doctorate_admission = DoctorateAdmissionFactory(
            supervision_group=promoter.process,
            training__management_entity=doctoral_commission,
        )
        general_admission = GeneralEducationAdmissionFactory(
            candidate=doctorate_admission.candidate,
        )
        continuing_admission = ContinuingEducationAdmissionFactory(
            candidate=doctorate_admission.candidate,
        )
        cls.doctorate_admission_url = resolve_url("secondary-studies", uuid=doctorate_admission.uuid)
        cls.general_admission_url = resolve_url("general_secondary_studies", uuid=general_admission.uuid)
        cls.continuing_admission_url = resolve_url("continuing_secondary_studies", uuid=continuing_admission.uuid)
        cls.candidate_user = doctorate_admission.candidate.user
        cls.candidate_user_without_admission = CandidateFactory().person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user
        cls.promoter_user = promoter.person.user
        cls.committee_member_user = CaMemberFactory(process=promoter.process).person.user
        cls.doctorate_admission_uuid = doctorate_admission.uuid
        cls.general_admission_uuid = general_admission.uuid
        cls.continuing_admission_uuid = continuing_admission.uuid

    def create_belgian_diploma_with_doctorate_admission(self, data):
        self.client.force_authenticate(self.candidate_user)
        return self.client.put(self.doctorate_admission_url, data)

    def create_belgian_diploma_with_general_admission(self, data):
        self.client.force_authenticate(self.candidate_user)
        return self.client.put(self.general_admission_url, data)

    def create_belgian_diploma_with_continuing_admission(self, data):
        self.client.force_authenticate(self.candidate_user)
        return self.client.put(self.continuing_admission_url, data)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate_user)
        methods_not_allowed = ["delete", "post", "patch"]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.doctorate_admission_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_diploma_get_with_candidate(self):
        self.client.force_authenticate(user=self.candidate_user)
        self.create_belgian_diploma_with_doctorate_admission(self.diploma_data)
        response = self.client.get(self.doctorate_admission_url)
        self.assertEqual(
            response.json()["belgian_diploma"]["academic_graduation_year"],
            self.diploma_data["belgian_diploma"]["academic_graduation_year"],
        )

    def test_diploma_create_with_doctorate_admission(self):
        self.client.force_authenticate(user=self.candidate_user)
        response = self.create_belgian_diploma_with_doctorate_admission(self.diploma_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        belgian_diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.candidate_user.pk)
        self.assertEqual(
            belgian_diploma.academic_graduation_year.year,
            self.diploma_data["belgian_diploma"]["academic_graduation_year"],
        )
        self.assertIsNone(belgian_diploma.community)
        self.assertEqual(belgian_diploma.educational_type, self.diploma_data["belgian_diploma"]["educational_type"])
        self.assertEqual(belgian_diploma.educational_other, "")
        self.assertEqual(belgian_diploma.institute.uuid, self.diploma_data["belgian_diploma"]["institute"])
        self.assertEqual(belgian_diploma.other_institute_name, "")
        foreign_diploma = ForeignHighSchoolDiploma.objects.filter(person__user_id=self.candidate_user.pk)
        self.assertEqual(foreign_diploma.count(), 0)
        updated_admission = BaseAdmission.objects.get(uuid=self.doctorate_admission_uuid)
        self.assertEqual(
            updated_admission.specific_question_answers,
            {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My answer !',
            },
        )

    def test_diploma_create_with_general_admission(self):
        self.client.force_authenticate(user=self.candidate_user)
        response = self.create_belgian_diploma_with_general_admission(self.diploma_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

        belgian_diploma = BelgianHighSchoolDiploma.objects.filter(person__user_id=self.candidate_user.pk)
        self.assertEqual(belgian_diploma.count(), 1)

        foreign_diploma = ForeignHighSchoolDiploma.objects.filter(person__user_id=self.candidate_user.pk)
        self.assertEqual(foreign_diploma.count(), 0)

        updated_admission = BaseAdmission.objects.get(uuid=self.general_admission_uuid)
        self.assertEqual(
            updated_admission.specific_question_answers,
            {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My answer !',
            },
        )
        self.assertEqual(updated_admission.modified_at, datetime.datetime.now())
        self.assertEqual(updated_admission.last_update_author, self.candidate_user.person)

    def test_diploma_create_with_continuing_admission(self):
        self.client.force_authenticate(user=self.candidate_user)
        response = self.create_belgian_diploma_with_continuing_admission(self.diploma_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

        belgian_diploma = BelgianHighSchoolDiploma.objects.filter(person__user_id=self.candidate_user.pk)
        self.assertEqual(belgian_diploma.count(), 1)

        foreign_diploma = ForeignHighSchoolDiploma.objects.filter(person__user_id=self.candidate_user.pk)
        self.assertEqual(foreign_diploma.count(), 0)

        updated_admission = BaseAdmission.objects.get(uuid=self.continuing_admission_uuid)
        self.assertEqual(
            updated_admission.specific_question_answers,
            {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My answer !',
            },
        )

    def test_diploma_update_with_candidate(self):
        self.create_belgian_diploma_with_doctorate_admission(self.diploma_data)
        response = self.client.put(
            self.doctorate_admission_url,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
                "belgian_diploma": {
                    "institute": self.high_school.uuid,
                    "academic_graduation_year": self.academic_year.year,
                },
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.candidate_user.pk)
        self.assertEqual(diploma.institute.uuid, self.diploma_data["belgian_diploma"]["institute"])

    def test_diploma_update_by_belgian_diploma(self):
        ForeignHighSchoolDiplomaFactory(person=self.candidate_user.person)
        HighSchoolDiplomaAlternativeFactory(person=self.candidate_user.person)
        self.assertEqual(ForeignHighSchoolDiploma.objects.count(), 1)
        response = self.create_belgian_diploma_with_doctorate_admission(self.diploma_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertIsNone(response.json()["foreign_diploma"])
        self.assertIsNone(response.json()["high_school_diploma_alternative"])
        self.assertIsNotNone(response.json()["belgian_diploma"])
        self.assertEqual(ForeignHighSchoolDiploma.objects.count(), 0)
        self.assertEqual(HighSchoolDiplomaAlternative.objects.count(), 0)
        diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.candidate_user.pk)
        self.assertEqual(diploma.institute.uuid, self.diploma_data["belgian_diploma"]["institute"])

    def test_delete_diploma(self):
        self.create_belgian_diploma_with_doctorate_admission(self.diploma_data)
        self.create_belgian_diploma_with_doctorate_admission({"graduated_from_high_school": GotDiploma.NO.name})
        self.assertEqual(BelgianHighSchoolDiploma.objects.filter(person__user_id=self.candidate_user.pk).count(), 0)

    def test_diploma_get_with_no_role_user(self):
        self.create_belgian_diploma_with_doctorate_admission(self.diploma_data)
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.doctorate_admission_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_diploma_update_with_no_role_user(self):
        self.create_belgian_diploma_with_doctorate_admission(self.diploma_data)
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.put(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.put(self.doctorate_admission_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_diploma_get_with_promoter_user(self):
        self.create_belgian_diploma_with_doctorate_admission(self.diploma_data)
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.doctorate_admission_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_diploma_update_with_promoter_user(self):
        self.create_belgian_diploma_with_doctorate_admission(self.diploma_data)
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.put(self.doctorate_admission_url, self.diploma_updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_diploma_update_is_partially_working_if_already_valuated_by_admission(self):
        self.create_belgian_diploma_with_general_admission(self.diploma_data)
        diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.candidate_user.pk)
        self.assertEqual(diploma.educational_type, self.diploma_data['belgian_diploma']['educational_type'])
        admission = BaseAdmission.objects.get(uuid=self.general_admission_uuid)
        self.assertEqual(admission.specific_question_answers, self.diploma_data['specific_question_answers'])
        self.assertEqual(admission.modified_at, datetime.datetime.now())
        self.assertEqual(admission.last_update_author, self.candidate_user.person)
        # Valuate the secondary studies
        ContinuingEducationAdmissionFactory(
            candidate=self.candidate_user.person,
            valuated_secondary_studies_person=self.candidate_user.person,
        )

        # Want to update the diploma and the specific question answers -> only update the specific question answers
        updated_data = {
            "graduated_from_high_school": GotDiploma.THIS_YEAR.name,
            "belgian_diploma": {
                "institute": self.high_school.uuid,
                "academic_graduation_year": self.academic_year.year,
                "educational_type": EducationalType.TRANSITION_METHOD.name,
            },
            "specific_question_answers": {
                "fe254203-17c7-47d6-95e4-3c5c532da551": "My answer 2 !",
            },
        }
        self.create_belgian_diploma_with_general_admission(updated_data)
        diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.candidate_user.pk)
        self.assertEqual(diploma.educational_type, self.diploma_data['belgian_diploma']['educational_type'])
        self.assertEqual(diploma.person.graduated_from_high_school, self.diploma_data['graduated_from_high_school'])
        admission = BaseAdmission.objects.get(uuid=self.general_admission_uuid)
        self.assertEqual(admission.specific_question_answers, updated_data['specific_question_answers'])


@override_settings(ROOT_URLCONF='admission.api.url_v1')
@freezegun.freeze_time('2020-11-01')
class ForeignHighSchoolDiplomaTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admission = DoctorateAdmissionFactory()
        cls.user = cls.admission.candidate.user
        cls.url = reverse("secondary-studies")
        cls.admission_url = resolve_url("secondary-studies", uuid=cls.admission.uuid)
        cls.academic_year = AcademicYearFactory(current=True)
        cls.language = LanguageFactory(code="FR")
        cls.country = CountryFactory(iso_code="FR")
        cls.foreign_diploma_data = {
            "graduated_from_high_school": GotDiploma.YES.name,
            "foreign_diploma": {
                "other_linguistic_regime": "Français",
                "academic_graduation_year": cls.academic_year.year,
                "linguistic_regime": "FR",
                "country": "FR",
            },
        }
        cls.general_admission = GeneralEducationAdmissionFactory(candidate=cls.admission.candidate)
        cls.general_admission_url = resolve_url("general_secondary_studies", uuid=cls.general_admission.uuid)

        AdmissionAcademicCalendarFactory.produce_all_required()

    def create_foreign_diploma(self, data):
        self.client.force_authenticate(self.user)
        return self.client.put(self.admission_url, data)

    def create_foreign_diploma_with_general_admission(self, data):
        self.client.force_authenticate(self.user)
        return self.client.put(self.general_admission_url, data)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.user)
        methods_not_allowed = ["delete", "post", "patch"]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.admission_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_diploma_get(self):
        self.create_foreign_diploma(self.foreign_diploma_data)
        response = self.client.get(self.url)
        self.assertEqual(response.json()["foreign_diploma"]["other_linguistic_regime"], "Français")

    def test_diploma_create(self):
        response = self.create_foreign_diploma(self.foreign_diploma_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        foreign_diploma = ForeignHighSchoolDiploma.objects.get(person__user_id=self.user.pk)
        self.assertEqual(foreign_diploma.academic_graduation_year, self.academic_year)
        self.assertEqual(foreign_diploma.country, self.country)
        self.assertEqual(foreign_diploma.linguistic_regime, self.language)
        belgian_diploma = BelgianHighSchoolDiploma.objects.filter(person__user_id=self.user.pk)
        self.assertEqual(belgian_diploma.count(), 0)

    def test_diploma_create_with_general_admission(self):
        response = self.create_foreign_diploma_with_general_admission(self.foreign_diploma_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        foreign_diploma = ForeignHighSchoolDiploma.objects.get(person__user_id=self.user.pk)
        self.assertEqual(foreign_diploma.academic_graduation_year, self.academic_year)
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.user.person)

    def test_diploma_update_by_foreign_diploma(self):
        BelgianHighSchoolDiplomaFactory(person=self.user.person)
        HighSchoolDiplomaAlternativeFactory(person=self.user.person)
        response = self.create_foreign_diploma(self.foreign_diploma_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertIsNone(response.json()["belgian_diploma"])
        self.assertIsNone(response.json()["high_school_diploma_alternative"])
        self.assertIsNotNone(response.json()["foreign_diploma"])
        diploma = ForeignHighSchoolDiploma.objects.get(person__user_id=self.user.pk)
        self.assertEqual(diploma.other_linguistic_regime, "Français")
        self.assertEqual(BelgianHighSchoolDiploma.objects.count(), 0)
        self.assertEqual(HighSchoolDiplomaAlternative.objects.count(), 0)

    def test_delete_diploma(self):
        self.create_foreign_diploma(self.foreign_diploma_data)
        self.assertEqual(
            ForeignHighSchoolDiploma.objects.get(person__user_id=self.user.pk).other_linguistic_regime,
            "Français",
        )
        self.client.put(self.admission_url, {"graduated_from_high_school": GotDiploma.NO.name})
        self.assertEqual(ForeignHighSchoolDiploma.objects.filter(person__user_id=self.user.pk).count(), 0)


@override_settings(ROOT_URLCONF='admission.api.url_v1', OSIS_DOCUMENT_BASE_URL="http://dummyurl.com/document/")
class HighSchoolDiplomaAlternativeTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admission = DoctorateAdmissionFactory()
        cls.user = cls.admission.candidate.user
        cls.url = reverse("secondary-studies")
        cls.admission_url = resolve_url("secondary-studies", uuid=cls.admission.uuid)
        cls.general_admission_url = resolve_url("general_secondary_studies", uuid=cls.admission.uuid)
        cls.file_uuid = '4bdffb42-552d-415d-9e4c-725f10dce228'
        cls.high_school_diploma_alternative_data = {
            "graduated_from_high_school": GotDiploma.NO.name,
            "high_school_diploma_alternative": {
                "first_cycle_admission_exam": [cls.file_uuid],
            },
        }
        AdmissionAcademicCalendarFactory.produce_all_required()

    def setUp(self):
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile"})
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            return_value=self.file_uuid,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: [self.file_uuid] if value else [],
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def create_high_school_diploma_alternative(self, data):
        self.client.force_authenticate(self.user)
        return self.client.put(self.admission_url, data)

    def create_high_school_diploma_alternative_with_general_admission(self, data):
        self.client.force_authenticate(self.user)
        return self.client.put(self.general_admission_url, data)

    def test_diploma_get(self):
        self.create_high_school_diploma_alternative(self.high_school_diploma_alternative_data)
        response = self.client.get(self.url)
        self.assertEqual(
            response.json()["high_school_diploma_alternative"]["first_cycle_admission_exam"],
            [self.file_uuid],
        )

    def test_diploma_create(self):
        BelgianHighSchoolDiplomaFactory(person=self.user.person)
        ForeignHighSchoolDiplomaFactory(person=self.user.person)
        # Create the high school diploma alternative
        response = self.create_high_school_diploma_alternative(self.high_school_diploma_alternative_data)
        # Check response
        json_response = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK, json_response)
        self.assertIsNone(json_response["belgian_diploma"])
        self.assertIsNone(json_response["foreign_diploma"])
        self.assertIsNotNone(json_response["high_school_diploma_alternative"])
        # Check the updated object
        high_school_diploma_alternative = HighSchoolDiplomaAlternative.objects.get(person__user_id=self.user.pk)
        self.assertEqual(high_school_diploma_alternative.first_cycle_admission_exam, [UUID(self.file_uuid)])
        # Clean previous high school diplomas
        self.assertEqual(BelgianHighSchoolDiploma.objects.filter(person=self.user.person).count(), 0)
        self.assertEqual(ForeignHighSchoolDiploma.objects.filter(person=self.user.person).count(), 0)

    def test_diploma_update(self):
        BelgianHighSchoolDiplomaFactory(person=self.user.person)
        ForeignHighSchoolDiplomaFactory(person=self.user.person)
        HighSchoolDiplomaAlternativeFactory(person=self.user.person)
        # Update the high school diploma alternative
        response = self.create_high_school_diploma_alternative(self.high_school_diploma_alternative_data)
        # Check response
        json_response = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK, json_response)
        self.assertIsNone(json_response["belgian_diploma"])
        self.assertIsNone(json_response["foreign_diploma"])
        self.assertIsNotNone(json_response["high_school_diploma_alternative"])
        # Check the created object
        high_school_diploma_alternative = HighSchoolDiplomaAlternative.objects.get(person__user_id=self.user.pk)
        self.assertEqual(high_school_diploma_alternative.first_cycle_admission_exam, [UUID(self.file_uuid)])
        # Clean previous high school diplomas
        self.assertEqual(BelgianHighSchoolDiploma.objects.filter(person=self.user.person).count(), 0)
        self.assertEqual(ForeignHighSchoolDiploma.objects.filter(person=self.user.person).count(), 0)

    def test_delete_diploma(self):
        self.create_high_school_diploma_alternative(self.high_school_diploma_alternative_data)
        self.assertEqual(
            HighSchoolDiplomaAlternative.objects.get(person__user_id=self.user.pk).first_cycle_admission_exam,
            [UUID(self.file_uuid)],
        )
        self.client.put(self.admission_url, {"graduated_from_high_school": GotDiploma.NO.name})
        self.assertEqual(HighSchoolDiplomaAlternative.objects.filter(person__user_id=self.user.pk).count(), 1)
        self.client.put(self.admission_url, {"graduated_from_high_school": GotDiploma.YES.name})
        self.assertEqual(HighSchoolDiplomaAlternative.objects.filter(person__user_id=self.user.pk).count(), 0)
