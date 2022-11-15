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
import datetime
from unittest.mock import ANY

import mock
from django.shortcuts import resolve_url
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import (
    ProfessionalExperienceFactory,
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
)
from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.secondary_studies import BelgianHighSchoolDiplomaFactory, ForeignHighSchoolDiplomaFactory
from base.models.enums.teaching_type import TeachingTypeEnum
from base.tests.factories.academic_year import AcademicYearFactory
from osis_profile.models import ProfessionalExperience, EducationalExperience, EducationalExperienceYear
from osis_profile.models.enums.curriculum import (
    ActivityType,
    ActivitySector,
    Result,
    EvaluationSystem,
    TranscriptType,
    Grade,
)
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.diploma_title import DiplomaTitleFactory
from reference.tests.factories.language import LanguageFactory
from reference.tests.factories.superior_non_university import SuperiorNonUniversityFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class GetCurriculumTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Mocked data
        cls.admission = DoctorateAdmissionFactory()
        cls.other_admission = DoctorateAdmissionFactory()
        cls.country = CountryFactory()
        cls.academic_year_2018 = AcademicYearFactory(year=2018)
        cls.academic_year_2020 = AcademicYearFactory(year=2020)
        cls.user = cls.admission.candidate.user
        cls.other_user = cls.other_admission.candidate.user
        cls.user_without_admission = CandidateFactory().person.user

        cls.professional_experiences = [
            ProfessionalExperienceFactory(
                person=cls.admission.candidate,
                institute_name='First institute',
                start_date=datetime.date(2020, 1, 1),
                end_date=datetime.date(2021, 1, 1),
                type=ActivityType.WORK.name,
                role='Librarian',
                sector=ActivitySector.PUBLIC.name,
                activity='Work - activity',
            ),
            ProfessionalExperienceFactory(
                person=cls.admission.candidate,
                institute_name='Second institute',
                start_date=datetime.date(2020, 1, 1),
                end_date=datetime.date(2020, 9, 1),
                type=ActivityType.WORK.name,
                role='Librarian',
                sector=ActivitySector.PUBLIC.name,
                activity='Work - activity',
            ),
        ]

        cls.educational_experiences = [
            EducationalExperienceFactory(
                person=cls.admission.candidate,
                country=cls.country,
                institute_name='UCL',
                education_name='Computer science',
                obtained_diploma=False,
            ),
        ]

        EducationalExperienceYearFactory(
            educational_experience=cls.educational_experiences[0],
            academic_year=cls.academic_year_2020,
            result=Result.SUCCESS.name,
        )
        cls.today_date = datetime.date(2020, 11, 1)
        cls.today_datetime = datetime.datetime(2020, 11, 1)

        # Targeted urls
        cls.agnostic_url = resolve_url('curriculum')
        cls.admission_url = resolve_url('curriculum', uuid=cls.admission.uuid)

    def setUp(self) -> None:
        # Mock datetime to return the 2020 year as the current year
        patcher = mock.patch('base.models.academic_year.timezone')
        self.addCleanup(patcher.stop)
        self.mock_foo = patcher.start()
        self.mock_foo.now.return_value = self.today_datetime

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

    def test_get_curriculum(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.admission_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        response = response.json()
        self.assertEqual(response.get('file'), {'curriculum': []})
        self.assertEqual(
            response.get('minimal_year'),
            1 + self.today_date.year - IProfilCandidatTranslator.NB_MAX_ANNEES_CV_REQUISES,
        )
        self.assertEqual(
            response.get('professional_experiences'),
            [
                {
                    'uuid': str(self.professional_experiences[0].uuid),
                    'institute_name': 'First institute',
                    'start_date': '2020-01-01',
                    'end_date': '2021-01-01',
                    'type': ActivityType.WORK.name,
                    'valuated_from_admission': [],
                },
                {
                    'uuid': str(self.professional_experiences[1].uuid),
                    'institute_name': 'Second institute',
                    'start_date': '2020-01-01',
                    'end_date': '2020-09-01',
                    'type': ActivityType.WORK.name,
                    'valuated_from_admission': [],
                },
            ],
        )
        self.assertEqual(
            response.get('educational_experiences'),
            [
                {
                    'uuid': ANY,
                    'institute_name': 'UCL',
                    'institute': None,
                    'program': None,
                    'education_name': 'Computer science',
                    'educationalexperienceyear_set': [{'academic_year': 2020}],
                    'valuated_from_admission': [],
                }
            ],
        )

    def test_get_curriculum_minimal_year_with_last_registration(self):
        self.client.force_authenticate(user=self.user)

        self.user.person.last_registration_year = self.academic_year_2018
        self.user.person.save()
        response = self.client.get(self.admission_url)

        # Check response data
        response = response.json()
        self.assertEqual(
            response.get('minimal_year'),
            self.academic_year_2018.year + 1,
        )

        self.user.person.last_registration_year = None
        self.user.person.save()

    def test_get_curriculum_minimal_year_with_belgian_diploma(self):
        self.client.force_authenticate(user=self.user)

        belgian_diploma = BelgianHighSchoolDiplomaFactory(
            person=self.user.person,
            academic_graduation_year=self.academic_year_2018,
        )

        response = self.client.get(self.admission_url)

        # Check response data
        response = response.json()
        self.assertEqual(
            response.get('minimal_year'),
            self.academic_year_2018.year + 1,
        )

        belgian_diploma.delete()

    def test_get_curriculum_minimal_year_with_foreign_diploma(self):
        self.client.force_authenticate(user=self.user)

        foreign_diploma = ForeignHighSchoolDiplomaFactory(
            person=self.user.person,
            academic_graduation_year=self.academic_year_2018,
        )

        response = self.client.get(self.admission_url)

        # Check response data
        response = response.json()
        self.assertEqual(
            response.get('minimal_year'),
            self.academic_year_2018.year + 1,
        )

        foreign_diploma.delete()


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class ProfessionalExperienceTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Mocked data
        cls.admission = DoctorateAdmissionFactory()
        cls.other_admission = DoctorateAdmissionFactory()

        cls.academic_year_2018 = AcademicYearFactory(year=2018)
        cls.academic_year_2020 = AcademicYearFactory(year=2020)
        cls.user = cls.admission.candidate.user
        cls.other_user = cls.other_admission.candidate.user
        cls.user_without_admission = CandidateFactory().person.user

        cls.today_date = datetime.date(2020, 11, 1)
        cls.today_datetime = datetime.datetime(2020, 11, 1)

        # Targeted urls
        cls.agnostic_url = resolve_url('cv_professional_experiences-list')
        cls.admission_url = resolve_url('cv_professional_experiences-list', uuid=cls.admission.uuid)

    def setUp(self) -> None:
        # Mock datetime to return the 2020 year as the current year
        patcher = mock.patch('base.models.academic_year.timezone')
        self.addCleanup(patcher.stop)
        self.mock_foo = patcher.start()
        self.mock_foo.now.return_value = self.today_datetime

        self.professional_experience = ProfessionalExperienceFactory(
            person=self.admission.candidate,
            institute_name='First institute',
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2021, 1, 1),
            type=ActivityType.WORK.name,
            role='Librarian',
            sector=ActivitySector.PUBLIC.name,
            activity='Work - activity',
        )

        self.admission_details_url = resolve_url(
            'cv_professional_experiences-detail',
            uuid=self.admission.uuid,
            experience_id=self.professional_experience.uuid,
        )

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

        methods_not_allowed_on_detail = [
            'patch',
            'post',
        ]

        methods_not_allowed_on_listing_create = [
            'patch',
            'put',
            'get',
            'delete',
        ]

        for method in methods_not_allowed_on_detail:
            response = getattr(self.client, method)(self.admission_details_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        for method in methods_not_allowed_on_listing_create:
            response = getattr(self.client, method)(self.admission_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_professional_experience(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.admission_details_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        self.assertEqual(
            response.json(),
            {
                'uuid': str(self.professional_experience.uuid),
                'institute_name': 'First institute',
                'start_date': '2020-01-01',
                'end_date': '2021-01-01',
                'type': ActivityType.WORK.name,
                'certificate': [],
                'role': 'Librarian',
                'sector': ActivitySector.PUBLIC.name,
                'activity': 'Work - activity',
                'valuated_from_admission': [],
            },
        )

    def test_post_professional_experience(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.admission_url,
            data={
                'institute_name': 'Second institute',
                'start_date': '2019-01-01',
                'end_date': '2020-01-01',
                'type': ActivityType.VOLUNTEERING.name,
                'certificate': [],
                'role': 'Helper',
                'sector': ActivitySector.PRIVATE.name,
                'activity': 'Volunteering - activity',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        json_response = response.json()

        # Check response data
        self.assertEqual(
            json_response,
            {
                'uuid': ANY,
                'institute_name': 'Second institute',
                'start_date': '2019-01-01',
                'end_date': '2020-01-01',
                'type': ActivityType.VOLUNTEERING.name,
                'certificate': [],
                'role': 'Helper',
                'sector': ActivitySector.PRIVATE.name,
                'activity': 'Volunteering - activity',
                'valuated_from_admission': [],
            },
        )

        experience: ProfessionalExperience = ProfessionalExperience.objects.filter(
            uuid=json_response.get('uuid'),
        ).first()

        self.assertIsNotNone(experience)

        self.assertEqual(experience.person, self.user.person)
        self.assertEqual(experience.institute_name, 'Second institute')
        self.assertEqual(experience.start_date, datetime.date(2019, 1, 1))
        self.assertEqual(experience.end_date, datetime.date(2020, 1, 1))
        self.assertEqual(experience.type, ActivityType.VOLUNTEERING.name)
        self.assertEqual(experience.certificate, [])
        self.assertEqual(experience.role, 'Helper')
        self.assertEqual(experience.sector, ActivitySector.PRIVATE.name)
        self.assertEqual(experience.activity, 'Volunteering - activity')

    def test_put_professional_experience(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            self.admission_details_url,
            data={
                'start_date': '2020-01-01',
                'end_date': '2021-01-01',
                'type': ActivityType.WORK.name,
                'sector': ActivitySector.PRIVATE.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()

        # Check response data
        self.assertEqual(json_response.get('sector'), ActivitySector.PRIVATE.name),

        experience = ProfessionalExperience.objects.get(
            uuid=self.professional_experience.uuid,
        )

        self.assertEqual(experience.sector, ActivitySector.PRIVATE.name)

    def test_put_valuated_professional_experience_is_forbidden(self):
        self.client.force_authenticate(user=self.user)

        self.professional_experience.valuated_from_admission.set([self.admission])

        response = self.client.put(
            self.admission_details_url,
            data={
                'start_date': '2020-01-01',
                'end_date': '2021-01-01',
                'type': ActivityType.WORK.name,
                'sector': ActivitySector.PRIVATE.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_professional_experience(self):
        self.client.force_authenticate(user=self.user)

        self.assertTrue(
            ProfessionalExperience.objects.filter(
                uuid=self.professional_experience.uuid,
            ).exists()
        )

        self.client.delete(self.admission_details_url)

        self.assertFalse(
            ProfessionalExperience.objects.filter(
                uuid=self.professional_experience.uuid,
            ).exists()
        )

    def test_delete_valuated_professional_experience_is_forbidden(self):
        self.client.force_authenticate(user=self.user)

        self.professional_experience.valuated_from_admission.set([self.admission])

        response = self.client.delete(self.admission_details_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class EducationalExperienceTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Mocked data
        cls.admission = DoctorateAdmissionFactory()
        cls.other_admission = DoctorateAdmissionFactory()

        cls.academic_year_2018 = AcademicYearFactory(year=2018)
        cls.academic_year_2019 = AcademicYearFactory(year=2019)
        cls.academic_year_2020 = AcademicYearFactory(year=2020)
        cls.user = cls.admission.candidate.user
        cls.other_user = cls.other_admission.candidate.user
        cls.user_without_admission = CandidateFactory().person.user

        cls.diploma = DiplomaTitleFactory()
        cls.linguistic_regime = LanguageFactory()
        cls.institute = SuperiorNonUniversityFactory(teaching_type=TeachingTypeEnum.SOCIAL_PROMOTION.name)

        cls.today_date = datetime.date(2020, 11, 1)
        cls.today_datetime = datetime.datetime(2020, 11, 1)

        cls.country = CountryFactory()

        # Targeted urls
        cls.agnostic_url = resolve_url('cv_educational_experiences-list')
        cls.admission_url = resolve_url('cv_educational_experiences-list', uuid=cls.admission.uuid)

    def setUp(self) -> None:
        # Mock datetime to return the 2020 year as the current year
        patcher = mock.patch('base.models.academic_year.timezone')
        self.addCleanup(patcher.stop)
        self.mock_foo = patcher.start()
        self.mock_foo.now.return_value = self.today_datetime

        self.educational_experience = EducationalExperienceFactory(
            person=self.admission.candidate,
            country=self.country,
            institute=None,
            institute_name='UCL',
            institute_address='Place de l\'Université',
            program=self.diploma,
            education_name='Computer science',
            study_system='',
            evaluation_type=EvaluationSystem.ECTS_CREDITS.name,
            linguistic_regime=self.linguistic_regime,
            transcript_type=TranscriptType.ONE_FOR_ALL_YEARS.name,
            obtained_diploma=True,
            obtained_grade=Grade.GREAT_DISTINCTION.name,
            graduate_degree=[],
            graduate_degree_translation=[],
            transcript=[],
            transcript_translation=[],
            bachelor_cycle_continuation=True,
            diploma_equivalence=[],
            rank_in_diploma='10 on 100',
            expected_graduation_date=datetime.date(2022, 8, 30),
            dissertation_title='Title',
            dissertation_score='15/20',
            dissertation_summary=[],
        )

        EducationalExperienceYearFactory(
            educational_experience=self.educational_experience,
            academic_year=self.academic_year_2020,
            result=Result.SUCCESS.name,
            registered_credit_number=15.4,
            acquired_credit_number=15.4,
            transcript=[],
            transcript_translation=[],
        )

        EducationalExperienceYearFactory(
            educational_experience=self.educational_experience,
            academic_year=self.academic_year_2018,
            result=Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
            registered_credit_number=18,
            acquired_credit_number=18,
            transcript=[],
            transcript_translation=[],
        )

        self.admission_details_url = resolve_url(
            'cv_educational_experiences-detail',
            uuid=self.admission.uuid,
            experience_id=self.educational_experience.uuid,
        )

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

        methods_not_allowed_on_detail = [
            'patch',
            'post',
        ]

        methods_not_allowed_on_listing_create = [
            'patch',
            'put',
            'get',
            'delete',
        ]

        for method in methods_not_allowed_on_detail:
            response = getattr(self.client, method)(self.admission_details_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        for method in methods_not_allowed_on_listing_create:
            response = getattr(self.client, method)(self.admission_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_educational_experience(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.admission_details_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()

        # Check response data
        self.assertEqual(json_response.get('uuid'), str(self.educational_experience.uuid))
        self.assertEqual(json_response.get('program'), str(self.diploma.uuid))
        self.assertEqual(json_response.get('education_name'), 'Computer science')
        self.assertEqual(json_response.get('institute_name'), 'UCL')
        self.assertEqual(json_response.get('country'), self.country.iso_code)
        self.assertEqual(json_response.get('institute'), None)
        self.assertEqual(json_response.get('institute_address'), 'Place de l\'Université')
        self.assertEqual(json_response.get('study_system'), '')
        self.assertEqual(json_response.get('evaluation_type'), EvaluationSystem.ECTS_CREDITS.name)
        self.assertEqual(json_response.get('linguistic_regime'), self.linguistic_regime.code)
        self.assertEqual(json_response.get('transcript_type'), TranscriptType.ONE_FOR_ALL_YEARS.name)
        self.assertEqual(json_response.get('obtained_diploma'), True)
        self.assertEqual(json_response.get('obtained_grade'), Grade.GREAT_DISTINCTION.name)
        self.assertEqual(json_response.get('graduate_degree'), [])
        self.assertEqual(json_response.get('graduate_degree_translation'), [])
        self.assertEqual(json_response.get('transcript'), [])
        self.assertEqual(json_response.get('transcript_translation'), [])
        self.assertEqual(json_response.get('bachelor_cycle_continuation'), True)
        self.assertEqual(json_response.get('diploma_equivalence'), [])
        self.assertEqual(json_response.get('rank_in_diploma'), '10 on 100')
        self.assertEqual(json_response.get('expected_graduation_date'), '2022-08-30')
        self.assertEqual(json_response.get('dissertation_title'), 'Title')
        self.assertEqual(json_response.get('dissertation_score'), '15/20')
        self.assertEqual(json_response.get('dissertation_summary'), [])

        self.assertEqual(len(json_response.get('educationalexperienceyear_set')), 2)
        json_first_educational_experience_year = json_response.get('educationalexperienceyear_set')[0]
        self.assertEqual(json_first_educational_experience_year.get('academic_year'), 2020)
        self.assertEqual(json_first_educational_experience_year.get('result'), Result.SUCCESS.name)
        self.assertEqual(json_first_educational_experience_year.get('registered_credit_number'), 15.4)
        self.assertEqual(json_first_educational_experience_year.get('acquired_credit_number'), 15.4)
        self.assertEqual(json_first_educational_experience_year.get('transcript'), [])
        self.assertEqual(json_first_educational_experience_year.get('transcript_translation'), [])

    def test_post_educational_experience(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.admission_url,
            data={
                'program': self.diploma.uuid,
                'education_name': 'Biology',
                'institute_name': 'Second institute',
                'country': self.country.iso_code,
                'institute': None,
                'institute_address': 'Louvain-La-Neuve',
                'study_system': '',
                'evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'linguistic_regime': self.linguistic_regime.code,
                'transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'obtained_diploma': True,
                'obtained_grade': Grade.GREAT_DISTINCTION.name,
                'graduate_degree': [],
                'graduate_degree_translation': [],
                'transcript': [],
                'transcript_translation': [],
                'bachelor_cycle_continuation': False,
                'diploma_equivalence': [],
                'rank_in_diploma': '10 on 100',
                'expected_graduation_date': '2022-08-30',
                'dissertation_title': 'Title',
                'dissertation_score': '15/20',
                'dissertation_summary': [],
                'educationalexperienceyear_set': [
                    {
                        'academic_year': 2020,
                        'result': Result.SUCCESS.name,
                        'registered_credit_number': 15.4,
                        'acquired_credit_number': 15.4,
                        'transcript': [],
                        'transcript_translation': [],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        json_response = response.json()

        # Check response data
        self.assertEqual(json_response.get('program'), str(self.diploma.uuid))
        self.assertEqual(json_response.get('education_name'), 'Biology')
        self.assertEqual(json_response.get('institute_name'), 'Second institute')
        self.assertEqual(json_response.get('country'), self.country.iso_code)
        self.assertEqual(json_response.get('institute'), None)
        self.assertEqual(json_response.get('institute_address'), 'Louvain-La-Neuve')
        self.assertEqual(json_response.get('study_system'), '')
        self.assertEqual(json_response.get('evaluation_type'), EvaluationSystem.ECTS_CREDITS.name)
        self.assertEqual(json_response.get('linguistic_regime'), self.linguistic_regime.code)
        self.assertEqual(json_response.get('transcript_type'), TranscriptType.ONE_FOR_ALL_YEARS.name)
        self.assertEqual(json_response.get('obtained_diploma'), True)
        self.assertEqual(json_response.get('obtained_grade'), Grade.GREAT_DISTINCTION.name)
        self.assertEqual(json_response.get('graduate_degree'), [])
        self.assertEqual(json_response.get('graduate_degree_translation'), [])
        self.assertEqual(json_response.get('transcript'), [])
        self.assertEqual(json_response.get('transcript_translation'), [])
        self.assertEqual(json_response.get('bachelor_cycle_continuation'), False)
        self.assertEqual(json_response.get('diploma_equivalence'), [])
        self.assertEqual(json_response.get('rank_in_diploma'), '10 on 100')
        self.assertEqual(json_response.get('expected_graduation_date'), '2022-08-30')
        self.assertEqual(json_response.get('dissertation_title'), 'Title')
        self.assertEqual(json_response.get('dissertation_score'), '15/20')
        self.assertEqual(json_response.get('dissertation_summary'), [])
        self.assertEqual(json_response.get('valuated_from_admission'), [])

        json_first_educational_experience_year = json_response.get('educationalexperienceyear_set')[0]
        self.assertEqual(json_first_educational_experience_year.get('academic_year'), 2020)
        self.assertEqual(json_first_educational_experience_year.get('result'), Result.SUCCESS.name)
        self.assertEqual(json_first_educational_experience_year.get('registered_credit_number'), 15.4)
        self.assertEqual(json_first_educational_experience_year.get('acquired_credit_number'), 15.4)
        self.assertEqual(json_first_educational_experience_year.get('transcript'), [])
        self.assertEqual(json_first_educational_experience_year.get('transcript_translation'), [])

        # Check saved data
        experience: EducationalExperience = EducationalExperience.objects.filter(
            uuid=json_response.get('uuid'),
        ).first()

        self.assertIsNotNone(experience)

        self.assertEqual(experience.person, self.user.person)
        self.assertEqual(experience.program, self.diploma)
        self.assertEqual(experience.education_name, 'Biology')
        self.assertEqual(experience.institute_name, 'Second institute')
        self.assertEqual(experience.country, self.country)
        self.assertEqual(experience.institute, None)
        self.assertEqual(experience.institute_address, 'Louvain-La-Neuve')
        self.assertEqual(experience.study_system, '')
        self.assertEqual(experience.evaluation_type, EvaluationSystem.ECTS_CREDITS.name)
        self.assertEqual(experience.linguistic_regime, self.linguistic_regime)
        self.assertEqual(experience.transcript_type, TranscriptType.ONE_FOR_ALL_YEARS.name)
        self.assertEqual(experience.obtained_diploma, True)
        self.assertEqual(experience.obtained_grade, Grade.GREAT_DISTINCTION.name)
        self.assertEqual(experience.graduate_degree, [])
        self.assertEqual(experience.graduate_degree_translation, [])
        self.assertEqual(experience.transcript, [])
        self.assertEqual(experience.transcript_translation, [])
        self.assertEqual(experience.bachelor_cycle_continuation, False)
        self.assertEqual(experience.diploma_equivalence, [])
        self.assertEqual(experience.rank_in_diploma, '10 on 100')
        self.assertEqual(experience.expected_graduation_date, datetime.date(2022, 8, 30))
        self.assertEqual(experience.dissertation_title, 'Title')
        self.assertEqual(experience.dissertation_score, '15/20')
        self.assertEqual(experience.dissertation_summary, [])

        first_educational_experience_year = EducationalExperienceYear.objects.filter(
            educational_experience=experience
        ).first()

        self.assertEqual(first_educational_experience_year.academic_year, self.academic_year_2020)
        self.assertEqual(first_educational_experience_year.result, Result.SUCCESS.name)
        self.assertEqual(first_educational_experience_year.registered_credit_number, 15.4)
        self.assertEqual(first_educational_experience_year.acquired_credit_number, 15.4)
        self.assertEqual(first_educational_experience_year.transcript, [])
        self.assertEqual(first_educational_experience_year.transcript_translation, [])

    def test_put_educational_experience(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            self.admission_details_url,
            data={
                'program': self.diploma.uuid,
                'education_name': 'Biology',
                'institute_name': '',
                'country': self.country.iso_code,
                'institute': self.institute.uuid,
                'institute_address': '',
                'evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'linguistic_regime': self.linguistic_regime.code,
                'transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'obtained_diploma': True,
                'obtained_grade': Grade.GREATER_DISTINCTION.name,
                'graduate_degree': [],
                'graduate_degree_translation': [],
                'transcript': [],
                'transcript_translation': [],
                'bachelor_cycle_continuation': False,
                'diploma_equivalence': [],
                'rank_in_diploma': '10 on 100',
                'expected_graduation_date': '2022-08-30',
                'dissertation_title': 'Title',
                'dissertation_score': '15/20',
                'dissertation_summary': [],
                'educationalexperienceyear_set': [
                    {
                        'academic_year': 2020,
                        'result': Result.SUCCESS.name,
                        'registered_credit_number': 25,
                        'acquired_credit_number': 25,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                    {
                        'academic_year': 2019,
                        'result': Result.SUCCESS.name,
                        'registered_credit_number': 14,
                        'acquired_credit_number': 14,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()

        # Check response data
        self.assertEqual(json_response.get('obtained_grade'), Grade.GREATER_DISTINCTION.name)
        self.assertEqual(json_response.get('study_system'), TeachingTypeEnum.SOCIAL_PROMOTION.name)

        json_first_educational_experience_year = json_response.get('educationalexperienceyear_set')[0]
        self.assertEqual(json_first_educational_experience_year.get('academic_year'), 2020)
        self.assertEqual(json_first_educational_experience_year.get('registered_credit_number'), 25)
        self.assertEqual(json_first_educational_experience_year.get('acquired_credit_number'), 25)

        # Check saved data
        experience = EducationalExperience.objects.get(
            uuid=self.educational_experience.uuid,
        )

        self.assertEqual(experience.obtained_grade, Grade.GREATER_DISTINCTION.name)

        educational_experience_years = EducationalExperienceYear.objects.filter(educational_experience=experience)

        self.assertEqual(len(educational_experience_years), 2)

        self.assertEqual(educational_experience_years[0].academic_year, self.academic_year_2020)
        self.assertEqual(educational_experience_years[0].registered_credit_number, 25)
        self.assertEqual(educational_experience_years[0].acquired_credit_number, 25)

        self.assertEqual(educational_experience_years[1].academic_year, self.academic_year_2019)
        self.assertEqual(educational_experience_years[1].registered_credit_number, 14)
        self.assertEqual(educational_experience_years[1].acquired_credit_number, 14)

    def test_put_valuated_educational_experience_is_forbidden(self):
        self.client.force_authenticate(user=self.user)

        self.educational_experience.valuated_from_admission.set([self.admission])

        response = self.client.put(
            self.admission_details_url,
            data={},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_educational_experience(self):
        self.client.force_authenticate(user=self.user)

        self.assertTrue(
            EducationalExperience.objects.filter(
                uuid=self.educational_experience.uuid,
            ).exists()
        )

        self.client.delete(self.admission_details_url)

        self.assertFalse(
            EducationalExperience.objects.filter(
                uuid=self.educational_experience.uuid,
            ).exists()
        )

    def test_delete_valuated_educational_experience_is_forbidden(self):
        self.client.force_authenticate(user=self.user)

        self.educational_experience.valuated_from_admission.set([self.admission])

        response = self.client.delete(self.admission_details_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
