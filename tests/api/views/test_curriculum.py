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

import freezegun
import mock
import uuid
from django.shortcuts import resolve_url
from django.test import override_settings

from rest_framework import status
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from admission.contrib.models import ContinuingEducationAdmission, GeneralEducationAdmission
from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutProposition
from admission.contrib.models.base import BaseAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.curriculum import (
    ProfessionalExperienceFactory,
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
)
from admission.tests.factories.form_item import AdmissionFormItemInstantiationFactory, TextAdmissionFormItemFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
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


class BaseCurriculumTestCase:
    @classmethod
    def setUpTestData(cls):
        cls.today_date = datetime.date(2020, 11, 1)
        cls.today_datetime = datetime.datetime(2020, 11, 1)
        cls.country = CountryFactory()
        cls.academic_year_2018 = AcademicYearFactory(year=2018)
        cls.academic_year_2019 = AcademicYearFactory(year=2019)
        cls.academic_year_2020 = AcademicYearFactory(year=2020)

    def setUp(self) -> None:
        # Mock datetime to return the 2020 year as the current year
        patcher = mock.patch('base.models.academic_year.timezone')
        self.addCleanup(patcher.stop)
        self.mock_foo = patcher.start()
        self.mock_foo.now.return_value = self.today_datetime
        # Mock files
        patcher = mock.patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)

        # Mock datetime to return the 2020 year as the current year
        patcher = freezegun.freeze_time('2020-11-01')
        patcher.start()
        self.addCleanup(patcher.stop)


def create_professional_experiences(person):
    return [
        ProfessionalExperienceFactory(
            person=person,
            institute_name='First institute',
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2021, 1, 1),
            type=ActivityType.WORK.name,
            role='Librarian',
            sector=ActivitySector.PUBLIC.name,
            activity='Work - activity',
        ),
        ProfessionalExperienceFactory(
            person=person,
            institute_name='Second institute',
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2020, 9, 1),
            type=ActivityType.WORK.name,
            role='Librarian',
            sector=ActivitySector.PUBLIC.name,
            activity='Work - activity',
        ),
    ]


def create_educational_experiences(person, country):
    experiences = [
        EducationalExperienceFactory(
            person=person,
            country=country,
            institute_name='UCL',
            education_name='Computer science 3',
            obtained_diploma=False,
            linguistic_regime__code=FR_ISO_CODE,
        ),
    ]

    EducationalExperienceYearFactory(
        educational_experience=experiences[0],
        academic_year=AcademicYearFactory(year=2020),
        result=Result.SUCCESS.name,
    )

    return experiences


