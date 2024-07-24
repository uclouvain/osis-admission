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
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.contrib.models import DoctorateAdmission
from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.enums import Onglets
from admission.forms import REQUIRED_FIELD_CLASS
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.form_item import TextAdmissionFormItemFactory, AdmissionFormItemInstantiationFactory
from admission.tests.factories.roles import ProgramManagerRoleFactory, CentralManagerRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from osis_profile import BE_ISO_CODE
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2022-01-01')
class AdmissionCurriculumGlobalFormViewForDoctorateTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        cls.be_country = CountryFactory(iso_code=BE_ISO_CODE, name='Belgique', name_en='Belgium')
        cls.foreign_country = CountryFactory(iso_code=FR_ISO_CODE, name='France', name_en='France')
        cls.training = DoctorateFactory(
            academic_year=cls.academic_years[1],
        )

        # Create users
        cls.sic_manager_user = CentralManagerRoleFactory(entity=cls.training.management_entity).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group,
        ).person.user

        # Url
        cls.base_url = 'admission:doctorate:update:curriculum'
        cls.base_details_url = 'admission:doctorate:curriculum'

    def setUp(self):
        # Mocked data
        self.text_question_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(),
            academic_year=self.training.academic_year,
            tab=Onglets.CURRICULUM.name,
            required=True,
        )

        self.text_question_uuid = str(self.text_question_instantiation.form_item.uuid)

        self.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            specific_question_answers={
                self.text_question_uuid: 'My first answer',
            },
            submitted=True,
        )

        # Urls
        self.form_url = resolve_url(self.base_url, uuid=self.doctorate_admission.uuid)
        self.details_url = resolve_url(self.base_details_url, uuid=self.doctorate_admission.uuid)

    def test_update_global_curriculum_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_education_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(len(form.fields['reponses_questions_specifiques'].fields), 1)
        self.assertIn('curriculum', form.fields)
        self.assertIn(REQUIRED_FIELD_CLASS, form.fields['curriculum'].widget.attrs.get('class', ''))
        self.assertNotIn('equivalence_diplome', form.fields)

    def test_submit_invalid_data(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(self.form_url, data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn('reponses_questions_specifiques', form.errors)
        self.assertEqual(
            len(getattr(form.fields['reponses_questions_specifiques'].fields[0], 'errors', [])),
            1,
        )

    def test_submit_valid_data(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'reponses_questions_specifiques_0': 'My new answer',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.doctorate_admission.refresh_from_db()

        self.assertEqual(
            self.doctorate_admission.specific_question_answers.get(self.text_question_uuid), 'My new answer'
        )
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)
