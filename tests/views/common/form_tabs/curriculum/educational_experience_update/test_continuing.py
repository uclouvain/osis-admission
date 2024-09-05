# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid
from unittest import mock

from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.constants import CONTEXT_CONTINUING
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.models import ContinuingEducationAdmission
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
)
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.campus import Campus
from base.models.enums.community import CommunityEnum
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from osis_profile.forms.experience_academique import (
    EDUCATIONAL_EXPERIENCE_FIELDS_BY_CONTEXT,
    EDUCATIONAL_EXPERIENCE_YEAR_FIELDS_BY_CONTEXT,
)
from osis_profile.models import EducationalExperience, EducationalExperienceYear
from osis_profile.models.enums.curriculum import TranscriptType, Result, EvaluationSystem, Reduction, Grade
from reference.models.enums.cycle import Cycle
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.diploma_title import DiplomaTitleFactory
from reference.tests.factories.language import LanguageFactory


# TODO: Remove duplicate tests with osis_profile
class CurriculumEducationalExperienceFormViewForContinuingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022, 2023]]
        cls.old_academic_years = [AcademicYearFactory(year=year) for year in [2003, 2004, 2005, 2006, 2007]]
        cls.be_country = CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')
        cls.fr_country = CountryFactory(iso_code='FR', name='France', name_en='France')
        cls.louvain_campus = Campus.objects.get(external_id=CampusFactory(name='Louvain-la-Neuve').external_id)
        cls.other_campus = Campus.objects.get(external_id=CampusFactory(name='Other').external_id)
        cls.greek = LanguageFactory(code='EL')
        cls.french = LanguageFactory(code='FR')
        cls.entity = EntityVersionFactory().entity

        cls.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=cls.entity,
            training__academic_year=cls.academic_years[0],
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.entity).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.continuing_admission.training.education_group,
        ).person.user
        cls.first_cycle_diploma = DiplomaTitleFactory(
            cycle=Cycle.FIRST_CYCLE.name,
        )
        cls.second_cycle_diploma = DiplomaTitleFactory(
            cycle=Cycle.SECOND_CYCLE.name,
        )
        cls.first_institute = OrganizationFactory(
            community=CommunityEnum.FRENCH_SPEAKING.name,
            establishment_type=EstablishmentTypeEnum.UNIVERSITY.name,
        )
        cls.second_institute = OrganizationFactory(
            community=CommunityEnum.FRENCH_SPEAKING.name,
            establishment_type=EstablishmentTypeEnum.NON_UNIVERSITY_HIGHER.name,
        )
        cls.files_names = [
            'graduate_degree',
            'graduate_degree_translation',
            'transcript',
            'transcript_translation',
            'dissertation_summary',
            '2020-transcript',
            '2020-transcript_translation',
            '2021-transcript',
            '2021-transcript_translation',
            '2022-transcript',
            '2022-transcript_translation',
            '2023-transcript',
            '2023-transcript_translation',
        ]
        cls.files_uuids = {file_name: uuid.uuid4() for file_name in cls.files_names}
        cls.new_file_uuids = {file_name: uuid.uuid4() for file_name in cls.files_names}

    def setUp(self):
        # Create data
        self.experience: EducationalExperience = EducationalExperienceFactory(
            person=self.continuing_admission.candidate,
            country=self.be_country,
            program=self.first_cycle_diploma,
            fwb_equivalent_program=self.first_cycle_diploma,
            institute=self.first_institute,
            linguistic_regime=self.french,
            education_name='',
            institute_name='',
            institute_address='',
            obtained_diploma=True,
            evaluation_type=EvaluationSystem.ECTS_CREDITS.name,
            transcript_type=TranscriptType.ONE_FOR_ALL_YEARS.name,
            obtained_grade=Grade.GREAT_DISTINCTION.name,
            graduate_degree=[self.files_uuids['graduate_degree']],
            transcript=[self.files_uuids['transcript']],
            graduate_degree_translation=[],
            transcript_translation=[],
            rank_in_diploma='10 on 100',
            expected_graduation_date=datetime.date(2024, 1, 1),
            dissertation_title='The new title',
            dissertation_score='A',
            dissertation_summary=[self.files_uuids['dissertation_summary']],
        )
        self.first_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=self.experience,
            academic_year=self.academic_years[0],
            result=Result.SUCCESS.name,
            registered_credit_number=10,
            acquired_credit_number=9,
            transcript=[],
            transcript_translation=[],
            with_block_1=True,
            with_complement=True,
            fwb_registered_credit_number=20,
            fwb_acquired_credit_number=19,
            reduction=Reduction.A150.name,
            is_102_change_of_course=True,
        )
        self.second_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=self.experience,
            academic_year=self.academic_years[2],
            result=Result.SUCCESS.name,
            registered_credit_number=30,
            acquired_credit_number=29,
            transcript=[],
            transcript_translation=[],
            with_block_1=False,
            with_complement=False,
            fwb_registered_credit_number=40,
            fwb_acquired_credit_number=39,
            reduction=Reduction.A150.name,
            is_102_change_of_course=False,
        )

        # Mock osis document api
        patcher = mock.patch("osis_document.api.utils.get_remote_token", side_effect=lambda value, **kwargs: value)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE, "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: value
        self.addCleanup(patcher.stop)

        # Targeted url
        self.form_url = resolve_url(
            'admission:continuing-education:update:curriculum:educational',
            uuid=self.continuing_admission.uuid,
            experience_uuid=self.experience.uuid,
        )
        self.details_url = resolve_url(
            'admission:continuing-education:curriculum',
            uuid=self.continuing_admission.uuid,
        )
        self.create_url = resolve_url(
            'admission:continuing-education:update:curriculum:educational_create',
            uuid=self.continuing_admission.uuid,
        )

    def test_update_curriculum_is_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']
        formset = response.context['year_formset']

        enabled_fields = EDUCATIONAL_EXPERIENCE_FIELDS_BY_CONTEXT[CONTEXT_CONTINUING]
        for field in base_form.fields:
            self.assertEqual(base_form.fields[field].disabled, field not in enabled_fields)

        disabled_fields = EDUCATIONAL_EXPERIENCE_YEAR_FIELDS_BY_CONTEXT[CONTEXT_CONTINUING]
        for form in formset:
            for field in form.fields:
                self.assertEqual(form.fields[field].disabled, field not in disabled_fields)

    def test_form_submission_to_create_an_experience(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.create_url,
            data={
                'base_form-start': '2020',
                'base_form-end': '2021',
                'base_form-country': self.be_country.iso_code,
                'base_form-other_institute': False,
                'base_form-institute_name': 'Custom institute name',
                'base_form-institute_address': 'Custom institute address',
                'base_form-institute': self.first_institute.pk,
                'base_form-program': self.first_cycle_diploma.pk,
                'base_form-other_program': False,
                'base_form-education_name': 'Custom education name',
                'base_form-evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'base_form-linguistic_regime': self.french.code,
                'base_form-transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'base_form-obtained_diploma': True,
                'base_form-obtained_grade': Grade.GREAT_DISTINCTION.name,
                'base_form-graduate_degree_0': [self.new_file_uuids['graduate_degree']],
                'base_form-graduate_degree_translation_0': [self.new_file_uuids['graduate_degree_translation']],
                'base_form-transcript_0': [self.new_file_uuids['transcript']],
                'base_form-transcript_translation_0': [self.new_file_uuids['transcript_translation']],
                'base_form-rank_in_diploma': '10 on 100',
                'base_form-expected_graduation_date': datetime.date(2022, 1, 1),
                'base_form-dissertation_title': 'The new title',
                'base_form-dissertation_score': 'A',
                'base_form-dissertation_summary_0': [self.new_file_uuids['dissertation_summary']],
                'year_formset-2020-is_enrolled': True,
                'year_formset-2020-academic_year': 2020,
                'year_formset-2020-result': Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
                'year_formset-2020-acquired_credit_number': 100,
                'year_formset-2020-registered_credit_number': 150,
                'year_formset-2020-transcript_0': [self.new_file_uuids['2020-transcript']],
                'year_formset-2020-transcript_translation_0': [self.new_file_uuids['2020-transcript_translation']],
                'year_formset-2021-is_enrolled': True,
                'year_formset-2021-academic_year': 2021,
                'year_formset-2021-acquired_credit_number': '',
                'year_formset-2021-registered_credit_number': '',
                'year_formset-2021-result': '',
                'year_formset-2021-transcript_0': [],
                'year_formset-2021-transcript_translation_0': [],
                'year_formset-TOTAL_FORMS': '2',
                'year_formset-INITIAL_FORMS': '0',
            },
        )

        experiences = EducationalExperience.objects.exclude(
            person=self.continuing_admission.candidate,
            pk=self.experience.pk,
        )

        self.assertEqual(len(experiences), 1)

        experience = experiences[0]

        self.assertRedirects(
            response=response,
            expected_url=resolve_url(
                'admission:continuing-education:curriculum',
                uuid=self.continuing_admission.uuid,
            ),
        )

        # Check the experience (only the continuing fields are filled)
        self.assertEqual(experience.country, self.be_country)
        self.assertEqual(experience.institute_name, '')
        self.assertEqual(experience.institute_address, '')
        self.assertEqual(experience.institute, self.first_institute)
        self.assertEqual(experience.program, self.first_cycle_diploma)
        self.assertEqual(experience.education_name, '')
        self.assertEqual(experience.evaluation_type, EvaluationSystem.ECTS_CREDITS.name)  # Automatically computed
        self.assertEqual(experience.linguistic_regime, None)
        self.assertEqual(experience.transcript_type, '')
        self.assertEqual(experience.obtained_diploma, True)
        self.assertEqual(experience.obtained_grade, '')
        self.assertEqual(experience.graduate_degree, [self.new_file_uuids['graduate_degree']])
        self.assertEqual(experience.graduate_degree_translation, [])
        self.assertEqual(experience.transcript, [])
        self.assertEqual(experience.transcript_translation, [])
        self.assertEqual(experience.rank_in_diploma, '')
        self.assertEqual(experience.expected_graduation_date, None)
        self.assertEqual(experience.dissertation_title, '')
        self.assertEqual(experience.dissertation_score, '')
        self.assertEqual(experience.dissertation_summary, [])

        years = experience.educationalexperienceyear_set.all().order_by('academic_year__year')

        self.assertEqual(len(years), 2)
        self.assertEqual(years[0].academic_year, self.academic_years[0])
        self.assertEqual(years[0].result, '')
        self.assertEqual(years[0].registered_credit_number, None)
        self.assertEqual(years[0].acquired_credit_number, None)
        self.assertEqual(years[0].transcript, [])
        self.assertEqual(years[0].transcript_translation, [])
        self.assertEqual(years[0].with_block_1, None)
        self.assertEqual(years[0].with_complement, None)
        self.assertEqual(years[0].fwb_registered_credit_number, None)
        self.assertEqual(years[0].fwb_acquired_credit_number, None)
        self.assertEqual(years[0].reduction, '')
        self.assertEqual(years[0].is_102_change_of_course, None)

        self.assertEqual(years[1].academic_year, self.academic_years[1])
        self.assertEqual(years[1].result, '')
        self.assertEqual(years[1].registered_credit_number, None)
        self.assertEqual(years[1].acquired_credit_number, None)
        self.assertEqual(years[1].transcript, [])
        self.assertEqual(years[1].transcript_translation, [])
        self.assertEqual(years[1].with_block_1, None)
        self.assertEqual(years[1].with_complement, None)
        self.assertEqual(years[1].fwb_registered_credit_number, None)
        self.assertEqual(years[1].fwb_acquired_credit_number, None)
        self.assertEqual(years[1].reduction, '')
        self.assertEqual(years[1].is_102_change_of_course, None)

    def test_form_submission_to_update_an_experience(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'base_form-start': '2020',
                'base_form-end': '2023',
                'base_form-country': self.be_country.iso_code,
                'base_form-other_institute': True,
                'base_form-institute_name': 'Custom institute name',
                'base_form-institute_address': 'Custom institute address',
                'base_form-institute': self.first_institute.pk,
                'base_form-program': self.first_cycle_diploma.pk,
                'base_form-other_program': True,
                'base_form-education_name': 'Custom education name',
                'base_form-evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'base_form-linguistic_regime': self.greek.code,
                'base_form-transcript_type': TranscriptType.ONE_A_YEAR.name,
                'base_form-obtained_diploma': True,
                'base_form-obtained_grade': Grade.GREATER_DISTINCTION.name,
                'base_form-graduate_degree_0': [self.new_file_uuids['graduate_degree']],
                'base_form-graduate_degree_translation_0': [self.new_file_uuids['graduate_degree_translation']],
                'base_form-transcript_0': [self.new_file_uuids['transcript']],
                'base_form-transcript_translation_0': [self.new_file_uuids['transcript_translation']],
                'base_form-rank_in_diploma': '11 on 100',
                'base_form-expected_graduation_date': datetime.date(2025, 1, 1),
                'base_form-dissertation_title': 'The new title v2',
                'base_form-dissertation_score': 'B',
                'base_form-dissertation_summary_0': [self.new_file_uuids['dissertation_summary']],
                # Update existing one
                'year_formset-2022-is_enrolled': True,
                'year_formset-2022-academic_year': 2022,
                'year_formset-2022-result': Result.FAILURE.name,
                'year_formset-2022-acquired_credit_number': 220,
                'year_formset-2022-registered_credit_number': 221,
                'year_formset-2022-transcript_0': [self.new_file_uuids['2022-transcript']],
                'year_formset-2022-transcript_translation_0': [self.new_file_uuids['2022-transcript_translation']],
                # Add new one
                'year_formset-2023-is_enrolled': True,
                'year_formset-2023-academic_year': 2023,
                'year_formset-2023-result': Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
                'year_formset-2023-acquired_credit_number': 230,
                'year_formset-2023-registered_credit_number': 231,
                'year_formset-2023-transcript_0': [self.new_file_uuids['2023-transcript']],
                'year_formset-2023-transcript_translation_0': [self.new_file_uuids['2023-transcript_translation']],
                'year_formset-TOTAL_FORMS': '2',
                'year_formset-INITIAL_FORMS': '2',
            },
        )

        self.assertRedirects(response=response, expected_url=self.details_url)

        self.experience.refresh_from_db()
        experience = self.experience

        # Check the experience (only the continuing fields are updated)
        self.assertEqual(experience.country, self.be_country)
        self.assertEqual(experience.institute_name, 'Custom institute name')
        self.assertEqual(experience.institute_address, 'Custom institute address')
        self.assertEqual(experience.institute, None)
        self.assertEqual(experience.program, None)
        self.assertEqual(experience.education_name, 'Custom education name')
        self.assertEqual(experience.evaluation_type, EvaluationSystem.ECTS_CREDITS.name)  # Automatically computed
        self.assertEqual(experience.linguistic_regime, None)  # Automatically cleaned
        self.assertEqual(experience.transcript_type, TranscriptType.ONE_FOR_ALL_YEARS.name)
        self.assertEqual(experience.obtained_diploma, True)
        self.assertEqual(experience.obtained_grade, Grade.GREAT_DISTINCTION.name)
        self.assertEqual(experience.graduate_degree, [self.new_file_uuids['graduate_degree']])
        self.assertEqual(experience.graduate_degree_translation, [])
        self.assertEqual(experience.transcript, [self.files_uuids['transcript']])
        self.assertEqual(experience.transcript_translation, [])
        self.assertEqual(experience.rank_in_diploma, '10 on 100')
        self.assertEqual(experience.expected_graduation_date, datetime.date(2024, 1, 1))
        self.assertEqual(experience.dissertation_title, 'The new title')
        self.assertEqual(experience.dissertation_score, 'A')
        self.assertEqual(experience.dissertation_summary, [self.files_uuids['dissertation_summary']])

        years = experience.educationalexperienceyear_set.all().order_by('academic_year__year')

        self.assertEqual(len(years), 2)
        self.assertEqual(years[0].academic_year, self.academic_years[2])
        self.assertEqual(years[0].result, Result.SUCCESS.name)
        self.assertEqual(years[0].registered_credit_number, 30)
        self.assertEqual(years[0].acquired_credit_number, 29)
        self.assertEqual(years[0].transcript, [])
        self.assertEqual(years[0].transcript_translation, [])

        self.assertEqual(years[0].with_block_1, None)
        self.assertEqual(years[0].with_complement, None)
        self.assertEqual(years[0].fwb_registered_credit_number, None)
        self.assertEqual(years[0].fwb_acquired_credit_number, None)
        self.assertEqual(years[0].reduction, Reduction.A150.name)
        self.assertEqual(years[0].is_102_change_of_course, None)

        self.assertEqual(years[1].academic_year, self.academic_years[3])
        self.assertEqual(years[1].result, '')
        self.assertEqual(years[1].registered_credit_number, None)
        self.assertEqual(years[1].acquired_credit_number, None)
        self.assertEqual(years[1].transcript, [])
        self.assertEqual(years[1].transcript_translation, [])
        self.assertEqual(years[1].with_block_1, None)
        self.assertEqual(years[1].with_complement, None)
        self.assertEqual(years[1].fwb_registered_credit_number, None)
        self.assertEqual(years[1].fwb_acquired_credit_number, None)
        self.assertEqual(years[1].reduction, '')
        self.assertEqual(years[1].is_102_change_of_course, None)