@override_settings(ROOT_URLCONF='admission.api.url_v1', OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DoctorateCurriculumTestCase(BaseCurriculumTestCase, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Mocked data
        cls.admission = DoctorateAdmissionFactory(
            status=ChoixStatutProposition.IN_PROGRESS.name,
        )
        cls.other_admission = DoctorateAdmissionFactory()
        cls.user = cls.admission.candidate.user
        cls.other_user = cls.other_admission.candidate.user
        cls.user_without_admission = CandidateFactory().person.user
        cls.linguistic_regime = LanguageFactory(code=FR_ISO_CODE)
        cls.linguistic_regime_with_translation = LanguageFactory(code='BR')

        AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year=cls.admission.doctorate.academic_year,
        )

        cls.put_data = {
            'reponses_questions_specifiques': {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My answer !',
            },
            'curriculum': ['file1.pdf'],
            'uuid_proposition': cls.admission.uuid,
        }

        cls.professional_experiences = create_professional_experiences(person=cls.user.person)
        cls.educational_experiences = create_educational_experiences(person=cls.user.person, country=cls.country)

        # Targeted urls
        cls.admission_url = resolve_url('doctorate_curriculum', uuid=cls.admission.uuid)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

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
        self.assertEqual(response.get('minimal_date'), '2016-09-01')
        self.assertEqual(response.get('maximal_date'), '2020-10-01')
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
                    'education_name': 'Computer science 3',
                    'educationalexperienceyear_set': [{'academic_year': 2020, 'result': Result.SUCCESS.name}],
                    'valuated_from_admission': [],
                    'country': self.country.iso_code,
                }
            ],
        )
        self.assertEqual(
            response.get('incomplete_periods'),
            [
                'De Septembre 2019 à Décembre 2019',
                'De Septembre 2018 à Janvier 2019',
                'De Septembre 2017 à Janvier 2018',
                'De Septembre 2016 à Janvier 2017',
            ],
        )

        self.assertEqual(
            response.get('incomplete_experiences'),
            {},
        )

    def test_get_curriculum_several_educational_experiences(self):
        self.client.force_authenticate(user=self.user)

        experience_2018 = EducationalExperienceFactory(
            person=self.admission.candidate,
            country=self.country,
            institute_name='UCL',
            education_name='Computer science 1',
            obtained_diploma=False,
            linguistic_regime__code=FR_ISO_CODE,
        )
        experience_2019 = EducationalExperienceFactory(
            person=self.admission.candidate,
            country=self.country,
            institute_name='UCL',
            education_name='Computer science 2',
            obtained_diploma=False,
            linguistic_regime__code=FR_ISO_CODE,
        )
        EducationalExperienceYearFactory(
            educational_experience=experience_2018,
            academic_year=self.academic_year_2018,
            result=Result.SUCCESS.name,
        )
        EducationalExperienceYearFactory(
            educational_experience=experience_2019,
            academic_year=self.academic_year_2019,
            result=Result.SUCCESS.name,
        )

        response = self.client.get(self.admission_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        response = response.json()

        experiences = response.get('educational_experiences')
        self.assertEqual(len(experiences), 3)
        self.assertEqual(
            [experience.get('education_name') for experience in experiences],
            [
                'Computer science 3',
                'Computer science 2',
                'Computer science 1',
            ],
        )
        self.assertEqual(
            response.get('incomplete_periods'),
            [
                'De Septembre 2017 à Janvier 2018',
                'De Septembre 2016 à Janvier 2017',
            ],
        )

    def test_get_curriculum_minimal_year_with_last_registration(self):
        self.client.force_authenticate(user=self.user)

        self.user.person.last_registration_year = self.academic_year_2018
        self.user.person.save()
        response = self.client.get(self.admission_url)

        # Check response data
        response = response.json()
        self.assertEqual(response.get('minimal_date'), '2019-09-01')
        self.assertEqual(response.get('incomplete_periods'), ['De Septembre 2019 à Décembre 2019'])
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
        self.assertEqual(response.get('minimal_date'), '2019-09-01')
        self.assertEqual(response.get('incomplete_periods'), ['De Septembre 2019 à Décembre 2019'])

        belgian_diploma.delete()

    def test_get_curriculum_minimal_year_with_foreign_diploma(self):
        self.client.force_authenticate(user=self.user)

        foreign_diploma = ForeignHighSchoolDiplomaFactory(
            person=self.user.person,
            academic_graduation_year=self.academic_year_2018,
            linguistic_regime__code=FR_ISO_CODE,
        )

        response = self.client.get(self.admission_url)

        # Check response data
        response = response.json()
        self.assertEqual(response.get('minimal_date'), '2019-09-01')
        self.assertEqual(response.get('incomplete_periods'), ['De Septembre 2019 à Décembre 2019'])

        foreign_diploma.delete()

    def test_get_curriculum_when_completed(self):
        self.client.force_authenticate(user=self.user)

        self.user.person.last_registration_year = self.academic_year_2019
        self.user.person.save()
        response = self.client.get(self.admission_url)

        # Check response data
        response = response.json()
        self.assertEqual(response.get('minimal_date'), '2020-09-01')
        self.assertEqual(response.get('incomplete_periods'), [])
        self.user.person.last_registration_year = None
        self.user.person.save()

    def _test_get_curriculum_with_incomplete_educational_experience(self, experience_args, experience_year_args):
        self.client.force_authenticate(user=self.user)

        default_experience_args = {
            'person': self.admission.candidate,
            'country': self.country,
            'institute_name': 'UCL',
            'linguistic_regime': self.linguistic_regime,
            'education_name': 'Computer science 1',
        }
        default_experience_args.update(experience_args)

        experience_2018 = EducationalExperienceFactory(
            **default_experience_args,
        )

        EducationalExperienceYearFactory(
            educational_experience=experience_2018,
            academic_year=AcademicYearFactory(year=2018),
            result=Result.SUCCESS.name,
            **experience_year_args,
        )

        # Transcript missing
        response = self.client.get(self.admission_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        self.assertEqual(
            json_response.get('incomplete_experiences'),
            {
                str(experience_2018.uuid): ['Cette expérience académique est incomplète.'],
            },
        )

    def test_get_curriculum_with_incomplete_educational_experience_transcript_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'transcript': [],
            },
            experience_year_args={},
        )

    def test_get_curriculum_with_incomplete_educational_experience_transcript_translation_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'country__iso_code': 'FR',
                'linguistic_regime': self.linguistic_regime_with_translation,
                'transcript_translation': [],
            },
            experience_year_args={},
        )

    def test_get_curriculum_with_incomplete_educational_experience_annual_transcript_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'transcript_type': TranscriptType.ONE_A_YEAR.name,
            },
            experience_year_args={
                'transcript': [],
            },
        )

    def test_get_curriculum_with_incomplete_educational_experience_annual_transcript_translation_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'country__iso_code': 'FR',
                'linguistic_regime': self.linguistic_regime_with_translation,
                'transcript_type': TranscriptType.ONE_A_YEAR.name,
            },
            experience_year_args={
                'transcript_translation': [],
            },
        )

    def test_get_curriculum_with_incomplete_educational_experience_diploma_rank_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'obtained_diploma': True,
                'rank_in_diploma': '',
            },
            experience_year_args={},
        )

    def test_get_curriculum_with_incomplete_educational_experience_diploma_date_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'obtained_diploma': True,
                'expected_graduation_date': None,
            },
            experience_year_args={},
        )

    def test_get_curriculum_with_incomplete_educational_experience_dissertation_title_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'obtained_diploma': True,
                'dissertation_title': '',
            },
            experience_year_args={},
        )

    def test_get_curriculum_with_incomplete_educational_experience_dissertation_score_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'obtained_diploma': True,
                'dissertation_score': '',
            },
            experience_year_args={},
        )

    def test_get_curriculum_with_incomplete_educational_experience_dissertation_summary_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'obtained_diploma': True,
                'dissertation_summary': [],
            },
            experience_year_args={},
        )

    def test_get_curriculum_with_incomplete_educational_experience_diploma_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'obtained_diploma': True,
                'graduate_degree': [],
            },
            experience_year_args={},
        )

    def test_get_curriculum_with_incomplete_educational_experience_diploma_translation_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'country__iso_code': 'FR',
                'linguistic_regime': self.linguistic_regime_with_translation,
                'obtained_diploma': True,
                'graduate_degree_translation': [],
            },
            experience_year_args={},
        )

    def test_put_curriculum(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(self.admission_url, data=self.put_data)

        self.assertEqual(response.status_code, HTTP_200_OK)
        updated_admission = BaseAdmission.objects.get(uuid=self.admission.uuid)

        self.assertEqual(
            updated_admission.specific_question_answers,
            {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My answer !',
            },
        )
        self.assertEqual(updated_admission.curriculum, [uuid.UUID('550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92')])


@override_settings(ROOT_URLCONF='admission.api.url_v1', OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class GeneralEducationCurriculumTestCase(BaseCurriculumTestCase, APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.admission = GeneralEducationAdmissionFactory(training__academic_year__year=2020)
        AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year__year=2020,
        )

        cls.linguistic_regime = LanguageFactory(code=FR_ISO_CODE)
        cls.linguistic_regime_with_translation = LanguageFactory(code='BR')

        cls.put_data = {
            'reponses_questions_specifiques': {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My answer !',
            },
            'curriculum': ['file1.pdf'],
            'uuid_proposition': cls.admission.uuid,
            'equivalence_diplome': ['file2.pdf'],
            'continuation_cycle_bachelier': False,
            'attestation_continuation_cycle_bachelier': [],
        }

        # Users
        cls.user = cls.admission.candidate.user

        cls.professional_experiences = create_professional_experiences(person=cls.user.person)
        cls.educational_experiences = create_educational_experiences(person=cls.user.person, country=cls.country)

        # Targeted urls
        cls.admission_url = resolve_url('general_curriculum', uuid=cls.admission.uuid)

    def test_get_curriculum_with_last_registration(self):
        self.client.force_authenticate(user=self.user)

        self.user.person.last_registration_year = self.academic_year_2019
        self.user.person.save()
        response = self.client.get(self.admission_url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check response data
        response = response.json()
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
                    'education_name': 'Computer science 3',
                    'educationalexperienceyear_set': [{'academic_year': 2020, 'result': Result.SUCCESS.name}],
                    'valuated_from_admission': [],
                    'country': self.country.iso_code,
                }
            ],
        )
        self.assertEqual(response.get('minimal_date'), '2020-09-01')
        self.assertEqual(response.get('maximal_date'), '2020-10-01')
        self.assertEqual(response.get('incomplete_periods'), [])
        self.user.person.last_registration_year = None
        self.user.person.save()

    def test_get_curriculum_when_completed(self):
        self.client.force_authenticate(user=self.user)

        self.user.person.last_registration_year = self.academic_year_2020
        self.user.person.save()
        response = self.client.get(self.admission_url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check response data
        response = response.json()
        self.assertEqual(response.get('minimal_date'), '2021-09-01')
        self.assertEqual(response.get('maximal_date'), '2020-10-01')
        self.assertEqual(response.get('incomplete_periods'), [])
        self.assertEqual(response.get('incomplete_experiences'), {})
        self.user.person.last_registration_year = None
        self.user.person.save()

    def _test_get_curriculum_with_incomplete_educational_experience(self, experience_args, experience_year_args):
        self.client.force_authenticate(user=self.user)

        default_experience_args = {
            'person': self.admission.candidate,
            'country': self.country,
            'institute_name': 'UCL',
            'linguistic_regime': self.linguistic_regime,
            'education_name': 'Computer science 1',
        }
        default_experience_args.update(experience_args)

        experience_2018 = EducationalExperienceFactory(
            **default_experience_args,
        )

        EducationalExperienceYearFactory(
            educational_experience=experience_2018,
            academic_year=AcademicYearFactory(year=2018),
            result=Result.SUCCESS.name,
            **experience_year_args,
        )

        # Transcript missing
        response = self.client.get(self.admission_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        self.assertEqual(
            json_response.get('incomplete_experiences'),
            {
                str(experience_2018.uuid): ['Cette expérience académique est incomplète.'],
            },
        )

    def test_get_curriculum_with_incomplete_educational_experience_transcript_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'transcript': [],
            },
            experience_year_args={},
        )

    def test_get_curriculum_with_incomplete_educational_experience_transcript_translation_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'country__iso_code': 'FR',
                'linguistic_regime': self.linguistic_regime_with_translation,
                'transcript_translation': [],
            },
            experience_year_args={},
        )

    def test_get_curriculum_with_incomplete_educational_experience_annual_transcript_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'transcript_type': TranscriptType.ONE_A_YEAR.name,
            },
            experience_year_args={
                'transcript': [],
            },
        )

    def test_get_curriculum_with_incomplete_educational_experience_annual_transcript_translation_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'country__iso_code': 'FR',
                'linguistic_regime': self.linguistic_regime_with_translation,
                'transcript_type': TranscriptType.ONE_A_YEAR.name,
            },
            experience_year_args={
                'transcript_translation': [],
            },
        )

    def test_get_curriculum_with_incomplete_educational_experience_diploma_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'obtained_diploma': True,
                'graduate_degree': [],
            },
            experience_year_args={},
        )

    def test_get_curriculum_with_incomplete_educational_experience_diploma_translation_missing(self):
        self._test_get_curriculum_with_incomplete_educational_experience(
            experience_args={
                'country__iso_code': 'FR',
                'linguistic_regime': self.linguistic_regime_with_translation,
                'obtained_diploma': True,
                'graduate_degree_translation': [],
            },
            experience_year_args={},
        )

    def test_put_curriculum(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(self.admission_url, data=self.put_data)

        self.assertEqual(response.status_code, HTTP_200_OK)
        updated_admission = GeneralEducationAdmission.objects.get(uuid=self.admission.uuid)

        self.assertEqual(
            updated_admission.specific_question_answers,
            {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My answer !',
            },
        )
        self.assertEqual(updated_admission.curriculum, [uuid.UUID('550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92')])
        self.assertEqual(updated_admission.diploma_equivalence, [uuid.UUID('550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92')])
        self.assertEqual(updated_admission.bachelor_cycle_continuation_certificate, [])
        self.assertEqual(updated_admission.bachelor_cycle_continuation, False)


@override_settings(ROOT_URLCONF='admission.api.url_v1', OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class ContinuingEducationCurriculumTestCase(BaseCurriculumTestCase, APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.admission = ContinuingEducationAdmissionFactory()
        AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year=cls.admission.training.academic_year,
        )

        cls.put_data = {
            'reponses_questions_specifiques': {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My answer !',
            },
            'curriculum': ['file1.pdf'],
            'uuid_proposition': cls.admission.uuid,
            'equivalence_diplome': ['file2.pdf'],
        }

        # Users
        cls.user = cls.admission.candidate.user

        cls.professional_experiences = create_professional_experiences(person=cls.user.person)
        cls.educational_experiences = create_educational_experiences(person=cls.user.person, country=cls.country)

        # Targeted urls
        cls.admission_url = resolve_url('continuing_curriculum', uuid=cls.admission.uuid)

    def test_put_curriculum(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(self.admission_url, data=self.put_data)

        self.assertEqual(response.status_code, HTTP_200_OK)
        updated_admission = ContinuingEducationAdmission.objects.get(uuid=self.admission.uuid)

        self.assertEqual(
            updated_admission.specific_question_answers,
            {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My answer !',
            },
        )
        self.assertEqual(updated_admission.curriculum, [uuid.UUID('550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92')])
        self.assertEqual(updated_admission.diploma_equivalence, [uuid.UUID('550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92')])

    def test_get_curriculum_with_last_registration(self):
        self.client.force_authenticate(user=self.user)

        self.user.person.last_registration_year = self.academic_year_2019
        self.user.person.save()
        response = self.client.get(self.admission_url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check response data
        response = response.json()
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
                    'education_name': 'Computer science 3',
                    'educationalexperienceyear_set': [{'academic_year': 2020, 'result': Result.SUCCESS.name}],
                    'valuated_from_admission': [],
                    'country': self.country.iso_code,
                }
            ],
        )
        self.assertEqual(response.get('minimal_date'), '2020-09-01')
        self.assertEqual(response.get('maximal_date'), '2020-10-01')
        self.assertEqual(response.get('incomplete_periods'), [])
        self.user.person.last_registration_year = None
        self.user.person.save()


@override_settings(ROOT_URLCONF='admission.api.url_v1', OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class PersonCurriculumTestCase(BaseCurriculumTestCase, APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        # Users
        cls.user = CandidateFactory().person.user

        cls.professional_experiences = create_professional_experiences(person=cls.user.person)
        cls.educational_experiences = create_educational_experiences(person=cls.user.person, country=cls.country)

        # Targeted url
        cls.agnostic_url = resolve_url('curriculum')

    def test_get_curriculum_with_last_registration(self):
        self.client.force_authenticate(user=self.user)

        self.user.person.last_registration_year = self.academic_year_2019
        self.user.person.save()
        response = self.client.get(self.agnostic_url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check response data
        response = response.json()
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
                    'education_name': 'Computer science 3',
                    'educationalexperienceyear_set': [{'academic_year': 2020, 'result': Result.SUCCESS.name}],
                    'valuated_from_admission': [],
                    'country': self.country.iso_code,
                }
            ],
        )
        self.assertEqual(response.get('minimal_date'), '2020-09-01')
        self.assertEqual(response.get('maximal_date'), '2020-10-01')
        self.assertEqual(response.get('incomplete_periods'), [])
        self.user.person.last_registration_year = None
        self.user.person.save()


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
        cls.linguistic_regime = LanguageFactory(code=FR_ISO_CODE)
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
