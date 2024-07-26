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
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.models import ContinuingEducationAdmission, DoctorateAdmission, GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.history import HistoryEntryFactory
from admission.tests.factories.roles import CentralManagerRoleFactory, SicManagementRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from reference.tests.factories.country import CountryFactory


class CoordonneesDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')

        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.central_manager = CentralManagerRoleFactory(entity=first_doctoral_commission)

        cls.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__private_email='john.doe@example.com',
            candidate__phone_mobile='0123456789',
        )

        cls.continuing_historic_entry = HistoryEntryFactory(
            author='John Doe',
            object_uuid=cls.continuing_admission.uuid,
            tags=['continuing-education'],
            message_fr='Historique de formation continue',
            message_en='Continuing education historic',
        )

        cls.continuing_url = resolve_url(
            'admission:continuing-education:history-api',
            uuid=cls.continuing_admission.uuid,
        )

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__private_email='john.doe@example.com',
            candidate__phone_mobile='0123456789',
        )

        cls.general_historic_entry = HistoryEntryFactory(
            author='John Doe',
            object_uuid=cls.general_admission.uuid,
            tags=['general-education'],
            message_fr='Historique de formation générale',
            message_en='General education historic',
        )

        cls.general_url = resolve_url('admission:general-education:history-api', uuid=cls.general_admission.uuid)

        cls.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__private_email='john.doe@example.com',
            candidate__phone_mobile='0123456789',
        )

        cls.doctorate_url = resolve_url('admission:doctorate:history-api', uuid=cls.doctorate_admission.uuid)

        cls.doctorate_historic_entry = HistoryEntryFactory(
            author='John Doe',
            object_uuid=cls.doctorate_admission.uuid,
            tags=['doctorate-education'],
            message_fr='Historique de formation doctorale',
            message_en='Doctorate education historic',
        )

    def test_historic_api_with_sic_manager_and_continuing_admission(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)

        historic_entries = response.json()

        self.assertEqual(len(historic_entries), 1)

        self.assertEqual(historic_entries[0]['author'], 'John Doe')
        self.assertEqual(historic_entries[0]['tags'], ['continuing-education'])
        self.assertEqual(historic_entries[0]['message'], 'Historique de formation continue')

    def test_historic_api_with_sic_manager_and_general_admission(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)

        historic_entries = response.json()

        self.assertEqual(len(historic_entries), 1)

        self.assertEqual(historic_entries[0]['author'], 'John Doe')
        self.assertEqual(historic_entries[0]['tags'], ['general-education'])
        self.assertEqual(historic_entries[0]['message'], 'Historique de formation générale')

    def test_historic_api_with_sic_manager_and_doctorate_admission(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 200)

        historic_entries = response.json()

        self.assertEqual(len(historic_entries), 1)

        self.assertEqual(historic_entries[0]['author'], 'John Doe')
        self.assertEqual(historic_entries[0]['tags'], ['doctorate-education'])
        self.assertEqual(historic_entries[0]['message'], 'Historique de formation doctorale')
