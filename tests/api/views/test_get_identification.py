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
from django.conf import settings
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd import EN_ISO_CODE
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import CandidateFactory
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
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


class PersonIdentificationViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.be_country = CountryFactory(iso_code=BE_ISO_CODE, european_union=True)
        cls.en_country = CountryFactory(iso_code=EN_ISO_CODE, european_union=False)

        cls.person: Person = CompletePersonFactory(
            country_of_citizenship=cls.be_country,
        )

        cls.url = resolve_url('admission_api_v1:person_identification')

    def test_retrieve_identification_is_forbidden_without_permission(self):
        # Not authenticated
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_identification(self):
        self.client.force_authenticate(user=self.person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = response.json()

        self.assertEqual(result['matricule'], self.person.global_id)

        self.assertEqual(result['nom'], self.person.last_name)
        self.assertEqual(result['prenom'], self.person.first_name)
        self.assertEqual(result['autres_prenoms'], self.person.middle_name)

        self.assertEqual(result['date_naissance'], self.person.birth_date.isoformat())
        self.assertEqual(result['annee_naissance'], self.person.birth_year)
        self.assertEqual(result['lieu_naissance'], self.person.birth_place)

        self.assertEqual(result['langue_contact'], self.person.language)
        self.assertEqual(result['nom_langue_contact'], dict(settings.LANGUAGES).get(self.person.language))

        self.assertEqual(result['sexe'], self.person.sex)
        self.assertEqual(result['genre'], self.person.gender)
        self.assertEqual(result['etat_civil'], self.person.civil_state)

        self.assertEqual(result['photo_identite'], [str(file) for file in self.person.id_photo])
        self.assertEqual(result['email'], self.person.email)

        self.assertEqual(result['annee_derniere_inscription_ucl'], self.person.last_registration_year.year)
        self.assertEqual(result['noma_derniere_inscription_ucl'], self.person.last_registration_id)

        self.assertEqual(result['numero_carte_identite'], self.person.id_card_number)
        self.assertEqual(result['carte_identite'], [str(file) for file in self.person.id_card])
        self.assertEqual(result['numero_registre_national_belge'], self.person.national_number)
        self.assertEqual(result['date_expiration_carte_identite'], self.person.id_card_expiry_date)

        self.assertEqual(result['numero_passeport'], self.person.passport_number)
        self.assertEqual(result['passeport'], [str(file) for file in self.person.passport])
        self.assertEqual(result['date_expiration_passeport'], self.person.passport_expiry_date)

        self.assertEqual(result['pays_residence'], BE_ISO_CODE)

        # Nationality => European country (BE)
        self.assertEqual(result['pays_nationalite'], BE_ISO_CODE)
        self.assertEqual(result['nom_pays_nationalite'], self.person.country_of_citizenship.name)
        self.assertEqual(result['pays_nationalite_europeen'], True)

        self.assertEqual(result['pays_naissance'], self.person.birth_country.iso_code)
        self.assertEqual(result['nom_pays_naissance'], self.person.birth_country.name)

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
