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
from base.tests.factories.education_group_year import EducationGroupYearFactory
from osis_profile.models import Experience, CurriculumYear
from osis_profile.models.enums.curriculum import ExperienceType
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import LanguageFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class CurriculumTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Mocked data
        cls.admission = DoctorateAdmissionFactory()
        cls.other_admission = DoctorateAdmissionFactory()
        cls.country = CountryFactory()
        cls.created_data = {
            'country': cls.country.iso_code,
            'type': ExperienceType.HIGHER_EDUCATION.name,
        }
        cls.user = cls.admission.candidate.user
        cls.other_user = cls.other_admission.candidate.user

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

        # Mock data
        second_curriculum_year = CurriculumYearFactory(
            academic_year=AcademicYearFactory(year=2022),
            person=self.admission.candidate,
        )
        first_curriculum_year = CurriculumYearFactory(
            academic_year=AcademicYearFactory(year=2021),
            person=self.admission.candidate,
        )
        program = EducationGroupYearFactory()
        linguistic_regime = LanguageFactory()
        second_experience = ExperienceFactory(
            curriculum_year=second_curriculum_year,
            country=self.country,
            type=ExperienceType.OTHER_ACTIVITY.name,
            program=program,
            linguistic_regime=linguistic_regime,
        )
        first_experience = ExperienceFactory(
            curriculum_year=first_curriculum_year,
            country=self.country,
            type=ExperienceType.HIGHER_EDUCATION.name,
        )

        response = self.client.get(self.agnostic_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        # The results are sorted in descending chronological order
        self.assertEqual(response.json()[0].get('uuid'), str(second_experience.uuid))
        self.assertEqual(response.json()[1].get('uuid'), str(first_experience.uuid))
        self.assertEqual(response.json()[0].get('type'), second_experience.type)
        self.assertEqual(response.json()[0].get('country'), self.country.iso_code)
        self.assertEqual(response.json()[0].get('linguistic_regime'), linguistic_regime.code)

    def test_add_experience_via_curriculum_year(self):
        self.client.force_authenticate(self.user)

        # Mock data
        curriculum_year = CurriculumYearFactory(
            academic_year=AcademicYearFactory(year=2022),
            person=self.admission.candidate,
        )

        # Directly specify the year of the experience via the 'curriculum_year' property
        response = self.client.post(self.agnostic_url, data={
            'curriculum_year': curriculum_year.id,
            **self.created_data,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json().get('type'), self.created_data['type'])
        self.assertEqual(response.json().get('country'), self.country.iso_code)
        self.assertEqual(response.json().get('curriculum_year'), {
            'academic_year': 2022,
            'id': curriculum_year.id,
        })

    def test_add_experience_via_academic_year_and_related_to_existing_cv_year(self):
        self.client.force_authenticate(self.user)

        # Mock data
        curriculum_year = CurriculumYearFactory(
            academic_year=AcademicYearFactory(year=2022),
            person=self.admission.candidate,
        )

        # Specify the year of the experience via the 'academic_year' property
        response = self.client.post(self.agnostic_url, data={
            'academic_year': curriculum_year.academic_year.year,
            **self.created_data,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json().get('curriculum_year'), {
            'academic_year': 2022,
            'id': curriculum_year.id,
        })

    def test_add_experience_via_academic_year_and_related_to_a_non_existing_cv_year(self):
        self.client.force_authenticate(self.user)

        # Mock data
        academic_year = AcademicYearFactory(year=2022)

        # Specify the year of the experience via the 'academic_year' property
        response = self.client.post(self.agnostic_url, data={
            'academic_year': academic_year.year,
            **self.created_data,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # A new CV year has been created
        created_curriculum_year = CurriculumYear.objects.filter(
            person=self.admission.candidate,
            academic_year=academic_year,
        )
        self.assertEqual(len(created_curriculum_year), 1)
        self.assertEqual(response.json().get('curriculum_year'), {
            'academic_year': 2022,
            'id': created_curriculum_year[0].id
        })

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

        # Mock data
        curriculum_year = CurriculumYearFactory(
            academic_year=AcademicYearFactory(year=2022),
            person=self.admission.candidate,
        )
        experience = ExperienceFactory(
            curriculum_year=curriculum_year,
            country=self.country,
            type=ExperienceType.HIGHER_EDUCATION.name,
        )

        detail_url = resolve_url('curriculum', xp=experience.uuid)
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('uuid'), str(experience.uuid))
        self.assertEqual(response.json().get('type'), experience.type)
        self.assertEqual(response.json().get('country'), self.country.iso_code)

    def test_get_one_experience_other_candidate(self):
        self.client.force_authenticate(self.other_user)

        # Mock data
        curriculum_year = CurriculumYearFactory(
            academic_year=AcademicYearFactory(year=2022),
            person=self.admission.candidate,
        )
        experience = ExperienceFactory(
            curriculum_year=curriculum_year,
            country=self.country,
            type=ExperienceType.HIGHER_EDUCATION.name,
        )

        detail_url = resolve_url('curriculum', xp=experience.uuid)
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_experience(self):
        self.client.force_authenticate(self.user)

        # Mock data
        first_curriculum_year = CurriculumYearFactory(
            academic_year=AcademicYearFactory(year=2021),
            person=self.admission.candidate,
        )
        second_curriculum_year = CurriculumYearFactory(
            academic_year=AcademicYearFactory(year=2022),
            person=self.admission.candidate,
        )
        experience = ExperienceFactory(
            curriculum_year=first_curriculum_year,
            country=self.country,
            type=ExperienceType.HIGHER_EDUCATION.name,
        )

        update_url = resolve_url('curriculum', xp=experience.uuid)
        response = self.client.put(update_url, data={
            'curriculum_year': second_curriculum_year.id,
            'country': self.country.iso_code,
            'type': ExperienceType.OTHER_ACTIVITY.name,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('uuid'), str(experience.uuid))
        self.assertEqual(response.json().get('type'), ExperienceType.OTHER_ACTIVITY.name)
        self.assertEqual(response.json().get('curriculum_year'), {
            'id': second_curriculum_year.id,
            'academic_year': 2022,
        })
        self.assertEqual(response.json().get('country'), self.country.iso_code)

    def test_update_valuated_experience(self):
        self.client.force_authenticate(self.user)

        # Mock data
        curriculum_year = CurriculumYearFactory(
            academic_year=AcademicYearFactory(year=2021),
            person=self.admission.candidate,
        )
        experience = ExperienceFactory(
            curriculum_year=curriculum_year,
            country=self.country,
            type=ExperienceType.HIGHER_EDUCATION.name,
        )
        self.admission.valuated_experiences.add(experience)

        update_url = resolve_url('curriculum', xp=experience.uuid)
        response = self.client.put(update_url, data={
            'curriculum_year': curriculum_year.id,
            'country': self.country.iso_code,
            'type': ExperienceType.OTHER_ACTIVITY.name,
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_experience(self):
        self.client.force_authenticate(self.user)

        # Mock data
        curriculum_year = CurriculumYearFactory(
            academic_year=AcademicYearFactory(year=2021),
            person=self.admission.candidate,
        )
        experience = ExperienceFactory(
            curriculum_year=curriculum_year,
            country=self.country,
            type=ExperienceType.HIGHER_EDUCATION.name,
        )

        self.assertTrue(Experience.objects.filter(pk=experience.id).exists())

        update_url = resolve_url('curriculum', xp=experience.uuid)
        response = self.client.delete(update_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Experience.objects.filter(pk=experience.id).exists())
        self.assertFalse(CurriculumYear.objects.filter(pk=curriculum_year.id).exists())

    def test_delete_valuated_experience(self):
        self.client.force_authenticate(self.user)

        # Mock data
        curriculum_year = CurriculumYearFactory(
            academic_year=AcademicYearFactory(year=2021),
            person=self.admission.candidate,
        )
        experience = ExperienceFactory(
            curriculum_year=curriculum_year,
            country=self.country,
            type=ExperienceType.HIGHER_EDUCATION.name,
        )
        self.admission.valuated_experiences.add(experience)

        self.assertTrue(Experience.objects.filter(pk=experience.id).exists())

        update_url = resolve_url('curriculum', xp=experience.uuid)
        response = self.client.delete(update_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Experience.objects.filter(pk=experience.id).exists())
