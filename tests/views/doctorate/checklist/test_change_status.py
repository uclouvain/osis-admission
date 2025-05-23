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
import mock
from django.shortcuts import resolve_url
from rest_framework.test import APITestCase

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import ChoixStatutChecklist
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory


class ChangeStatusViewTestCase(APITestCase):
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

    def setUp(self) -> None:
        super().setUp()
        self.admission = DoctorateAdmissionFactory(
            training=self.training,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        # Mock invoke
        patcher = mock.patch(
            'infrastructure.utils.MessageBusInMemory.invoke',
        )
        self.mock_invoke = patcher.start()
        self.addCleanup(patcher.stop)

    def test_change_checklist_status(self):
        self.client.force_login(user=self.sic_manager_user)

        data = "field1=abc&field2=defghijk"

        url = resolve_url(
            'admission:doctorate:change-checklist-status',
            uuid=self.admission.uuid,
            tab='assimilation',
            status=ChoixStatutChecklist.GEST_REUSSITE.name,
        )

        # Check the response
        response = self.client.post(url, data=data, content_type='application/x-www-form-urlencoded')

        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.checklist['current']['assimilation']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(
            self.admission.checklist['current']['assimilation']['extra'],
            {
                'field1': 'abc',
                'field2': 'defghijk',
            },
        )

        # Update existing extra
        response = self.client.post(
            url,
            data='field2=zero&field3=un',
            content_type='application/x-www-form-urlencoded',
        )

        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.checklist['current']['assimilation']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(
            self.admission.checklist['current']['assimilation']['extra'],
            {
                'field1': 'abc',
                'field2': 'zero',
                'field3': 'un',
            },
        )

        # No current checklist
        self.admission.checklist.pop('current', None)
        self.admission.save()

        response = self.client.post(url, data=data, content_type='application/x-www-form-urlencoded')

        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.checklist['current']['assimilation']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(
            self.admission.checklist['current']['assimilation']['extra'],
            {
                'field1': 'abc',
                'field2': 'defghijk',
            },
        )
