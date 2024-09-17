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
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import ChoixStatutChecklist
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory


class ChangeExtraViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.second_sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.second_fac_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group
        ).person.user

        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        super().setUp()
        self.admission = DoctorateAdmissionFactory(
            training=self.training,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )
        self.url = resolve_url(
            'admission:doctorate:change-checklist-extra',
            uuid=self.admission.uuid,
            tab='assimilation',
        )


    def test_change_extra_of_assimilation_with_a_bad_request(self):
        self.client.force_login(user=self.sic_manager_user)
        url = resolve_url(
            'admission:doctorate:change-checklist-extra',
            uuid=self.admission.uuid,
            tab='assimilation',
        )

        # Check the response
        response = self.client.post(url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.get('date_debut', []),
            [FIELD_REQUIRED_MESSAGE],
        )

        # Check that the admission has not been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.checklist['current']['assimilation'],
            {
                'enfants': [],
                'libelle': '',
                'extra': {},
                'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
            },
        )

    def test_change_extra_of_assimilation_with_a_valid_request(self):
        self.client.force_login(user=self.sic_manager_user)
        url = resolve_url(
            'admission:doctorate:change-checklist-extra',
            uuid=self.admission.uuid,
            tab='assimilation',
        )

        # Check the response
        response = self.client.post(
            url,
            data={
                'date_debut': '2021-12-31',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.checklist['current']['assimilation'],
            {
                'enfants': [],
                'libelle': '',
                'extra': {
                    'date_debut': '2021-12-31',
                },
                'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
            },
        )
        self.assertEqual(
            self.admission.last_update_author,
            self.sic_manager_user.person,
        )

        # Empty checklist
        self.admission.checklist.pop('current', None)
        self.admission.save()

        response = self.client.post(
            url,
            data={
                'date_debut': '2021-12-31',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.checklist['current']['assimilation'].get('extra'),
            {
                'date_debut': '2021-12-31',
            },
        )

    def test_change_extra_of_assimilation_is_forbidden_for_a_program_manager(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 403)