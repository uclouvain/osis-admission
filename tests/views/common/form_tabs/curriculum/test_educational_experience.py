# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid
from unittest import mock

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext
from rest_framework import status

from admission.constants import PDF_MIME_TYPE, FIELD_REQUIRED_MESSAGE
from admission.contrib.models.base import AdmissionEducationalValuatedExperiences
from admission.contrib.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.tests.factories.curriculum import EducationalExperienceFactory, EducationalExperienceYearFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.forms.utils.choice_field import BLANK_CHOICE_DISPLAY
from base.models.academic_year import AcademicYear
from base.models.campus import Campus
from base.models.enums.community import CommunityEnum
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from osis_profile.models import EducationalExperience, EducationalExperienceYear
from osis_profile.models.enums.curriculum import TranscriptType, Result, EvaluationSystem
from reference.models.enums.cycle import Cycle
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.diploma_title import DiplomaTitleFactory
from reference.tests.factories.language import LanguageFactory


class CurriculumEducationalExperienceFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        cls.old_academic_years = [AcademicYearFactory(year=year) for year in [2003, 2004, 2005, 2006, 2007]]
        cls.be_country = CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')
        cls.fr_country = CountryFactory(iso_code='FR', name='France', name_en='France')
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        cls.louvain_campus = Campus.objects.get(external_id=CampusFactory(name='Louvain-la-Neuve').external_id)
        cls.other_campus = Campus.objects.get(external_id=CampusFactory(name='Other').external_id)
        EntityVersionFactory(entity=first_doctoral_commission)
        cls.greek = LanguageFactory(code='EL')
        cls.french = LanguageFactory(code='FR')

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=cls.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__country_of_citizenship=CountryFactory(european_union=False),
            candidate__graduated_from_high_school_year=None,
            candidate__last_registration_year=None,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
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

    def setUp(self):
        # Create data
        self.experience: EducationalExperience = EducationalExperienceFactory(
            person=self.general_admission.candidate,
            country=self.be_country,
            program=self.first_cycle_diploma,
            fwb_equivalent_program=self.first_cycle_diploma,
            institute=self.first_institute,
            linguistic_regime=self.french,
            education_name='Computer science',
            institute_name='University of Louvain',
            institute_address='Rue de Louvain, 1000 Bruxelles',
            expected_graduation_date=datetime.date(2024, 1, 1),
        )
        self.first_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=self.experience,
            academic_year=self.academic_years[0],
            with_block_1=True,
            with_reduction=False,
            is_102_change_of_course=True,
        )
        self.second_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=self.experience,
            academic_year=self.academic_years[2],
            with_complement=True,
            with_reduction=True,
        )

        # Mock osis document api
        patcher = mock.patch("osis_document.api.utils.get_remote_token", side_effect=lambda value, **kwargs: value)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value: value

        # Targeted url
        self.form_url = resolve_url(
            'admission:general-education:update:curriculum:educational',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )
        self.create_url = resolve_url(
            'admission:general-education:update:curriculum:educational_create',
            uuid=self.general_admission.uuid,
        )

    def test_update_curriculum_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # > Base form
        base_form = response.context['base_form']

        # Start
        self.assertEqual(base_form['start'].value(), self.academic_years[0].year)

        all_past_academic_years = AcademicYear.objects.filter(year__lte=2023).order_by('-year')

        academic_year_choices = [('', BLANK_CHOICE_DISPLAY)] + [
            (academic_year.year, f'{academic_year.year}-{academic_year.year + 1}')
            for academic_year in all_past_academic_years
        ]

        self.assertEqual([(c[0], c[1]) for c in base_form.fields['start'].choices], academic_year_choices)

        # End
        self.assertEqual(base_form['end'].value(), self.academic_years[2].year)
        self.assertEqual([(c[0], c[1]) for c in base_form.fields['end'].choices], academic_year_choices)

        # Country
        self.assertEqual(base_form['country'].value(), self.experience.country.iso_code)
        self.assertEqual(
            getattr(base_form.fields['country'], 'is_ue_country', None),
            self.experience.country.european_union,
        )

        # Institute
        self.assertEqual(base_form['other_institute'].value(), True)
        self.assertEqual(base_form['institute_name'].value(), self.experience.institute_name)
        self.assertEqual(base_form['institute_address'].value(), self.experience.institute_address)
        self.assertEqual(base_form['institute'].value(), self.experience.institute.pk)
        self.assertEqual(getattr(base_form.fields['institute'], 'community', None), self.experience.institute.community)

        # Program
        self.assertEqual(base_form['program'].value(), self.experience.program.pk)
        self.assertEqual(getattr(base_form.fields['program'], 'cycle', None), self.experience.program.cycle)
        self.assertEqual(base_form['fwb_equivalent_program'].value(), self.experience.fwb_equivalent_program.pk)
        self.assertEqual(
            getattr(base_form.fields['fwb_equivalent_program'], 'cycle', None),
            self.experience.fwb_equivalent_program.cycle,
        )
        self.assertEqual(base_form['other_program'].value(), True)
        self.assertEqual(base_form['education_name'].value(), self.experience.education_name)

        # Evaluation type
        self.assertEqual(base_form['evaluation_type'].value(), self.experience.evaluation_type)

        # Linguistic regime
        self.assertEqual(base_form['linguistic_regime'].value(), self.experience.linguistic_regime.code)

        # Transcript type
        self.assertEqual(base_form['transcript_type'].value(), self.experience.transcript_type)

        # Obtained diploma
        self.assertEqual(base_form['obtained_diploma'].value(), self.experience.obtained_diploma)

        # Obtained grade
        self.assertEqual(base_form['obtained_grade'].value(), self.experience.obtained_grade)

        # Graduate degree
        self.assertEqual(base_form['graduate_degree'].value(), self.experience.graduate_degree)

        # Graduate degree translation
        self.assertEqual(base_form['graduate_degree_translation'].value(), self.experience.graduate_degree_translation)

        # Transcript
        self.assertEqual(base_form['transcript'].value(), self.experience.transcript)

        # Transcript translation
        self.assertEqual(base_form['transcript_translation'].value(), self.experience.transcript_translation)

        # Rank in diploma
        self.assertEqual(base_form['rank_in_diploma'].value(), self.experience.rank_in_diploma)

        # Expected graduation date
        self.assertEqual(base_form['expected_graduation_date'].value(), self.experience.expected_graduation_date)

        # Dissertation title
        self.assertEqual(base_form['dissertation_title'].value(), self.experience.dissertation_title)

        # Dissertation score
        self.assertEqual(base_form['dissertation_score'].value(), self.experience.dissertation_score)

        # Dissertation summary
        self.assertEqual(base_form['dissertation_summary'].value(), self.experience.dissertation_summary)

        # Check disabled fields
        for field in base_form.fields:
            if field in {
                'rank_in_diploma',
                'expected_graduation_date',
                'dissertation_title',
                'dissertation_score',
                'dissertation_summary',
            }:
                self.assertTrue(base_form.fields[field].disabled, f'Field "{field}" should be disabled')
            else:
                self.assertFalse(base_form.fields[field].disabled, f'Field "{field}" should not be disabled')

        # > Year forms
        year_formset = response.context['year_formset']

        self.assertEqual(len(year_formset), 3)

        first_year_form = year_formset[2]
        second_year_form = year_formset[1]
        third_year_form = year_formset[0]

        # Academic year
        self.assertEqual(third_year_form['academic_year'].value(), self.academic_years[2].year)
        self.assertEqual(second_year_form['academic_year'].value(), self.academic_years[1].year)
        self.assertEqual(first_year_form['academic_year'].value(), self.academic_years[0].year)

        # Is enrolled
        self.assertEqual(third_year_form['is_enrolled'].value(), True)
        self.assertEqual(second_year_form['is_enrolled'].value(), False)
        self.assertEqual(first_year_form['is_enrolled'].value(), True)

        # Result
        self.assertEqual(third_year_form['result'].value(), self.second_experience_year.result)
        self.assertEqual(second_year_form['result'].value(), None)
        self.assertEqual(first_year_form['result'].value(), self.first_experience_year.result)

        # Registered credit number
        self.assertEqual(
            third_year_form['registered_credit_number'].value(), self.second_experience_year.registered_credit_number
        )
        self.assertEqual(second_year_form['registered_credit_number'].value(), None)
        self.assertEqual(
            first_year_form['registered_credit_number'].value(), self.first_experience_year.registered_credit_number
        )

        # Acquired credit hours
        self.assertEqual(
            third_year_form['acquired_credit_number'].value(), self.second_experience_year.acquired_credit_number
        )
        self.assertEqual(second_year_form['acquired_credit_number'].value(), None)
        self.assertEqual(
            first_year_form['acquired_credit_number'].value(), self.first_experience_year.acquired_credit_number
        )

        # Transcript
        self.assertEqual(third_year_form['transcript'].value(), self.second_experience_year.transcript)
        self.assertEqual(second_year_form['transcript'].value(), [])
        self.assertEqual(first_year_form['transcript'].value(), self.first_experience_year.transcript)

        # Transcript translation
        self.assertEqual(
            third_year_form['transcript_translation'].value(),
            self.second_experience_year.transcript_translation,
        )
        self.assertEqual(second_year_form['transcript_translation'].value(), [])
        self.assertEqual(
            first_year_form['transcript_translation'].value(),
            self.first_experience_year.transcript_translation,
        )

        # With block 1
        self.assertEqual(third_year_form['with_block_1'].value(), self.second_experience_year.with_block_1)
        self.assertEqual(second_year_form['with_block_1'].value(), None)
        self.assertEqual(first_year_form['with_block_1'].value(), self.first_experience_year.with_block_1)

        # With complement
        self.assertEqual(third_year_form['with_complement'].value(), self.second_experience_year.with_complement)
        self.assertEqual(second_year_form['with_complement'].value(), None)
        self.assertEqual(first_year_form['with_complement'].value(), self.first_experience_year.with_complement)

        # Fwb registered credit number
        self.assertEqual(
            third_year_form['fwb_registered_credit_number'].value(),
            self.second_experience_year.fwb_registered_credit_number,
        )
        self.assertEqual(second_year_form['fwb_registered_credit_number'].value(), None)
        self.assertEqual(
            first_year_form['fwb_registered_credit_number'].value(),
            self.first_experience_year.fwb_registered_credit_number,
        )

        # Fwb acquired credit number
        self.assertEqual(
            third_year_form['fwb_acquired_credit_number'].value(),
            self.second_experience_year.fwb_acquired_credit_number,
        )
        self.assertEqual(second_year_form['fwb_acquired_credit_number'].value(), None)
        self.assertEqual(
            first_year_form['fwb_acquired_credit_number'].value(),
            self.first_experience_year.fwb_acquired_credit_number,
        )

        # With reduction
        self.assertEqual(third_year_form['with_reduction'].value(), self.second_experience_year.with_reduction)
        self.assertEqual(second_year_form['with_reduction'].value(), None)
        self.assertEqual(first_year_form['with_reduction'].value(), self.first_experience_year.with_reduction)

        # Is 102 change of course
        self.assertEqual(
            third_year_form['is_102_change_of_course'].value(),
            self.second_experience_year.is_102_change_of_course,
        )
        self.assertEqual(second_year_form['is_102_change_of_course'].value(), None)
        self.assertEqual(
            first_year_form['is_102_change_of_course'].value(),
            self.first_experience_year.is_102_change_of_course,
        )

        # Check that the fields are not disabled
        for form in year_formset:
            for field in form.fields:
                self.assertFalse(form.fields[field].disabled, f'Field "{field}" should not be disabled')

    def test_submit_form_with_no_data(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'myfield': 'myvalue',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.is_valid(), False)

        missing_fields = [
            'start',
            'end',
            'country',
            'institute',
            'evaluation_type',
            'transcript_type',
            'obtained_diploma',
        ]

        for field in missing_fields:
            self.assertIn(FIELD_REQUIRED_MESSAGE, base_form.errors.get(field, []), field)

        year_formset = response.context['year_formset']

        self.assertEqual(year_formset.is_valid(), False)
        self.assertEqual(year_formset.management_form.is_valid(), False)

    def test_submit_form_with_invalid_dates(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'base_form-start': '2021',
                'base_form-end': '2020',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.is_valid(), False)

        self.assertIn(
            gettext("The start date must be earlier than or the same as the end date."),
            base_form.errors.get('__all__', []),
        )

    def test_submit_form_with_invalid_institute(self):
        self.client.force_login(self.sic_manager_user)

        # Other institute fields are missing
        response = self.client.post(
            self.form_url,
            data={
                'base_form-other_institute': True,
                'base_form-institute': self.experience.institute.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.is_valid(), False)

        self.assertIn(FIELD_REQUIRED_MESSAGE, base_form.errors.get('institute_name', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, base_form.errors.get('institute_address', []))

        self.assertEqual(base_form.cleaned_data['institute'], None)

        # Institute field is missing
        response = self.client.post(
            self.form_url,
            data={
                'base_form-other_institute': False,
                'base_form-institute_name': 'Institute name',
                'base_form-institute_address': 'Institute address',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.is_valid(), False)

        self.assertIn(FIELD_REQUIRED_MESSAGE, base_form.errors.get('institute', []))

        self.assertEqual(base_form.cleaned_data['institute_name'], '')
        self.assertEqual(base_form.cleaned_data['institute_address'], '')

    def test_submit_form_with_invalid_diploma_info(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'base_form-obtained_diploma': True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.is_valid(), False)

        self.assertIn(FIELD_REQUIRED_MESSAGE, base_form.errors.get('obtained_grade', []))

        # Clean additional data if no obtained diploma
        response = self.client.post(
            self.form_url,
            data={
                'base_form-obtained_diploma': False,
                'base_form-expected_graduation_date': '2021-01-01',
                'base_form-dissertation_title': 'Title',
                'base_form-dissertation_score': '1',
                'base_form-dissertation_summary_0': ['uuid1'],
                'base_form-graduate_degree_0': ['uuid2'],
                'base_form-graduate_degree_translation_0': ['uuid3'],
                'base_form-rank_in_diploma': 'My rank',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['expected_graduation_date'], None)
        self.assertEqual(base_form.cleaned_data['dissertation_title'], '')
        self.assertEqual(base_form.cleaned_data['dissertation_score'], '')
        self.assertEqual(base_form.cleaned_data['dissertation_summary'], [])
        self.assertEqual(base_form.cleaned_data['graduate_degree'], [])
        self.assertEqual(base_form.cleaned_data['graduate_degree_translation'], [])
        self.assertEqual(base_form.cleaned_data['rank_in_diploma'], '')

    def test_submit_form_with_invalid_be_country_info(self):
        self.client.force_login(self.sic_manager_user)

        # Program missing
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'BE',
                'base_form-education_name': 'Education name',
                'base_form-linguistic_regime': 'FR',
                'base_form-graduate_degree_translation_0': ['uuid3'],
                'base_form-transcript_translation_0': ['uuid4'],
                'base_form-fwb_equivalent_program': self.experience.fwb_equivalent_program.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.is_valid(), False)

        self.assertIn(FIELD_REQUIRED_MESSAGE, base_form.errors.get('program', []))

        self.assertEqual(base_form.cleaned_data['education_name'], '')
        self.assertEqual(base_form.cleaned_data['linguistic_regime'], None)
        self.assertEqual(base_form.cleaned_data['graduate_degree_translation'], [])
        self.assertEqual(base_form.cleaned_data['transcript_translation'], [])
        self.assertEqual(base_form.cleaned_data['fwb_equivalent_program'], None)

        # Other program missing
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'BE',
                'base_form-other_program': True,
                'base_form-education_name': '',
                'base_form-program': self.experience.program.pk,
                'base_form-linguistic_regime': 'FR',
                'base_form-graduate_degree_translation_0': ['uuid3'],
                'base_form-transcript_translation_0': ['uuid4'],
                'base_form-fwb_equivalent_program': self.experience.fwb_equivalent_program.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.is_valid(), False)

        self.assertIn(FIELD_REQUIRED_MESSAGE, base_form.errors.get('education_name', []))

        self.assertEqual(base_form.cleaned_data['program'], None)
        self.assertEqual(base_form.cleaned_data['linguistic_regime'], None)
        self.assertEqual(base_form.cleaned_data['graduate_degree_translation'], [])
        self.assertEqual(base_form.cleaned_data['transcript_translation'], [])

    def test_submit_form_with_invalid_foreign_country_info(self):
        self.client.force_login(self.sic_manager_user)

        # Program missing
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'FR',
                'base_form-program': self.experience.program.pk,
                'base_form-graduate_degree_translation_0': ['uuid3'],
                'base_form-transcript_translation_0': ['uuid4'],
                'base_form-fwb_equivalent_program': self.experience.fwb_equivalent_program.pk,
                'base_form-obtained_diploma': True,
                'base_form-transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.is_valid(), False)

        self.assertIn(FIELD_REQUIRED_MESSAGE, base_form.errors.get('education_name', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, base_form.errors.get('linguistic_regime', []))

        self.assertEqual(base_form.cleaned_data['graduate_degree_translation'], [])
        self.assertEqual(base_form.cleaned_data['transcript_translation'], [])
        self.assertEqual(base_form.cleaned_data['program'], None)

        # Missing translations
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'FR',
                'base_form-other_program': True,
                'base_form-education_name': 'Bachelor',
                'base_form-program': self.experience.program.pk,
                'base_form-linguistic_regime': 'EL',
                'base_form-graduate_degree_translation_0': ['uuid3'],
                'base_form-transcript_translation_0': ['uuid4'],
                'base_form-fwb_equivalent_program': self.experience.fwb_equivalent_program.pk,
                'base_form-obtained_diploma': True,
                'base_form-transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.is_valid(), False)

        self.assertEqual(base_form.cleaned_data['program'], None)
        self.assertEqual(base_form.cleaned_data['graduate_degree_translation'], ['uuid3'])
        self.assertEqual(base_form.cleaned_data['transcript_translation'], ['uuid4'])

    def test_submit_form_with_no_enrolled_year(self):
        self.client.force_login(self.sic_manager_user)

        # No specified year
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'BE',
                'base_form-start': 2020,
                'base_form-end': 2021,
                'year_formset-TOTAL_FORMS': 0,
                'year_formset-INITIAL_FORMS': 0,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.is_valid(), False)

        self.assertIn(
            gettext('At least one academic year is required.'),
            base_form.errors.get('__all__', []),
        )

        # No enrolled year
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'BE',
                'base_form-start': 2020,
                'base_form-end': 2021,
                'year_formset-TOTAL_FORMS': 2,
                'year_formset-INITIAL_FORMS': 2,
                'year_formset-2020-academic_year': 2020,
                'year_formset-2021-academic_year': 2021,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.is_valid(), False)

        self.assertIn(
            gettext('At least one academic year is required.'),
            base_form.errors.get('__all__', []),
        )

    def test_submit_form_with_incomplete_credits(self):
        self.client.force_login(self.sic_manager_user)

        # In Belgium, credits are required since 2004
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'BE',
                'base_form-start': 2003,
                'base_form-end': 2006,
                'year_formset-TOTAL_FORMS': 4,
                'year_formset-INITIAL_FORMS': 4,
                'year_formset-2003-academic_year': 2003,
                'year_formset-2003-is_enrolled': True,
                'year_formset-2003-result': Result.SUCCESS.name,
                'year_formset-2004-academic_year': 2004,
                'year_formset-2004-is_enrolled': True,
                'year_formset-2004-result': Result.SUCCESS.name,
                'year_formset-2005-academic_year': 2005,
                'year_formset-2006-academic_year': 2006,
                'year_formset-2006-is_enrolled': True,
                'year_formset-2006-result': Result.SUCCESS.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        year_formset = response.context['year_formset']

        self.assertEqual(year_formset.is_valid(), False)

        self.assertEqual(len(year_formset.forms), 4)

        form_2006, form_2005, form_2004, form_2003 = year_formset.forms

        self.assertEqual(form_2003.is_valid(), True)
        self.assertEqual(form_2005.is_valid(), True)  # Valid because not enrolled

        for form in [form_2004, form_2006]:
            self.assertEqual(form.is_valid(), False)

            for field in [
                'acquired_credit_number',
                'registered_credit_number',
            ]:
                self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get(field, []), f'{field} must be required')

        self.assertEqual(base_form.cleaned_data['evaluation_type'], EvaluationSystem.ECTS_CREDITS.name)

        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'BE',
                'base_form-start': 2003,
                'base_form-end': 2003,
                'year_formset-TOTAL_FORMS': 1,
                'year_formset-INITIAL_FORMS': 1,
                'year_formset-2003-academic_year': 2003,
                'year_formset-2003-is_enrolled': True,
                'year_formset-2003-result': Result.SUCCESS.name,
                'year_formset-2003-acquired_credit_number': 10,
                'year_formset-2003-registered_credit_number': 10,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['evaluation_type'], EvaluationSystem.NO_CREDIT_SYSTEM.name)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]
        self.assertEqual(first_form.cleaned_data['acquired_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['registered_credit_number'], None)

        # For other countries, credits depends on the evaluation type
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'FR',
                'base_form-start': 2003,
                'base_form-end': 2004,
                'base_form-evaluation_type': EvaluationSystem.NON_EUROPEAN_CREDITS.name,
                'year_formset-TOTAL_FORMS': 2,
                'year_formset-INITIAL_FORMS': 2,
                'year_formset-2003-academic_year': 2003,
                'year_formset-2003-is_enrolled': True,
                'year_formset-2003-result': Result.SUCCESS.name,
                'year_formset-2004-academic_year': 2004,
                'year_formset-2004-is_enrolled': True,
                'year_formset-2004-result': Result.SUCCESS.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']

        for form in year_formset.forms:
            self.assertEqual(form.is_valid(), False)

            for field in [
                'acquired_credit_number',
                'registered_credit_number',
            ]:
                self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get(field, []), f'{field} must be required')

        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'FR',
                'base_form-start': 2003,
                'base_form-end': 2004,
                'base_form-evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'year_formset-TOTAL_FORMS': 2,
                'year_formset-INITIAL_FORMS': 2,
                'year_formset-2003-academic_year': 2003,
                'year_formset-2003-is_enrolled': True,
                'year_formset-2003-result': Result.SUCCESS.name,
                'year_formset-2004-academic_year': 2004,
                'year_formset-2004-is_enrolled': True,
                'year_formset-2004-result': Result.SUCCESS.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']

        for form in year_formset.forms:
            self.assertEqual(form.is_valid(), False)

            for field in [
                'acquired_credit_number',
                'registered_credit_number',
            ]:
                self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get(field, []), f'{field} must be required')

        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'FR',
                'base_form-start': 2003,
                'base_form-end': 2004,
                'base_form-evaluation_type': EvaluationSystem.NO_CREDIT_SYSTEM.name,
                'year_formset-TOTAL_FORMS': 2,
                'year_formset-INITIAL_FORMS': 2,
                'year_formset-2003-academic_year': 2003,
                'year_formset-2003-is_enrolled': True,
                'year_formset-2003-result': Result.SUCCESS.name,
                'year_formset-2004-academic_year': 2004,
                'year_formset-2004-is_enrolled': True,
                'year_formset-2004-result': Result.SUCCESS.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']

        for form in year_formset.forms:
            self.assertEqual(form.is_valid(), True)
            form.cleaned_data['acquired_credit_number'] = None
            form.cleaned_data['registered_credit_number'] = None

    def test_submit_form_with_invalid_credits(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'BE',
                'base_form-start': 2004,
                'base_form-end': 2007,
                'year_formset-TOTAL_FORMS': 4,
                'year_formset-INITIAL_FORMS': 4,
                'year_formset-2004-academic_year': 2004,
                'year_formset-2004-is_enrolled': True,
                'year_formset-2004-result': Result.SUCCESS.name,
                'year_formset-2004-acquired_credit_number': 0,
                'year_formset-2004-registered_credit_number': 0,
                'year_formset-2005-academic_year': 2005,
                'year_formset-2005-is_enrolled': True,
                'year_formset-2005-result': Result.SUCCESS.name,
                'year_formset-2005-acquired_credit_number': 15,
                'year_formset-2005-registered_credit_number': 10,
                'year_formset-2006-academic_year': 2006,
                'year_formset-2006-is_enrolled': True,
                'year_formset-2006-result': Result.SUCCESS.name,
                'year_formset-2006-acquired_credit_number': 10,
                'year_formset-2006-registered_credit_number': 10,
                'year_formset-2007-academic_year': 2007,
                'year_formset-2007-is_enrolled': True,
                'year_formset-2007-result': Result.SUCCESS.name,
                'year_formset-2007-acquired_credit_number': 0,
                'year_formset-2007-registered_credit_number': 10,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']

        self.assertEqual(year_formset.is_valid(), False)

        self.assertEqual(len(year_formset.forms), 4)

        form_2007, form_2006, form_2005, form_2004 = year_formset.forms

        self.assertEqual(form_2007.is_valid(), True)
        self.assertEqual(form_2006.is_valid(), True)
        self.assertEqual(form_2005.is_valid(), False)
        self.assertIn('acquired_credit_number', form_2005.errors)
        self.assertEqual(form_2004.is_valid(), False)
        self.assertIn('registered_credit_number', form_2004.errors)

    def test_submit_or_not_the_transcripts(self):
        self.client.force_login(self.sic_manager_user)

        file_uuid = str(uuid.uuid4())

        # Global Transcript
        response = self.client.post(
            self.form_url,
            data={
                'base_form-transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'base_form-transcript_0': [file_uuid],
                'base_form-transcript_translation_0': [file_uuid],
                'base_form-start': 2020,
                'base_form-end': 2020,
                'base_form-country': 'FR',
                'base_form-linguistic_regime': 'EL',
                'year_formset-TOTAL_FORMS': 1,
                'year_formset-INITIAL_FORMS': 1,
                'year_formset-2020-academic_year': 2020,
                'year_formset-2020-is_enrolled': True,
                'year_formset-2020-transcript_0': [file_uuid],
                'year_formset-2020-transcript_translation_0': [file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['transcript'], [file_uuid])
        self.assertEqual(base_form.cleaned_data['transcript_translation'], [file_uuid])

        year_formset = response.context['year_formset']

        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['transcript'], [])
        self.assertEqual(first_form.cleaned_data['transcript_translation'], [])

        # Global transcript without translation because in belgium
        response = self.client.post(
            self.form_url,
            data={
                'base_form-transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'base_form-transcript_0': [file_uuid],
                'base_form-transcript_translation_0': [file_uuid],
                'base_form-country': 'BE',
                'base_form-linguistic_regime': 'EL',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['transcript'], [file_uuid])
        self.assertEqual(base_form.cleaned_data['transcript_translation'], [])

        # Global transcript without translation because the language doesn't require it
        response = self.client.post(
            self.form_url,
            data={
                'base_form-transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'base_form-transcript_0': [file_uuid],
                'base_form-transcript_translation_0': [file_uuid],
                'base_form-country': 'FR',
                'base_form-linguistic_regime': 'FR',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['transcript'], [file_uuid])
        self.assertEqual(base_form.cleaned_data['transcript_translation'], [])

        # Individual Transcript
        response = self.client.post(
            self.form_url,
            data={
                'base_form-transcript_type': TranscriptType.ONE_A_YEAR.name,
                'base_form-transcript_0': [file_uuid],
                'base_form-start': 2020,
                'base_form-end': 2020,
                'base_form-country': 'FR',
                'base_form-linguistic_regime': 'EL',
                'year_formset-TOTAL_FORMS': 1,
                'year_formset-INITIAL_FORMS': 1,
                'year_formset-2020-academic_year': 2020,
                'year_formset-2020-is_enrolled': True,
                'year_formset-2020-transcript_0': [file_uuid],
                'year_formset-2020-transcript_translation_0': [file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['transcript'], [])
        self.assertEqual(base_form.cleaned_data['transcript_translation'], [])

        year_formset = response.context['year_formset']

        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['transcript'], [file_uuid])
        self.assertEqual(first_form.cleaned_data['transcript_translation'], [file_uuid])

        # Individual Transcript without translation because in belgium
        response = self.client.post(
            self.form_url,
            data={
                'base_form-transcript_type': TranscriptType.ONE_A_YEAR.name,
                'base_form-transcript_0': [file_uuid],
                'base_form-start': 2020,
                'base_form-end': 2020,
                'base_form-country': 'BE',
                'base_form-linguistic_regime': 'EL',
                'year_formset-TOTAL_FORMS': 1,
                'year_formset-INITIAL_FORMS': 1,
                'year_formset-2020-academic_year': 2020,
                'year_formset-2020-is_enrolled': True,
                'year_formset-2020-transcript_0': [file_uuid],
                'year_formset-2020-transcript_translation_0': [file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['transcript'], [])
        self.assertEqual(base_form.cleaned_data['transcript_translation'], [])

        year_formset = response.context['year_formset']

        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['transcript'], [file_uuid])
        self.assertEqual(first_form.cleaned_data['transcript_translation'], [])

        # Individual Transcript without translation because the language doesn't require it
        response = self.client.post(
            self.form_url,
            data={
                'base_form-transcript_type': TranscriptType.ONE_A_YEAR.name,
                'base_form-transcript_0': [file_uuid],
                'base_form-start': 2020,
                'base_form-end': 2020,
                'base_form-country': 'FR',
                'base_form-linguistic_regime': 'FR',
                'year_formset-TOTAL_FORMS': 1,
                'year_formset-INITIAL_FORMS': 1,
                'year_formset-2020-academic_year': 2020,
                'year_formset-2020-is_enrolled': True,
                'year_formset-2020-transcript_0': [file_uuid],
                'year_formset-2020-transcript_translation_0': [file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['transcript'], [])
        self.assertEqual(base_form.cleaned_data['transcript_translation'], [])

        year_formset = response.context['year_formset']

        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['transcript'], [file_uuid])
        self.assertEqual(first_form.cleaned_data['transcript_translation'], [])

    def test_submit_or_not_the_graduated_degree(self):
        self.client.force_login(self.sic_manager_user)

        file_uuid = str(uuid.uuid4())

        # With obtained diploma
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'FR',
                'base_form-linguistic_regime': 'EL',
                'base_form-obtained_diploma': True,
                'base_form-graduate_degree_0': [file_uuid],
                'base_form-graduate_degree_translation_0': [file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['graduate_degree'], [file_uuid])
        self.assertEqual(base_form.cleaned_data['graduate_degree_translation'], [file_uuid])

        # With obtained diploma without translation because in belgium
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'BE',
                'base_form-linguistic_regime': 'EL',
                'base_form-obtained_diploma': True,
                'base_form-graduate_degree_0': [file_uuid],
                'base_form-graduate_degree_translation_0': [file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['graduate_degree'], [file_uuid])
        self.assertEqual(base_form.cleaned_data['graduate_degree_translation'], [])

        # With obtained diploma without translation because the linguistic regime doesn't require it
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'FR',
                'base_form-linguistic_regime': 'FR',
                'base_form-obtained_diploma': True,
                'base_form-graduate_degree_0': [file_uuid],
                'base_form-graduate_degree_translation_0': [file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['graduate_degree'], [file_uuid])
        self.assertEqual(base_form.cleaned_data['graduate_degree_translation'], [])

        # Without obtained diploma
        response = self.client.post(
            self.form_url,
            data={
                'base_form-country': 'FR',
                'base_form-linguistic_regime': 'EL',
                'base_form-graduate_degree_0': [file_uuid],
                'base_form-graduate_degree_translation_0': [file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        base_form = response.context['base_form']

        self.assertEqual(base_form.cleaned_data['graduate_degree'], [])
        self.assertEqual(base_form.cleaned_data['graduate_degree_translation'], [])

    def test_submit_fwb_bachelor_data_if_necessary(self):
        self.client.force_login(self.sic_manager_user)

        default_data = {
            'base_form-start': 2020,
            'base_form-end': 2020,
            'base_form-obtained_diploma': False,
            'base_form-country': 'BE',
            'base_form-institute': self.experience.institute.pk,
            'base_form-program': self.first_cycle_diploma.pk,
            'base_form-fwb_equivalent_program': self.experience.program.pk,
            'year_formset-TOTAL_FORMS': 1,
            'year_formset-INITIAL_FORMS': 1,
            'year_formset-2020-academic_year': 2020,
            'year_formset-2020-is_enrolled': True,
            'year_formset-2020-with_block_1': True,
            'year_formset-2020-with_complement': True,
            'year_formset-2020-fwb_registered_credit_number': 10,
            'year_formset-2020-fwb_acquired_credit_number': 10,
            'year_formset-2020-is_102_change_of_course': True,
        }

        # No chosen program -> no fwb data
        response = self.client.post(
            self.form_url,
            data={
                **default_data,
                'base_form-program': '',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], None)
        self.assertEqual(first_form.cleaned_data['with_complement'], None)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], None)

        # No chosen institute -> no fwb data
        response = self.client.post(
            self.form_url,
            data={
                **default_data,
                'base_form-institute': '',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], None)
        self.assertEqual(first_form.cleaned_data['with_complement'], None)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], None)

        # Obtained diploma -> no fwb data
        response = self.client.post(
            self.form_url,
            data={
                **default_data,
                'base_form-obtained_diploma': True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], None)
        self.assertEqual(first_form.cleaned_data['with_complement'], None)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], None)

        # No block 1 -> no fwb credits
        copy_data = default_data.copy()
        copy_data.pop('year_formset-2020-with_block_1')
        response = self.client.post(
            self.form_url,
            data=copy_data,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], False)
        self.assertEqual(first_form.cleaned_data['with_complement'], None)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], True)

        # With block 1 -> fwb credits
        response = self.client.post(
            self.form_url,
            data=default_data,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], True)
        self.assertEqual(first_form.cleaned_data['with_complement'], None)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], 10)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], 10)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], True)

        # With first cycle equivalent program -> fwb credits
        response = self.client.post(
            self.form_url,
            data={
                **default_data,
                'base_form-other_program': True,
                'base_form-program': self.second_cycle_diploma.pk,
                'base_form-fwb_equivalent_program': self.first_cycle_diploma.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], True)
        self.assertEqual(first_form.cleaned_data['with_complement'], None)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], 10)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], 10)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], True)

    def test_submit_fwb_master_data_if_necessary(self):
        self.client.force_login(self.sic_manager_user)

        default_data = {
            'base_form-start': 2020,
            'base_form-end': 2020,
            'base_form-obtained_diploma': False,
            'base_form-country': 'BE',
            'base_form-institute': self.experience.institute.pk,
            'base_form-program': self.second_cycle_diploma.pk,
            'base_form-fwb_equivalent_program': self.second_cycle_diploma.pk,
            'year_formset-TOTAL_FORMS': 1,
            'year_formset-INITIAL_FORMS': 1,
            'year_formset-2020-academic_year': 2020,
            'year_formset-2020-is_enrolled': True,
            'year_formset-2020-with_block_1': True,
            'year_formset-2020-with_complement': True,
            'year_formset-2020-fwb_registered_credit_number': 10,
            'year_formset-2020-fwb_acquired_credit_number': 10,
            'year_formset-2020-is_102_change_of_course': True,
        }

        # No chosen program -> no fwb data
        response = self.client.post(
            self.form_url,
            data={
                **default_data,
                'base_form-program': '',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], None)
        self.assertEqual(first_form.cleaned_data['with_complement'], None)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], None)

        # No chosen institute -> no fwb data
        response = self.client.post(
            self.form_url,
            data={
                **default_data,
                'base_form-institute': '',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], None)
        self.assertEqual(first_form.cleaned_data['with_complement'], None)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], None)

        # Obtained diploma -> no fwb data
        response = self.client.post(
            self.form_url,
            data={
                **default_data,
                'base_form-obtained_diploma': True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], None)
        self.assertEqual(first_form.cleaned_data['with_complement'], None)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], None)

        # No complement -> no fwb credits
        copy_data = default_data.copy()
        copy_data.pop('year_formset-2020-with_complement')
        response = self.client.post(
            self.form_url,
            data=copy_data,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], None)
        self.assertEqual(first_form.cleaned_data['with_complement'], False)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], None)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], None)

        # With complement -> fwb credits
        response = self.client.post(
            self.form_url,
            data=default_data,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], None)
        self.assertEqual(first_form.cleaned_data['with_complement'], True)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], 10)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], 10)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], None)

        # With second cycle equivalent program -> fwb credits
        response = self.client.post(
            self.form_url,
            data={
                **default_data,
                'base_form-program': self.first_cycle_diploma.pk,
                'base_form-other_program': True,
                'base_form-fwb_equivalent_program': self.second_cycle_diploma.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        year_formset = response.context['year_formset']
        first_form = year_formset.forms[0]

        self.assertEqual(first_form.cleaned_data['with_block_1'], None)
        self.assertEqual(first_form.cleaned_data['with_complement'], True)
        self.assertEqual(first_form.cleaned_data['fwb_registered_credit_number'], 10)
        self.assertEqual(first_form.cleaned_data['fwb_acquired_credit_number'], 10)
        self.assertEqual(first_form.cleaned_data['is_102_change_of_course'], None)

    def test_post_form_with_existing_years(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'base_form-start': 2020,
                'base_form-end': 2021,
                'base_form-country': 'BE',
                'base_form-institute': self.second_institute.pk,
                'base_form-evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'base_form-transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'base_form-program': self.second_cycle_diploma.pk,
                'base_form-obtained_diploma': False,
                'year_formset-TOTAL_FORMS': 2,
                'year_formset-INITIAL_FORMS': 3,
                'year_formset-2020-academic_year': 2020,
                'year_formset-2020-is_enrolled': True,
                'year_formset-2020-result': Result.SUCCESS.name,
                'year_formset-2020-acquired_credit_number': 10,
                'year_formset-2020-registered_credit_number': 10,
                'year_formset-2021-academic_year': 2021,
                'year_formset-2021-is_enrolled': True,
                'year_formset-2021-result': Result.SUCCESS.name,
                'year_formset-2021-acquired_credit_number': 20,
                'year_formset-2021-registered_credit_number': 20,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check the updated experience
        self.experience.refresh_from_db()

        self.assertEqual(self.experience.institute, self.second_institute)
        self.assertEqual(self.experience.program, self.second_cycle_diploma)
        self.assertEqual(self.experience.evaluation_type, EvaluationSystem.ECTS_CREDITS.name)
        self.assertEqual(self.experience.transcript_type, TranscriptType.ONE_FOR_ALL_YEARS.name)
        self.assertEqual(self.experience.obtained_diploma, False)

        # Check the years
        years = self.experience.educationalexperienceyear_set.all().order_by('academic_year__year')

        self.assertEqual(len(years), 2)

        self.assertEqual(years[0].academic_year.year, 2020)
        self.assertEqual(years[0].result, Result.SUCCESS.name)
        self.assertEqual(years[0].acquired_credit_number, 10)
        self.assertEqual(years[0].registered_credit_number, 10)

        self.assertEqual(years[1].academic_year.year, 2021)
        self.assertEqual(years[1].result, Result.SUCCESS.name)
        self.assertEqual(years[1].acquired_credit_number, 20)
        self.assertEqual(years[1].registered_credit_number, 20)

    def test_post_form_with_created_and_deleted_years(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'base_form-start': 2004,
                'base_form-end': 2004,
                'base_form-country': 'BE',
                'base_form-institute': self.second_institute.pk,
                'base_form-evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'base_form-transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'base_form-program': self.second_cycle_diploma.pk,
                'base_form-obtained_diploma': False,
                'year_formset-TOTAL_FORMS': 1,
                'year_formset-INITIAL_FORMS': 3,
                'year_formset-2004-academic_year': 2004,
                'year_formset-2004-is_enrolled': True,
                'year_formset-2004-result': Result.SUCCESS.name,
                'year_formset-2004-acquired_credit_number': 10,
                'year_formset-2004-registered_credit_number': 10,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check the updated experience
        self.experience.refresh_from_db()

        self.assertEqual(self.experience.institute, self.second_institute)
        self.assertEqual(self.experience.program, self.second_cycle_diploma)
        self.assertEqual(self.experience.evaluation_type, EvaluationSystem.ECTS_CREDITS.name)
        self.assertEqual(self.experience.transcript_type, TranscriptType.ONE_FOR_ALL_YEARS.name)
        self.assertEqual(self.experience.obtained_diploma, False)

        # Check the years
        years = self.experience.educationalexperienceyear_set.all()

        self.assertEqual(len(years), 1)

        self.assertEqual(years[0].academic_year.year, 2004)
        self.assertEqual(years[0].result, Result.SUCCESS.name)
        self.assertEqual(years[0].acquired_credit_number, 10)
        self.assertEqual(years[0].registered_credit_number, 10)

    def test_post_form_with_created_experience(self):
        self.client.force_login(self.sic_manager_user)

        self.assertFalse(
            EducationalExperience.objects.filter(
                person=self.general_admission.candidate,
                institute=self.second_institute,
            ).exists()
        )

        response = self.client.post(
            self.create_url,
            data={
                'base_form-start': 2004,
                'base_form-end': 2004,
                'base_form-country': 'BE',
                'base_form-institute': self.second_institute.pk,
                'base_form-evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'base_form-transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'base_form-program': self.second_cycle_diploma.pk,
                'base_form-obtained_diploma': False,
                'year_formset-TOTAL_FORMS': 1,
                'year_formset-INITIAL_FORMS': 3,
                'year_formset-2004-academic_year': 2004,
                'year_formset-2004-is_enrolled': True,
                'year_formset-2004-result': Result.SUCCESS.name,
                'year_formset-2004-acquired_credit_number': 10,
                'year_formset-2004-registered_credit_number': 10,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        new_experience = EducationalExperience.objects.filter(
            person=self.general_admission.candidate,
            institute=self.second_institute,
        ).first()

        self.assertIsNotNone(new_experience)

        # Check the created experience
        self.assertEqual(new_experience.institute, self.second_institute)
        self.assertEqual(new_experience.program, self.second_cycle_diploma)
        self.assertEqual(new_experience.evaluation_type, EvaluationSystem.ECTS_CREDITS.name)
        self.assertEqual(new_experience.transcript_type, TranscriptType.ONE_FOR_ALL_YEARS.name)
        self.assertEqual(new_experience.obtained_diploma, False)

        # Check the years
        years = new_experience.educationalexperienceyear_set.all()

        self.assertEqual(len(years), 1)

        self.assertEqual(years[0].academic_year.year, 2004)
        self.assertEqual(years[0].result, Result.SUCCESS.name)
        self.assertEqual(years[0].acquired_credit_number, 10)
        self.assertEqual(years[0].registered_credit_number, 10)

        # Check that the experience has been valuated
        self.assertTrue(
            AdmissionEducationalValuatedExperiences.objects.filter(
                baseadmission_id=self.general_admission.uuid,
                educationalexperience_id=new_experience.uuid,
            ).exists()
        )

        # Check that the checklist has been updated
        self.general_admission.refresh_from_db()

        last_experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][-1]

        self.assertEqual(
            last_experience_checklist['extra']['identifiant'],
            str(new_experience.uuid),
        )

        self.assertEqual(
            last_experience_checklist,
            {
                'libelle': 'To be processed',
                'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                'extra': {
                    'identifiant': str(new_experience.uuid),
                    'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
                    'commentaire_authentification': '',
                },
                'enfants': [],
            },
        )


class CurriculumEducationalExperienceDeleteViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        cls.be_country = CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)
        cls.french = LanguageFactory(code='FR')

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=cls.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__country_of_citizenship=CountryFactory(european_union=False),
            candidate__graduated_from_high_school_year=None,
            candidate__last_registration_year=None,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
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

    def setUp(self):
        # Create data
        self.experience: EducationalExperience = EducationalExperienceFactory(
            person=self.general_admission.candidate,
            country=self.be_country,
            program=self.first_cycle_diploma,
            fwb_equivalent_program=self.first_cycle_diploma,
            institute=self.first_institute,
            linguistic_regime=self.french,
            education_name='Computer science',
            institute_name='University of Louvain',
            institute_address='Rue de Louvain, 1000 Bruxelles',
            expected_graduation_date=datetime.date(2024, 1, 1),
        )
        self.first_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=self.experience,
            academic_year=self.academic_years[0],
            with_block_1=True,
            with_reduction=False,
            is_102_change_of_course=True,
        )
        self.second_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=self.experience,
            academic_year=self.academic_years[2],
            with_complement=True,
            with_reduction=True,
        )
        # Targeted url
        self.delete_url = resolve_url(
            'admission:general-education:update:curriculum:educational_delete',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )

    def test_delete_experience_from_curriculum_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.delete(self.delete_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_experience_from_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.delete(self.delete_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_delete_unknown_experience_returns_404(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.delete(
            resolve_url(
                'admission:general-education:update:curriculum:educational_delete',
                uuid=self.general_admission.uuid,
                experience_uuid=uuid.uuid4(),
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_known_experience(self):
        self.client.force_login(self.sic_manager_user)

        # Simulate a valuated experience
        AdmissionEducationalValuatedExperiences.objects.create(
            baseadmission_id=self.general_admission.uuid,
            educationalexperience_id=self.experience.uuid,
        )

        self.general_admission.checklist['current']['parcours_anterieur']['enfants'] = [
            Checklist.initialiser_checklist_experience(experience_uuid=self.experience.uuid).to_dict()
        ]

        self.general_admission.save()

        response = self.client.delete(self.delete_url)

        self.assertFalse(EducationalExperience.objects.filter(uuid=self.experience.uuid).exists())

        self.assertFalse(
            EducationalExperienceYear.objects.filter(
                educational_experience__uuid=self.experience.uuid,
            ).exists()
        )

        self.assertFalse(
            AdmissionEducationalValuatedExperiences.objects.filter(
                educationalexperience_id=self.experience.uuid
            ).exists()
        )

        self.general_admission.refresh_from_db()

        self.assertEqual(
            self.general_admission.checklist['current']['parcours_anterieur']['enfants'],
            [],
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
