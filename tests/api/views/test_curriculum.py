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
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import CurriculumYearFactory, ExperienceFactory
from base.tests.factories.academic_year import AcademicYearFactory
from osis_profile.models import CurriculumYear


class CurriculumTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.academic_year = AcademicYearFactory(year=2000)
        cls.curriculum_year = CurriculumYearFactory(academic_graduation_year=cls.current_academic_year)
        cls.admission = DoctorateAdmissionFactory()
        cls.valuated_experience = ExperienceFactory(curriculum_year=cls.curriculum_year, valuated_from=cls.admission)
        cls.user = cls.curriculum_year.person.user
        cls.url = reverse("admission_api_v1:curriculum")
        cls.curriculum_year_create_data = {
            "curriculum_years": [
                {
                    "academic_graduation_year": cls.academic_year.year,
                    "experiences": [
                        {
                            "course_type": "BELGIAN_UNIVERSITY",
                        },
                        {
                            "course_type": "FOREIGN_UNIVERSITY",
                        },
                    ],
                },
            ],
        }
        cls.curriculum_year_update_data = {
            "curriculum_years": [
                {
                    "academic_graduation_year": cls.current_academic_year.year,
                    "experiences": [
                        {
                            "course_type": "BELGIAN_NON_UNIVERSITY_HIGHER_EDUCATION",
                        },
                        {
                            "course_type": "FOREIGN_NON_UNIVERSITY_HIGHER_EDUCATION",
                        },
                    ],
                },
            ],
        }
        cls.curriculum_year_without_experiences_data = {
            "curriculum_years": [
                {
                    "academic_graduation_year": cls.current_academic_year.year,
                    "experiences": [],
                },
            ],
        }

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

    def test_curriculum_get(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.json()["curriculum_years"]), 1)
        self.assertEqual(response.json()["curriculum_years"][0]["academic_graduation_year"], 2021)
        self.assertEqual(len(response.json()["curriculum_years"][0]["experiences"]), 1)
        self.assertEqual(
            response.json()["curriculum_years"][0]["experiences"][0]["course_type"],
            self.valuated_experience.course_type,
        )

    def test_curriculum_create(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, self.curriculum_year_create_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        curriculum_years = CurriculumYear.objects.filter(person=self.user.person)
        self.assertEqual(curriculum_years.count(), 2)
        curriculum = curriculum_years.get(academic_graduation_year=self.academic_year)
        self.assertEqual(curriculum.experiences.count(), 2)
        curriculum_course_types = curriculum.experiences.values_list("course_type", flat=True)
        self.assertIn("BELGIAN_UNIVERSITY", curriculum_course_types)
        self.assertIn("FOREIGN_UNIVERSITY", curriculum_course_types)
        self.assertEqual(curriculum.academic_graduation_year, self.academic_year)

    def test_curriculum_update(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, self.curriculum_year_update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        curriculum_years = CurriculumYear.objects.filter(person=self.user.person)
        self.assertEqual(curriculum_years.count(), 1)
        curriculum = curriculum_years.get(academic_graduation_year=self.current_academic_year)
        self.assertEqual(curriculum.experiences.count(), 3)
        curriculum_course_types = curriculum.experiences.values_list("course_type", flat=True)
        self.assertIn("BELGIAN_NON_UNIVERSITY_HIGHER_EDUCATION", curriculum_course_types)
        self.assertIn("FOREIGN_NON_UNIVERSITY_HIGHER_EDUCATION", curriculum_course_types)
        self.assertIn(self.valuated_experience.course_type, curriculum_course_types)
        self.assertEqual(curriculum.academic_graduation_year, self.current_academic_year)

    def test_update_curriculum_experiences_wont_delete_valuated_ones(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, self.curriculum_year_without_experiences_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        curriculum_years = CurriculumYear.objects.filter(person=self.user.person)
        self.assertEqual(curriculum_years.count(), 1)  # only the initial valuated experience must stay
