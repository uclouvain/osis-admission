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
import datetime

import freezegun
from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory
from base.models.enums.person_address_type import PersonAddressType
from base.models.person_address import PersonAddress
from base.tests.factories.entity import EntityFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_address import PersonAddressFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class CoordonneesTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.agnostic_url = resolve_url('coordonnees')
        # Data
        cls.updated_data = {
            "residential": {'street': "Rue de la sobriété"},
            "contact": {},
            "phone_mobile": "+32 490 00 00 01",
            "private_email": "joe.poe@example.be",
            "emergency_contact_phone": "+32 490 00 00 02",
        }
        cls.updated_data_with_contact_address = {
            "residential": {'street': "Rue de la sobriété"},
            "contact": {'street': "Rue du pin"},
            "phone_mobile": "+32 490 00 00 01",
            "private_email": "joe.poe@example.be",
            "emergency_contact_phone": "+32 490 00 00 02",
        }
        cls.address = PersonAddressFactory(
            label=PersonAddressType.CONTACT.name,
            street="Rue de la soif",
        )
        cls.other_address = PersonAddressFactory(
            label=PersonAddressType.CONTACT.name,
            street="Rue de la faim",
        )
        cls.address.person.private_email = "john.doe@example.be"
        cls.address.person.save()
        doctoral_commission = EntityFactory()
        promoter = PromoterFactory()
        cls.promoter_user = promoter.person.user
        cls.admission = DoctorateAdmissionFactory(
            supervision_group=promoter.process,
            candidate=cls.address.person,
            training__management_entity=doctoral_commission,
        )
        AdmissionAcademicCalendarFactory.produce_all_required()
        cls.admission_url = resolve_url('coordonnees', uuid=cls.admission.uuid)
        # Users
        cls.candidate_user = cls.address.person.user
        cls.candidate_user_without_admission = cls.other_address.person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user
        cls.committee_member_user = CaMemberFactory(process=promoter.process).person.user

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate_user_without_admission)
        methods_not_allowed = ['delete', 'post', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.agnostic_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_coordonnees_get_no_role(self):
        self.client.force_authenticate(self.no_role_user)
        response = self.client.get(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())

    def test_coordonnees_get_candidate_with_admission(self):
        self.client.force_authenticate(self.candidate_user)
        response = self.client.get(self.admission_url)
        self.assertEqual(response.json()['contact']['street'], "Rue de la soif")
        self.assertEqual(response.json()['private_email'], "john.doe@example.be")
        response = self.client.get(self.agnostic_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_coordonnees_get_candidate_without_admission(self):
        self.client.force_authenticate(self.candidate_user_without_admission)
        response = self.client.get(self.agnostic_url)
        self.assertEqual(response.json()['contact']['street'], "Rue de la faim")

    def test_coordonnees_update_candidate_without_admission(self):
        self.client.force_authenticate(self.candidate_user_without_admission)
        response = self.client.put(self.agnostic_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        address = PersonAddress.objects.get(
            person__user_id=self.candidate_user_without_admission.pk,
            label=PersonAddressType.RESIDENTIAL.name,
        )
        self.assertEqual(address.street, "Rue de la sobriété")
        self.assertEqual(address.person.private_email, "joe.poe@example.be")
        self.assertEqual(address.person.phone_mobile, "+32 490 00 00 01")
        self.assertEqual(address.person.emergency_contact_phone, "+32 490 00 00 02")

    @freezegun.freeze_time('2023-01-01')
    def test_coordonnees_update_candidate_with_admission(self):
        self.client.force_authenticate(self.candidate_user)
        response = self.client.put(self.admission_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        address = PersonAddress.objects.get(
            person__user_id=self.candidate_user.pk,
            label=PersonAddressType.RESIDENTIAL.name,
        )
        self.assertEqual(address.street, "Rue de la sobriété")
        self.assertEqual(address.person.private_email, "joe.poe@example.be")
        self.assertEqual(address.person.phone_mobile, "+32 490 00 00 01")
        self.assertEqual(address.person.emergency_contact_phone, "+32 490 00 00 02")

        self.admission.refresh_from_db()
        self.assertEqual(self.admission.last_update_author, self.candidate_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

    @freezegun.freeze_time('2023-01-01')
    def test_coordonnees_update_candidate_with_general_admission(self):
        admission = GeneralEducationAdmissionFactory()

        self.client.force_authenticate(admission.candidate.user)

        response = self.client.put(resolve_url('general_coordinates', uuid=admission.uuid), self.updated_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

        address = PersonAddress.objects.get(
            person=admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
        )
        self.assertEqual(address.street, "Rue de la sobriété")
        self.assertEqual(address.person.private_email, "joe.poe@example.be")
        self.assertEqual(address.person.phone_mobile, "+32 490 00 00 01")
        self.assertEqual(address.person.emergency_contact_phone, "+32 490 00 00 02")

        admission.refresh_from_db()
        self.assertEqual(admission.last_update_author, admission.candidate)
        self.assertEqual(admission.modified_at, datetime.datetime.now())

    def test_coordonnees_update_candidate_with_contact(self):
        self.client.force_authenticate(self.candidate_user)
        response = self.client.put(self.admission_url, self.updated_data_with_contact_address)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        residential_address = PersonAddress.objects.get(
            person__user_id=self.candidate_user.pk,
            label=PersonAddressType.RESIDENTIAL.name,
        )
        contact_address = PersonAddress.objects.get(
            person__user_id=self.candidate_user.pk,
            label=PersonAddressType.CONTACT.name,
        )
        self.assertEqual(residential_address.street, "Rue de la sobriété")
        self.assertEqual(contact_address.street, "Rue du pin")

    def test_coordonnees_update_candidate_with_other_submitted_proposition(self):
        candidate = DoctorateAdmissionFactory(status=ChoixStatutPropositionDoctorale.CONFIRMEE.name).candidate
        self.client.force_authenticate(candidate.user)
        response = self.client.put(self.agnostic_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_coordonnees_update_candidate_with_submitted_proposition(self):
        self.client.force_authenticate(self.candidate_user)
        submitted_admission = DoctorateAdmissionFactory(
            candidate=self.address.person,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )
        response = self.client.put(resolve_url('coordonnees', uuid=submitted_admission.uuid), self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        submitted_admission.delete()

    def test_coordonnees_get_promoter(self):
        self.client.force_authenticate(self.promoter_user)
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_coordonnees_get_committee_member(self):
        self.client.force_authenticate(self.committee_member_user)
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
