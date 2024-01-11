# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################

from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from base.models.enums.state_iufc import StateIUFC
from base.models.specific_iufc_informations import SpecificIUFCInformations
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.specific_iufc_informations import SpecificIUFCInformationsFactory
from base.tests.factories.user import UserFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class ContinuingEducationTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2020)
        cls.user = UserFactory()
        cls.training_specific_information: SpecificIUFCInformations = SpecificIUFCInformationsFactory(
            training_assistance=False,
            registration_required=True,
            state=StateIUFC.OPEN.name,
        )

        cls.base_url = 'retrieve-continuing-education-specific-information'

        cls.url = resolve_url(
            cls.base_url,
            sigle=cls.training_specific_information.training.acronym,
            annee=cls.training_specific_information.training.academic_year.year,
        )

    def test_retrieve_specific_information_of_unknown_training_throws_404(self):
        self.client.force_authenticate(user=self.user)

        # Unknown training acronym
        response = self.client.get(
            resolve_url(
                self.base_url,
                sigle='UNKNOWN',
                annee=self.training_specific_information.training.academic_year.year,
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Unknown academic year
        response = self.client.get(
            resolve_url(self.base_url, sigle=self.training_specific_information.training.acronym, annee=1800),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_specific_information_of_known_training(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(path=self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()

        self.assertEqual(json_response['sigle_formation'], self.training_specific_information.training.acronym)
        self.assertEqual(json_response['annee'], self.training_specific_information.training.academic_year.year)
        self.assertEqual(json_response['aide_a_la_formation'], False)
        self.assertEqual(json_response['inscription_au_role_obligatoire'], True)
        self.assertEqual(json_response['etat'], StateIUFC.OPEN.name)
