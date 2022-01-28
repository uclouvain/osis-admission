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
from django.shortcuts import resolve_url
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import CurriculumYearFactory, ExperienceFactory
from base.tests.factories.academic_year import AcademicYearFactory
from osis_profile.models import Experience, CurriculumYear
from osis_profile.models.enums.curriculum import ExperienceTypes
from reference.tests.factories.country import CountryFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class CurriculumTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Mocked data
        cls.admission = DoctorateAdmissionFactory()
        cls.other_admission = DoctorateAdmissionFactory()
        cls.country = CountryFactory()
        cls.first_academic_year = AcademicYearFactory(year=2000)
        cls.second_academic_year = AcademicYearFactory(year=2001)
        cls.other_academic_year = AcademicYearFactory(year=2005)
        cls.first_curriculum_year = CurriculumYearFactory(
            academic_year=cls.first_academic_year,
            person=cls.admission.candidate,
        )
        cls.second_curriculum_year = CurriculumYearFactory(
            academic_year=cls.second_academic_year,
            person=cls.admission.candidate,
        )
        cls.second_experience = ExperienceFactory(
            curriculum_year=cls.second_curriculum_year,
            country=cls.country,
            type=ExperienceTypes.OTHER_OCCUPATIONS.name,
        )
        cls.first_experience = ExperienceFactory(
            curriculum_year=cls.first_curriculum_year,
            country=cls.country,
            type=ExperienceTypes.HIGHER_EDUCATION.name,
        )
        cls.user = cls.admission.candidate.user
        cls.other_user = cls.other_admission.candidate.user

        # Request data
        cls.created_data = {
            'country': cls.country.pk,
            'type': ExperienceTypes.HIGHER_EDUCATION.name,
        }

        # Targeted urls
        cls.agnostic_url = resolve_url('curriculum')
        cls.admission_url = resolve_url('curriculum', uuid=cls.admission.uuid)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_other_candidate_assert_not_authorized(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.user)

        response = getattr(self.client, 'patch')(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = getattr(self.client, 'patch')(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_experiences_candidate(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.agnostic_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0].get('id'), self.first_experience.id)
        self.assertEqual(response.json()[0].get('type'), self.first_experience.type)
        self.assertEqual(response.json()[1].get('id'), self.second_experience.id)
        self.assertEqual(response.json()[1].get('type'), self.second_experience.type)

    def test_add_experience_via_curriculum_year(self):
        self.client.force_authenticate(self.user)

        # Directly specify the year of the experience via the 'curriculum_year' property
        response = self.client.post(self.agnostic_url, data={
            'curriculum_year': self.first_curriculum_year.id,
            **self.created_data,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json().get('type'), self.created_data['type'])
        self.assertEqual(response.json().get('country'), self.created_data['country'])
        self.assertEqual(response.json().get('curriculum_year'), self.first_curriculum_year.id)

    def test_add_experience_via_academic_year_and_related_to_existing_cv_year(self):
        self.client.force_authenticate(self.user)

        # Specify the year of the experience via the 'academic_year' property
        response = self.client.post(self.agnostic_url, data={
            'academic_year': self.first_academic_year.year,
            **self.created_data,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json().get('type'), self.created_data['type'])
        self.assertEqual(response.json().get('country'), self.created_data['country'])
        self.assertEqual(response.json().get('curriculum_year'), self.first_curriculum_year.id)

    def test_add_experience_via_academic_year_and_related_to_a_non_existing_cv_year(self):
        self.client.force_authenticate(self.user)

        # There is no experience specified for this user for this academic year
        self.assertFalse(CurriculumYear.objects.filter(
            person=self.admission.candidate,
            academic_year=self.other_academic_year,
        ).exists())

        # Specify the year of the experience via the 'academic_year' property
        response = self.client.post(self.agnostic_url, data={
            'academic_year': self.other_academic_year.year,
            **self.created_data,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json().get('type'), self.created_data['type'])
        self.assertEqual(response.json().get('country'), self.created_data['country'])
        # A new CV year has been created
        created_curriculum_year = CurriculumYear.objects.filter(
            person=self.admission.candidate,
            academic_year=self.other_academic_year,
        )
        self.assertEqual(len(created_curriculum_year), 1)
        self.assertEqual(response.json().get('curriculum_year'), created_curriculum_year[0].id)

    def test_add_experience_without_related_year(self):
        self.client.force_authenticate(self.user)

        # Don't specify the year of the experience
        response = self.client.post(self.agnostic_url, data={
            **self.created_data,
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.json())

    def test_get_one_experience_candidate(self):
        self.client.force_authenticate(self.user)
        detail_url = resolve_url('curriculum', xp=self.first_experience.id)

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('id'), self.first_experience.id)
        self.assertEqual(response.json().get('type'), self.first_experience.type)

    def test_update_experience(self):
        self.client.force_authenticate(self.user)

        new_experience = ExperienceFactory(
            curriculum_year=self.first_curriculum_year,
            country=self.country,
            type=ExperienceTypes.HIGHER_EDUCATION.name,
        )

        update_url = resolve_url('curriculum', xp=new_experience.id)

        response = self.client.put(update_url, data={
            'curriculum_year': self.second_curriculum_year.id,
            'country': new_experience.country.id,
            'type': ExperienceTypes.HIGHER_EDUCATION.name,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('id'), new_experience.id)
        self.assertEqual(response.json().get('type'), ExperienceTypes.HIGHER_EDUCATION.name)
        self.assertEqual(response.json().get('country'), self.country.id)
        # 'curriculum_year' is a read-only property then it is not updated
        self.assertEqual(response.json().get('curriculum_year'), self.first_curriculum_year.id)

    def test_update_valuated_experience(self):
        self.client.force_authenticate(self.user)

        new_experience = ExperienceFactory(
            curriculum_year=self.first_curriculum_year,
            country=self.country,
            type=ExperienceTypes.HIGHER_EDUCATION.name,
            valuated_from=self.admission,
        )

        update_url = resolve_url('curriculum', xp=new_experience.id)
        response = self.client.put(update_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_experience(self):
        self.client.force_authenticate(self.user)

        new_experience = ExperienceFactory(
            curriculum_year=self.first_curriculum_year,
            country=self.country,
            type=ExperienceTypes.HIGHER_EDUCATION.name,
        )

        self.assertEqual(Experience.objects.filter(pk=new_experience.id).count(), 1)

        update_url = resolve_url('curriculum', xp=new_experience.id)
        response = self.client.delete(update_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Experience.objects.filter(pk=new_experience.id).count(), 0)

    def test_delete_experience_and_related_curriculum_year(self):
        self.client.force_authenticate(self.user)

        new_curriculum_year = CurriculumYearFactory(
            person=self.admission.candidate,
            academic_year=self.other_academic_year,
        )
        new_experience = ExperienceFactory(
            curriculum_year=new_curriculum_year,
            country=self.country,
            type=ExperienceTypes.HIGHER_EDUCATION.name,
        )

        self.assertEqual(Experience.objects.filter(pk=new_experience.id).count(), 1)
        self.assertEqual(CurriculumYear.objects.filter(pk=new_curriculum_year.id).count(), 1)

        update_url = resolve_url('curriculum', xp=new_experience.id)
        response = self.client.delete(update_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Experience.objects.filter(pk=new_experience.id).count(), 0)
        self.assertEqual(CurriculumYear.objects.filter(pk=new_curriculum_year.id).count(), 0)
