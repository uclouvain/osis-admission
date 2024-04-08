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
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd import EN_ISO_CODE
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import CandidateFactory
from base.models.enums.person_address_type import PersonAddressType
from base.models.person_address import PersonAddress
from osis_profile import BE_ISO_CODE
from reference.tests.factories.country import CountryFactory


class GeneralIdentificationViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.be_country = CountryFactory(iso_code=BE_ISO_CODE, european_union=True)
        cls.en_country = CountryFactory(iso_code=EN_ISO_CODE, european_union=False)

        cls.person = CompletePersonFactory(
            country_of_citizenship=cls.be_country,
        )
        cls.admission = GeneralEducationAdmissionFactory(
            candidate=cls.person,
            status=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
        )

        cls.url = resolve_url('admission_api_v1:general_identification', uuid=cls.admission.uuid)

    def test_retrieve_identification_is_forbidden_without_permission(self):
        # Not authenticated
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Other user
        self.client.force_authenticate(user=CandidateFactory().person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_identification(self):
        self.client.force_authenticate(user=self.person.user)

        # Nationality => European country (BE)
        # Residential country => BE
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = response.json()

        self.assertEqual(result['pays_nationalite_europeen'], True)
        self.assertEqual(result['pays_nationalite'], BE_ISO_CODE)
        self.assertEqual(result['pays_residence'], BE_ISO_CODE)

        # Nationality => Not European country (US)
        # Residential country => US
        self.person.country_of_citizenship = self.en_country
        self.person.save()

        address = PersonAddress.objects.get(person=self.person, label=PersonAddressType.RESIDENTIAL.name)
        address.country = self.en_country
        address.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = response.json()

        self.assertEqual(result['pays_nationalite_europeen'], False)
        self.assertEqual(result['pays_nationalite'], EN_ISO_CODE)
        self.assertEqual(result['pays_residence'], EN_ISO_CODE)

        # No nationality
        # No residential country
        self.person.country_of_citizenship = None
        self.person.save()

        address.delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = response.json()

        self.assertEqual(result['pays_nationalite_europeen'], None)
        self.assertEqual(result['pays_nationalite'], '')
        self.assertEqual(result['pays_residence'], '')
