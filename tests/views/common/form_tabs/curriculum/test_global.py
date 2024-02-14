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

from admission.contrib.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories.form_item import TextAdmissionFormItemFactory, AdmissionFormItemInstantiationFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.models.enums.got_diploma import GotDiploma
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import Master120TrainingFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory


@freezegun.freeze_time("2022-01-01")
class AdmissionCurriculumGlobalFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.training = Master120TrainingFactory(
            management_entity=first_doctoral_commission,
            academic_year=cls.academic_years[1],
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group,
        ).person.user

    def setUp(self):
        # Mocked data
        self.text_question_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(),
            academic_year=self.training.academic_year,
            tab=Onglets.CURRICULUM.name,
            required=True,
        )

        self.text_question_uuid = str(self.text_question_instantiation.form_item.uuid)

        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate__graduated_from_high_school=GotDiploma.THIS_YEAR.name,
            candidate__graduated_from_high_school_year=self.academic_years[1],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            specific_question_answers={
                self.text_question_uuid: 'My first answer',
            },
        )

        # Url
        self.form_url = resolve_url(
            'admission:general-education:update:curriculum:global',
            uuid=self.general_admission.uuid,
        )

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

        self.assertEqual(len(form.fields['specific_question_answers'].fields), 1)

    def test_submit_invalid_data(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(self.form_url, data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn('specific_question_answers', form.errors)
        self.assertEqual(
            len(getattr(form.fields['specific_question_answers'].fields[0], 'errors', [])),
            1,
        )

    def test_submit_valid_data(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'specific_question_answers_0': 'My new answer',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.specific_question_answers.get(self.text_question_uuid), 'My new answer')
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
