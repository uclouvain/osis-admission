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

from admission.contrib.models import ContinuingEducationAdmission, DoctorateAdmission, GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CentralManagerRoleFactory, SicManagementRoleFactory
from base.models.enums.person_address_type import PersonAddressType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person_address import PersonAddressFactory
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

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__private_email='john.doe@example.com',
            candidate__phone_mobile='0123456789',
        )

        cls.general_url = resolve_url('admission:general-education:coordonnees', uuid=cls.general_admission.uuid)

        cls.confirmed_general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=cls.general_admission.training,
            candidate=cls.general_admission.candidate,
            admitted=True,
        )

        cls.confirmed_general_url = resolve_url(
            'admission:general-education:coordonnees',
            uuid=cls.confirmed_general_admission.uuid,
        )

        cls.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__private_email='john.doe@example.com',
            candidate__phone_mobile='0123456789',
        )

        cls.doctorate_url = resolve_url('admission:doctorate:coordonnees', uuid=cls.doctorate_admission.uuid)

        cls.confirmed_doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=cls.doctorate_admission.training,
            candidate=cls.doctorate_admission.candidate,
            admitted=True,
        )

        cls.confirmed_doctorate_url = resolve_url(
            'admission:doctorate:coordonnees',
            uuid=cls.confirmed_doctorate_admission.uuid,
        )

    def test_continuing_coordonnees_detail_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)
        residential_address = PersonAddressFactory(
            person=self.continuing_admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
        )
        contact_address = PersonAddressFactory(
            person=self.continuing_admission.candidate,
            label=PersonAddressType.CONTACT.name,
        )

        url = resolve_url('admission:continuing-education:coordonnees', uuid=self.continuing_admission.uuid)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['coordonnees']['contact'], contact_address)
        self.assertEqual(response.context['coordonnees']['residential'], residential_address)
        self.assertEqual(response.context['coordonnees']['private_email'], 'john.doe@example.com')
        self.assertEqual(response.context['coordonnees']['phone_mobile'], '0123456789')

    def test_general_coordonnees_detail_sic_manager_without_address(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['coordonnees']['contact'], None)
        self.assertEqual(response.context['coordonnees']['residential'], None)
        self.assertEqual(response.context['coordonnees']['private_email'], 'john.doe@example.com')
        self.assertEqual(response.context['coordonnees']['phone_mobile'], '0123456789')

        self.assertIsNone(response.context['profil_candidat'])

        response = self.client.get(self.confirmed_general_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context.get('profil_candidat'),
            ProfilCandidatDTO(
                nom='Doe',
                prenom='John',
                genre='H',
                nationalite='BE',
                nom_pays_nationalite='Belgique',
                pays='BE',
                nom_pays='Belgique',
                code_postal='1348',
                ville='Louvain-La-Neuve',
                rue="Place de l'Université",
                numero_rue='2',
                boite_postale='',
            ),
        )

    def test_general_coordonnees_detail_sic_manager_with_contact_address(self):
        self.client.force_login(user=self.sic_manager_user)

        contact_address = PersonAddressFactory(
            person=self.general_admission.candidate,
            label=PersonAddressType.CONTACT.name,
        )

        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['coordonnees']['contact'], contact_address)
        self.assertEqual(response.context['coordonnees']['residential'], None)
        self.assertEqual(response.context['coordonnees']['private_email'], 'john.doe@example.com')
        self.assertEqual(response.context['coordonnees']['phone_mobile'], '0123456789')

    def test_general_coordonnees_detail_sic_manager_with_residential_and_contact_addresses(self):
        self.client.force_login(user=self.sic_manager_user)

        contact_address = PersonAddressFactory(
            person=self.general_admission.candidate,
            label=PersonAddressType.CONTACT.name,
        )
        residential_address = PersonAddressFactory(
            person=self.general_admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
        )

        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['coordonnees']['contact'], contact_address)
        self.assertEqual(response.context['coordonnees']['residential'], residential_address)
        self.assertEqual(response.context['coordonnees']['private_email'], 'john.doe@example.com')
        self.assertEqual(response.context['coordonnees']['phone_mobile'], '0123456789')

    def test_doctorate_coordonnees_detail_central_manager_user(self):
        self.client.force_login(user=self.central_manager.person.user)

        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, 200)

    def test_doctorate_coordonnees_detail_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        residential_address = PersonAddressFactory(
            person=self.doctorate_admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
        )
        contact_address = PersonAddressFactory(
            person=self.doctorate_admission.candidate,
            label=PersonAddressType.CONTACT.name,
        )

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.doctorate_admission.uuid)
        self.assertEqual(response.context['coordonnees']['contact'], contact_address)
        self.assertEqual(response.context['coordonnees']['residential'], residential_address)
        self.assertEqual(response.context['coordonnees']['private_email'], 'john.doe@example.com')
        self.assertEqual(response.context['coordonnees']['phone_mobile'], '0123456789')
        self.assertIsNone(response.context.get('profil_candidat'))

        response = self.client.get(self.confirmed_doctorate_url)
        self.assertEqual(response.context['dossier'].uuid, self.confirmed_doctorate_admission.uuid)
        self.assertEqual(
            response.context.get('profil_candidat'),
            ProfilCandidatDTO(
                nom='Doe',
                prenom='John',
                genre='H',
                nationalite='BE',
                nom_pays_nationalite='Belgique',
                pays='BE',
                nom_pays='Belgique',
                code_postal='1348',
                ville='Louvain-La-Neuve',
                rue="Place de l'Université",
                numero_rue='2',
                boite_postale='',
            ),
        )

        self.assertEqual(response.status_code, 200)
