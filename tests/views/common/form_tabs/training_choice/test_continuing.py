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

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext_lazy
from rest_framework import status

from admission.ddd.admission.domain.enums import TypeFormation
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    ChoixMoyensDecouverteFormation,
)
from admission.models import ContinuingEducationAdmission
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
    ContinuingEducationTrainingFactory,
)
from admission.tests.factories.form_item import AdmissionFormItemInstantiationFactory, TextAdmissionFormItemFactory
from admission.tests.factories.roles import (
    SicManagementRoleFactory,
    CandidateFactory,
    ProgramManagerRoleFactory,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.models.campus import Campus
from base.models.enums.organization_type import MAIN
from base.models.enums.state_iufc import StateIUFC
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityWithVersionFactory
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2021-12-01')
class ContinuingTrainingChoiceFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.error_message_no_training = gettext_lazy('The selected training has not been found for this year.')

        CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')

        cls.first_campus = CampusFactory(name='Mons', organization__type=MAIN)
        cls.all_campuses = Campus.objects.filter(organization__type=MAIN)

        cls.first_entity = EntityWithVersionFactory()

        cls.specific_questions = [
            AdmissionFormItemInstantiationFactory(
                form_item=TextAdmissionFormItemFactory(),
                tab=Onglets.CHOIX_FORMATION.name,
                academic_year=cls.academic_years[0],
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=TextAdmissionFormItemFactory(),
                tab=Onglets.CURRICULUM.name,
                academic_year=cls.academic_years[0],
            ),
        ]

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_entity).person.user

    def setUp(self):
        self.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__academic_year=self.academic_years[0],
            training__management_entity=self.first_entity,
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__id_photo=[],
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            interested_mark=False,
            ways_to_find_out_about_the_course=[
                ChoixMoyensDecouverteFormation.COURRIER_PERSONNALISE.name,
                ChoixMoyensDecouverteFormation.ANCIENS_ETUDIANTS.name,
            ],
            motivations='My first motivations',
            determined_academic_year=self.academic_years[0],
        )

        version = self.continuing_admission.training.educationgroupversion_set.first()
        version.root_group.main_teaching_campus = self.first_campus
        version.root_group.save(update_fields=['main_teaching_campus'])

        self.program_manager_user = ProgramManagerRoleFactory(
            education_group=self.continuing_admission.training.education_group
        ).person.user

        self.other_training_other_entity = ContinuingEducationTrainingFactory(
            management_entity=EntityWithVersionFactory(),
            academic_year=self.academic_years[1],
        )

        self.other_training_same_entity = ContinuingEducationTrainingFactory(
            management_entity=self.first_entity,
            academic_year=self.academic_years[1],
        )

        self.admission_form_url = resolve_url(
            'admission:continuing-education:update:training-choice',
            uuid=self.continuing_admission.uuid,
        )
        self.admission_detail_url = resolve_url(
            'admission:continuing-education:training-choice',
            uuid=self.continuing_admission.uuid,
        )

    def test_training_choice_access(self):
        # If the user is not authenticated, he should be redirected to the login page
        response = self.client.get(self.admission_form_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + self.admission_form_url)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(self.admission_form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, he should be able to access the page
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.admission_form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.admission_form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_training_choice_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.admission_form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check initial data
        form = response.context['form']

        self.assertEqual(
            form['continuing_education_training'].value(),
            self.continuing_admission.training.acronym,
        )
        self.assertEqual(form['academic_year'].value(), self.continuing_admission.determined_academic_year.year)
        self.assertEqual(form['campus'].value(), self.first_campus.uuid)
        self.assertEqual(form['training_type'].value(), TypeFormation.FORMATION_CONTINUE.name)
        self.assertEqual(form['motivations'].value(), 'My first motivations')
        self.assertCountEqual(
            form['ways_to_find_out_about_the_course'].value(),
            [
                ChoixMoyensDecouverteFormation.COURRIER_PERSONNALISE.name,
                ChoixMoyensDecouverteFormation.ANCIENS_ETUDIANTS.name,
            ],
        )
        self.assertEqual(form['interested_mark'].value(), False)

        # Check form fields choices
        self.assertEqual(
            form.fields['continuing_education_training'].choices,
            [
                (
                    self.continuing_admission.training.acronym,
                    f'{self.continuing_admission.training.acronym} - {self.continuing_admission.training.title}',
                )
            ],
        )

        # Check additional data used in the template
        self.assertTrue(form.display_long_continuing_fields)
        self.assertFalse(form.display_closed_continuing_fields)

    def test_training_choice_form_initialization_with_closed_short_training(self):
        self.client.force_login(self.sic_manager_user)

        self.continuing_admission.training.specificiufcinformations.registration_required = False
        self.continuing_admission.training.specificiufcinformations.state = StateIUFC.CLOSED.name
        self.continuing_admission.training.specificiufcinformations.save()

        response = self.client.get(self.admission_form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check additional data used in the template
        form = response.context['form']
        self.assertFalse(form.display_long_continuing_fields)
        self.assertTrue(form.display_closed_continuing_fields)

    def training_choice_form_submission_bad_training(self):
        self.client.force_login(self.sic_manager_user)

        # Because the training is not available for this year
        response = self.client.post(
            self.admission_form_url,
            {
                'continuing_education_training': self.continuing_admission.training.acronym,
                'academic_year': self.academic_years[1].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(
            self.error_message_no_training,
            form.errors.get('continuing_education_training', []),
        )

        # Because the specified acronym is not found
        response = self.client.post(
            self.admission_form_url,
            {
                'continuing_education_training': 'UNKNOWN',
                'academic_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(
            self.error_message_no_training,
            form.errors.get('continuing_education_training', []),
        )

        # Because the user doesn't manage this training
        response = self.client.post(
            self.admission_form_url,
            {
                'continuing_education_training': self.other_training_other_entity.acronym,
                'academic_year': self.other_training_other_entity.academic_year.year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(
            self.error_message_no_training,
            form.errors.get('continuing_education_training', []),
        )

    def test_training_choice_form_submission_with_invalid_data(self):
        self.client.force_login(self.sic_manager_user)

        # Missing fields
        response = self.client.post(self.admission_form_url, {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 3)

        for field in [
            'continuing_education_training',
            'academic_year',
            'motivations',
        ]:
            self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get(field, []))

        # Some fields are required for a long training
        response = self.client.post(
            self.admission_form_url,
            {
                'continuing_education_training': self.other_training_same_entity.acronym,
                'academic_year': self.other_training_same_entity.academic_year.year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 2)

        for field in [
            'ways_to_find_out_about_the_course',
            'motivations',
        ]:
            self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get(field, []), msg=field)

    def test_training_choice_form_submission_with_valid_data(self):
        self.client.force_login(self.sic_manager_user)

        # For a long and opened course
        response = self.client.post(
            self.admission_form_url,
            data={
                'continuing_education_training': self.other_training_same_entity.acronym,
                'academic_year': self.other_training_same_entity.academic_year.year,
                'motivations': 'New motivations',
                'ways_to_find_out_about_the_course': [ChoixMoyensDecouverteFormation.FACEBOOK.name],
                'other_way_to_find_out_about_the_course': 'Other way',
                'interested_mark': False,
            },
        )

        self.assertRedirects(response, self.admission_detail_url)

        self.continuing_admission.refresh_from_db()

        # Save the new data
        self.assertEqual(self.continuing_admission.training, self.other_training_same_entity)
        self.assertEqual(self.continuing_admission.determined_academic_year, self.academic_years[1])
        self.assertEqual(self.continuing_admission.motivations, 'New motivations')
        self.assertEqual(
            self.continuing_admission.ways_to_find_out_about_the_course,
            [ChoixMoyensDecouverteFormation.FACEBOOK.name],
        )
        self.assertEqual(self.continuing_admission.other_way_to_find_out_about_the_course, '')

        # Reset the interested_mark which is not displayed for an opened course
        self.assertEqual(self.continuing_admission.interested_mark, None)

        # For a closed course
        self.other_training_same_entity.specificiufcinformations.state = StateIUFC.CLOSED.name
        self.other_training_same_entity.specificiufcinformations.save()

        response = self.client.post(
            self.admission_form_url,
            data={
                'continuing_education_training': self.other_training_same_entity.acronym,
                'academic_year': self.other_training_same_entity.academic_year.year,
                'motivations': 'New motivations',
                'ways_to_find_out_about_the_course': [ChoixMoyensDecouverteFormation.AUTRE.name],
                'other_way_to_find_out_about_the_course': 'Other way',
                'interested_mark': False,
            },
        )

        self.assertRedirects(response, self.admission_detail_url)

        self.continuing_admission.refresh_from_db()

        # Save the new data
        self.assertEqual(self.continuing_admission.training, self.other_training_same_entity)
        self.assertEqual(self.continuing_admission.determined_academic_year, self.academic_years[1])
        self.assertEqual(self.continuing_admission.motivations, 'New motivations')
        self.assertEqual(
            self.continuing_admission.ways_to_find_out_about_the_course,
            [ChoixMoyensDecouverteFormation.AUTRE.name],
        )
        self.assertEqual(self.continuing_admission.other_way_to_find_out_about_the_course, 'Other way')
        self.assertEqual(self.continuing_admission.interested_mark, False)

        # For a short course
        self.other_training_same_entity.specificiufcinformations.registration_required = False
        self.other_training_same_entity.specificiufcinformations.save()

        response = self.client.post(
            self.admission_form_url,
            data={
                'continuing_education_training': self.other_training_same_entity.acronym,
                'academic_year': self.other_training_same_entity.academic_year.year,
                'motivations': 'New motivations',
                'ways_to_find_out_about_the_course': [ChoixMoyensDecouverteFormation.FACEBOOK.name],
                'interested_mark': False,
            },
        )

        self.assertRedirects(response, self.admission_detail_url)

        self.continuing_admission.refresh_from_db()

        # Save the new data
        self.assertEqual(self.continuing_admission.training, self.other_training_same_entity)
        self.assertEqual(self.continuing_admission.determined_academic_year, self.academic_years[1])
        self.assertEqual(self.continuing_admission.motivations, 'New motivations')
        self.assertEqual(self.continuing_admission.ways_to_find_out_about_the_course, [])
        self.assertEqual(self.continuing_admission.interested_mark, False)

        # For a training without the specific iufc information
        self.other_training_same_entity.specificiufcinformations.delete()

        response = self.client.post(
            self.admission_form_url,
            data={
                'continuing_education_training': self.other_training_same_entity.acronym,
                'academic_year': self.other_training_same_entity.academic_year.year,
                'motivations': 'New motivations',
                'ways_to_find_out_about_the_course': [ChoixMoyensDecouverteFormation.FACEBOOK.name],
                'interested_mark': False,
            },
        )

        self.assertRedirects(response, self.admission_detail_url)

        self.continuing_admission.refresh_from_db()

        # Save the new data
        self.assertEqual(self.continuing_admission.training, self.other_training_same_entity)
        self.assertEqual(self.continuing_admission.determined_academic_year, self.academic_years[1])
        self.assertEqual(self.continuing_admission.motivations, 'New motivations')
        self.assertEqual(self.continuing_admission.ways_to_find_out_about_the_course, [])
        self.assertEqual(self.continuing_admission.interested_mark, None)
