# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework import status
from rest_framework.test import APITestCase

from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.supervision import PromoterFactory
from base.tests.factories.person import PersonFactory
from gestion_des_comptes.models import HistoriqueMatriculeCompte


class DashboardTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = resolve_url('admission_api_v1:dashboard')
        promoter = PromoterFactory()
        cls.promoter_user = promoter.person.user
        admission = DoctorateAdmissionFactory(
            candidate__global_id='84169898'   # External account
        )
        cls.candidate_user = admission.candidate.user
        cls.no_role_user = PersonFactory(first_name="Joe").user
        cls.base_url = 'http://testserver'

    def test_dashboard_as_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_as_no_role(self):
        self.client.force_authenticate(self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.json(),
            {
                'donnees_transferees_vers_compte_interne': False,
                'links': {
                    'list_propositions': {'method': 'GET', 'url': f'{self.base_url}/api/v1/admission/propositions'},
                    'list_supervised': {'error': "Method 'GET' not allowed"},
                }
            },
        )

    def test_dashboard_as_candidate(self):
        self.client.force_authenticate(self.candidate_user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.json(),
            {
                'donnees_transferees_vers_compte_interne': False,
                'links': {
                    'list_propositions': {'method': 'GET', 'url': f'{self.base_url}/api/v1/admission/propositions'},
                    'list_supervised': {'error': "Method 'GET' not allowed"},
                }
            },
        )

    def test_dashboard_as_supervision_member(self):
        self.client.force_authenticate(self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.json(),
            {
                'donnees_transferees_vers_compte_interne': False,
                'links': {
                    'list_propositions': {'method': 'GET', 'url': f'{self.base_url}/api/v1/admission/propositions'},
                    'list_supervised': {
                        'method': 'GET',
                        'url': f'{self.base_url}/api/v1/admission/supervised_propositions',
                    },
                }
            },
        )

    def test_dashboard_after_external_account_switch_to_internal_account(self):
        HistoriqueMatriculeCompte.objects.create(
            matricule_interne='00989898',
            matricule_interne_actif=True,
            matricule_externe=self.candidate_user.person.global_id,
        )

        self.client.force_authenticate(self.candidate_user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.json(),
            {
                'donnees_transferees_vers_compte_interne': True,
                'links': {
                    'list_propositions': {'method': 'GET', 'url': f'{self.base_url}/api/v1/admission/propositions'},
                    'list_supervised': {'error': "Method 'GET' not allowed"},
                }
            },
        )
