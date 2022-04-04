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
from django.shortcuts import resolve_url
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, CddManagerFactory
from admission.tests.factories.secondary_studies import BelgianHighSchoolDiplomaFactory, ForeignHighSchoolDiplomaFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory
from osis_profile.models import BelgianHighSchoolDiploma, ForeignHighSchoolDiploma, Schedule
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import LanguageFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class BelgianHighSchoolDiplomaTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.agnostic_url = resolve_url("secondary-studies")
        cls.diploma_data = {
            "belgian_diploma": {
                "institute": "Test Institute",
                "academic_graduation_year": cls.academic_year.year,
                "educational_type": "TEACHING_OF_GENERAL_EDUCATION",
            }
        }
        cls.diploma_updated_data = {
            "belgian_diploma": {
                "institute": "Institute Of Test",
                "academic_graduation_year": cls.academic_year.year,
            },
        }
        cls.diploma_data_with_schedule = {
            "belgian_diploma": {
                "institute": "Test Institute",
                "academic_graduation_year": cls.academic_year.year,
                "educational_type": "TEACHING_OF_GENERAL_EDUCATION",
                "schedule": {
                    "latin": 3,
                },
            },
        }
        cls.diploma_data_educational_does_not_require_schedule = {
            "belgian_diploma": {
                "institute": "Test Institute",
                "academic_graduation_year": cls.academic_year.year,
                "educational_type": "PROFESSIONAL_EDUCATION_AND_MATURITY_EXAM",
                "schedule": {
                    "latin": 3,
                },
            },
        }
        # Users
        promoter = PromoterFactory()
        admission = DoctorateAdmissionFactory(supervision_group=promoter.process)
        cls.admission_url = resolve_url("secondary-studies", uuid=admission.uuid)
        cls.candidate_user = admission.candidate.user
        cls.candidate_user_without_admission = CandidateFactory().person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user
        cls.cdd_manager_user = CddManagerFactory(person__first_name="Jack").person.user
        cls.promoter_user = promoter.person.user
        cls.committee_member_user = CaMemberFactory(process=promoter.process).person.user

    def create_belgian_diploma(self, data):
        self.client.force_authenticate(self.candidate_user)
        return self.client.put(self.admission_url, data)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate_user_without_admission)
        methods_not_allowed = ["delete", "post", "patch"]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.agnostic_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_diploma_get_with_candidate(self):
        self.client.force_authenticate(user=self.candidate_user)
        self.create_belgian_diploma(self.diploma_data)
        response = self.client.get(self.admission_url)
        self.assertEqual(
            response.json()["belgian_diploma"]["academic_graduation_year"],
            self.diploma_data["belgian_diploma"]["academic_graduation_year"],
        )

    def test_diploma_create(self):
        self.client.force_authenticate(user=self.candidate_user)
        response = self.create_belgian_diploma(self.diploma_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        belgian_diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.candidate_user.pk)
        self.assertEqual(
            belgian_diploma.academic_graduation_year.year,
            self.diploma_data["belgian_diploma"]["academic_graduation_year"],
        )
        self.assertIsNone(belgian_diploma.result)
        self.assertIsNone(belgian_diploma.community)
        self.assertEqual(belgian_diploma.educational_type, self.diploma_data["belgian_diploma"]["educational_type"])
        self.assertEqual(belgian_diploma.educational_other, "")
        self.assertEqual(belgian_diploma.institute, self.diploma_data["belgian_diploma"]["institute"])
        self.assertEqual(belgian_diploma.other_institute, "")
        self.assertIsNone(belgian_diploma.schedule)
        foreign_diploma = ForeignHighSchoolDiploma.objects.filter(person__user_id=self.candidate_user.pk)
        self.assertEqual(foreign_diploma.count(), 0)

    def test_diploma_update_with_candidate(self):
        self.create_belgian_diploma(self.diploma_data)
        response = self.client.put(self.admission_url, {
            "belgian_diploma": {
                "institute": "Institute Of Test",
                "academic_graduation_year": self.academic_year.year,
            },
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.candidate_user.pk)
        self.assertEqual(diploma.institute, "Institute Of Test")

    def test_diploma_update_by_belgian_diploma(self):
        ForeignHighSchoolDiplomaFactory(person=self.candidate_user.person)
        self.assertEqual(ForeignHighSchoolDiploma.objects.count(), 1)
        response = self.create_belgian_diploma(self.diploma_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertIsNone(response.json()["foreign_diploma"])
        self.assertIsNotNone(response.json()["belgian_diploma"])
        self.assertEqual(ForeignHighSchoolDiploma.objects.count(), 0)
        diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.candidate_user.pk)
        self.assertEqual(diploma.institute, "Test Institute")

    def test_diploma_create_with_schedule(self):
        response = self.create_belgian_diploma(self.diploma_data_with_schedule)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.candidate_user.pk)
        self.assertEqual(diploma.institute, "Test Institute")
        self.assertIsNotNone(diploma.schedule)
        self.assertEqual(diploma.schedule.latin, 3)

    def test_diploma_create_with_schedule_without_correct_educational_type(self):
        response = self.create_belgian_diploma(self.diploma_data_educational_does_not_require_schedule)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.candidate_user.pk)
        self.assertEqual(diploma.institute, "Test Institute")
        self.assertIsNone(diploma.schedule)

    def test_diploma_create_without_required_schedule_deletes_it(self):
        response = self.create_belgian_diploma(self.diploma_data_with_schedule)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        response = self.create_belgian_diploma(self.diploma_data)
        self.assertIsNone(response.json()["belgian_diploma"]["schedule"])
        diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.candidate_user.pk)
        self.assertIsNone(diploma.schedule)
        self.assertEqual(Schedule.objects.count(), 0)

    def test_delete_diploma(self):
        self.create_belgian_diploma(self.diploma_data)
        self.create_belgian_diploma({})
        response = self.client.get(self.admission_url)
        self.assertEqual(response.json(), {'belgian_diploma': None, 'foreign_diploma': None})

    def test_delete_diploma_with_schedule(self):
        self.create_belgian_diploma(self.diploma_data_with_schedule)
        self.create_belgian_diploma({})
        response = self.client.get(self.admission_url)
        self.assertEqual(response.json(), {'belgian_diploma': None, 'foreign_diploma': None})

    def test_diploma_get_with_no_role_user(self):
        self.create_belgian_diploma(self.diploma_data)
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_diploma_update_with_no_role_user(self):
        self.create_belgian_diploma(self.diploma_data)
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.put(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.put(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_diploma_get_with_cdd_manager_user(self):
        self.create_belgian_diploma(self.diploma_data)
        self.client.force_authenticate(user=self.cdd_manager_user)
        response = self.client.get(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_diploma_update_with_cdd_manager_user(self):
        self.create_belgian_diploma(self.diploma_data)
        self.client.force_authenticate(user=self.cdd_manager_user)
        response = self.client.put(self.agnostic_url, self.diploma_updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.put(self.admission_url, self.diploma_updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_diploma_get_with_promoter_user(self):
        self.create_belgian_diploma(self.diploma_data)
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_diploma_update_with_promoter_user(self):
        self.create_belgian_diploma(self.diploma_data)
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.put(self.admission_url, self.diploma_updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_diploma_get_with_cdd_member_user(self):
        self.create_belgian_diploma(self.diploma_data)
        self.client.force_authenticate(user=self.cdd_manager_user)
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class ForeignHighSchoolDiplomaTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CandidateFactory().person.user
        cls.url = reverse("secondary-studies")
        cls.academic_year = AcademicYearFactory(current=True)
        cls.language = LanguageFactory(code="FR")
        cls.country = CountryFactory(iso_code="FR")
        cls.foreign_diploma_data = {
            "foreign_diploma": {
                "other_linguistic_regime": "Français",
                "academic_graduation_year": cls.academic_year.year,
                "linguistic_regime": "FR",
                "country": "FR",
            },
        }

    def create_foreign_diploma(self, data):
        self.client.force_authenticate(self.user)
        return self.client.put(self.url, data)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.user)
        methods_not_allowed = ["delete", "post", "patch"]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
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

    def test_diploma_update_by_foreign_diploma(self):
        BelgianHighSchoolDiplomaFactory(person=self.user.person)
        response = self.create_foreign_diploma(self.foreign_diploma_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertIsNone(response.json()["belgian_diploma"])
        self.assertIsNotNone(response.json()["foreign_diploma"])
        diploma = ForeignHighSchoolDiploma.objects.get(person__user_id=self.user.pk)
        self.assertEqual(diploma.other_linguistic_regime, "Français")

    def test_diploma_without_schedule_update_by_foreign_diploma(self):
        BelgianHighSchoolDiplomaFactory(person=self.user.person, schedule=None)
        response = self.create_foreign_diploma(self.foreign_diploma_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertIsNone(response.json()["belgian_diploma"])
        self.assertIsNotNone(response.json()["foreign_diploma"])
        diploma = ForeignHighSchoolDiploma.objects.get(person__user_id=self.user.pk)
        self.assertEqual(diploma.other_linguistic_regime, "Français")

    def test_delete_diploma(self):
        self.create_foreign_diploma(self.foreign_diploma_data)
        self.assertEqual(
            ForeignHighSchoolDiploma.objects.get(person__user_id=self.user.pk).other_linguistic_regime,
            "Français",
        )
        self.client.put(self.url, {})
        response = self.client.get(self.url)
        self.assertEqual(response.json(), {'belgian_diploma': None, 'foreign_diploma': None})
        self.assertEqual(ForeignHighSchoolDiploma.objects.filter(person__user_id=self.user.pk).count(), 0)
