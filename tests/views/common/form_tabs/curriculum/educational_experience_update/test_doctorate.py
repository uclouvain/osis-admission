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

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.models import DoctorateAdmission
from admission.models.base import AdmissionEducationalValuatedExperiences
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
)
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.forms.utils.choice_field import BLANK_CHOICE_DISPLAY
from base.forms.utils.file_field import PDF_MIME_TYPE
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
from osis_profile.models.enums.curriculum import TranscriptType, Result, EvaluationSystem, Reduction, Grade
from reference.models.enums.cycle import Cycle
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.diploma_title import DiplomaTitleFactory
from reference.tests.factories.language import LanguageFactory


# TODO: Remove duplicate tests with osis_profile
class CurriculumEducationalExperienceFormViewForDoctorateTestCase(TestCase):
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

        cls.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=cls.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__country_of_citizenship=CountryFactory(european_union=False),
            candidate__graduated_from_high_school_year=None,
            candidate__last_registration_year=None,
            candidate__id_photo=[],
            submitted=True,
        )

        cls.files_uuids = [[uuid.uuid4()] for _ in range(4)]

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.doctorate_admission.training.education_group,
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
            person=self.doctorate_admission.candidate,
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
            reduction='',
            is_102_change_of_course=True,
        )
        self.second_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=self.experience,
            academic_year=self.academic_years[2],
            with_complement=True,
            reduction=Reduction.A150.name,
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
            'admission:doctorate:update:curriculum:educational',
            uuid=self.doctorate_admission.uuid,
            experience_uuid=self.experience.uuid,
        )
        self.create_url = resolve_url(
            'admission:doctorate:update:curriculum:educational_create',
            uuid=self.doctorate_admission.uuid,
        )

    def test_update_curriculum_is_allowed_for_fac_users(self):
        other_admission = DoctorateAdmissionFactory(
            training=self.doctorate_admission.training,
            candidate=self.doctorate_admission.candidate,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        self.client.force_login(self.program_manager_user)
        response = self.client.get(
            resolve_url(
                'admission:doctorate:update:curriculum:educational',
                uuid=other_admission.uuid,
                experience_uuid=self.experience.uuid,
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

        # Check that no field is disabled
        for field in base_form.fields:
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
        self.assertEqual(third_year_form['reduction'].value(), self.second_experience_year.reduction)
        self.assertEqual(second_year_form['reduction'].value(), None)
        self.assertEqual(first_year_form['reduction'].value(), self.first_experience_year.reduction)

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

        missing_fields = [
            'expected_graduation_date',
            'dissertation_title',
            'dissertation_score',
            'obtained_grade',
        ]

        for field in missing_fields:
            self.assertIn(FIELD_REQUIRED_MESSAGE, base_form.errors.get(field, []), field)

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

    def test_post_form_with_created_experience(self):
        self.client.force_login(self.sic_manager_user)

        self.assertFalse(
            EducationalExperience.objects.filter(
                person=self.doctorate_admission.candidate,
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
                'base_form-expected_graduation_date': '2021-01-01',
                'base_form-dissertation_title': 'Title',
                'base_form-dissertation_score': '1',
                'base_form-dissertation_summary_0': ['uuid1'],
                'base_form-graduate_degree_0': ['uuid2'],
                'base_form-graduate_degree_translation_0': ['uuid3'],
                'base_form-transcript_0': self.files_uuids[0],
                'base_form-rank_in_diploma': 'My rank',
                'year_formset-TOTAL_FORMS': 1,
                'year_formset-INITIAL_FORMS': 0,
                'year_formset-2004-academic_year': 2004,
                'year_formset-2004-is_enrolled': True,
                'year_formset-2004-result': Result.SUCCESS.name,
                'year_formset-2004-acquired_credit_number': 10,
                'year_formset-2004-registered_credit_number': 10,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        new_experience = EducationalExperience.objects.filter(
            person=self.doctorate_admission.candidate,
            institute=self.second_institute,
        ).first()

        self.assertIsNotNone(new_experience)

        # Check the created experience
        self.assertEqual(new_experience.institute, self.second_institute)
        self.assertEqual(new_experience.program, self.second_cycle_diploma)
        self.assertEqual(new_experience.evaluation_type, EvaluationSystem.ECTS_CREDITS.name)
        self.assertEqual(new_experience.transcript_type, TranscriptType.ONE_FOR_ALL_YEARS.name)
        self.assertEqual(new_experience.obtained_diploma, False)
        self.assertEqual(new_experience.expected_graduation_date, None)
        self.assertEqual(new_experience.rank_in_diploma, '')
        self.assertEqual(new_experience.dissertation_title, '')
        self.assertEqual(new_experience.dissertation_score, '')
        self.assertEqual(new_experience.dissertation_summary, [])

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
                baseadmission_id=self.doctorate_admission.uuid,
                educationalexperience_id=new_experience.uuid,
            ).exists()
        )

    @freezegun.freeze_time('2023-01-01')
    def test_post_form_with_updated_experience(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'base_form-start': 2021,
                'base_form-end': 2021,
                'base_form-country': 'BE',
                'base_form-institute': self.second_institute.pk,
                'base_form-evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'base_form-transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'base_form-program': self.second_cycle_diploma.pk,
                'base_form-obtained_diploma': True,
                'base_form-obtained_grade': Grade.GREAT_DISTINCTION.name,
                'base_form-expected_graduation_date': '2021-01-01',
                'base_form-dissertation_title': 'Title',
                'base_form-dissertation_score': '1',
                'base_form-dissertation_summary_0': self.files_uuids[0],
                'base_form-graduate_degree_0': self.files_uuids[1],
                'base_form-graduate_degree_translation_0': self.files_uuids[2],
                'base_form-transcript_0': self.files_uuids[3],
                'base_form-rank_in_diploma': 'My rank',
                'year_formset-TOTAL_FORMS': 1,
                'year_formset-INITIAL_FORMS': 3,
                'year_formset-2021-academic_year': 2021,
                'year_formset-2021-is_enrolled': True,
                'year_formset-2021-result': Result.SUCCESS.name,
                'year_formset-2021-acquired_credit_number': 20,
                'year_formset-2021-registered_credit_number': 20,
            },
        )
        print(response)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check the updated experience
        self.experience.refresh_from_db()

        self.assertEqual(self.experience.institute, self.second_institute)
        self.assertEqual(self.experience.program, self.second_cycle_diploma)
        self.assertEqual(self.experience.evaluation_type, EvaluationSystem.ECTS_CREDITS.name)
        self.assertEqual(self.experience.transcript_type, TranscriptType.ONE_FOR_ALL_YEARS.name)
        self.assertEqual(self.experience.obtained_diploma, True)
        self.assertEqual(self.experience.obtained_grade, Grade.GREAT_DISTINCTION.name)
        self.assertEqual(self.experience.expected_graduation_date, datetime.date(2021, 1, 1))
        self.assertEqual(self.experience.rank_in_diploma, 'My rank')
        self.assertEqual(self.experience.dissertation_title, 'Title')
        self.assertEqual(self.experience.dissertation_score, '1')
        self.assertEqual(self.experience.dissertation_summary, self.files_uuids[0])
        self.assertEqual(self.experience.graduate_degree, self.files_uuids[1])
        self.assertEqual(self.experience.graduate_degree_translation, [])

        # Check the years
        years = self.experience.educationalexperienceyear_set.all().order_by('academic_year__year')

        self.assertEqual(len(years), 1)

        self.assertEqual(years[0].academic_year.year, 2021)
        self.assertEqual(years[0].result, Result.SUCCESS.name)
        self.assertEqual(years[0].acquired_credit_number, 20)
        self.assertEqual(years[0].registered_credit_number, 20)

        # Check the admission
        self.doctorate_admission.refresh_from_db()
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)
        self.assertNotIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            self.doctorate_admission.requested_documents,
        )
