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

from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from admission.models.working_list import WorkingList
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    OngletsChecklist,
)
from admission.tests.factories.working_list import WorkingListFactory


class WorkingListAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        WorkingList.objects.all().delete()

        # Mocked data
        cls.working_list_with_checklist_filters = WorkingListFactory(
            name={
                settings.LANGUAGE_CODE_FR: 'Ma liste 2',
                settings.LANGUAGE_CODE_EN: 'My list 2',
            },
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters={
                OngletsChecklist.donnees_personnelles.name: [
                    'A_TRAITER',
                ],
                OngletsChecklist.parcours_anterieur.name: [
                    'A_TRAITER',
                ],
            },
            admission_statuses=[
                ChoixStatutPropositionGenerale.EN_BROUILLON.name,
                ChoixStatutPropositionGenerale.ANNULEE.name,
            ],
            admission_type=TypeDemande.INSCRIPTION.name,
            order=1,
            quarantine=True,
        )

        cls.working_list_without_checklist_filters = WorkingListFactory(
            name={
                settings.LANGUAGE_CODE_FR: 'Ma liste 1',
                settings.LANGUAGE_CODE_EN: 'My list 1',
            },
            admission_statuses=[
                ChoixStatutPropositionGenerale.CONFIRMEE.name,
            ],
            order=0,
            quarantine=False,
        )

        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )

        cls.url = reverse('admission:autocomplete:working-lists')

    def test_get_working_lists(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]['id'], self.working_list_without_checklist_filters.id)
        self.assertEqual(results[0]['text'], 'Ma liste 1')
        self.assertEqual(results[0]['checklist_filters_mode'], '')
        self.assertEqual(results[0]['checklist_filters'], [[] for tab_name in OngletsChecklist.get_names()])
        self.assertEqual(results[0]['admission_statuses'], [ChoixStatutPropositionGenerale.CONFIRMEE.name])
        self.assertEqual(results[0]['admission_type'], '')
        self.assertEqual(results[0]['quarantine'], False)

        self.assertEqual(results[1]['id'], self.working_list_with_checklist_filters.id)
        self.assertEqual(results[1]['text'], 'Ma liste 2')
        self.assertEqual(results[1]['checklist_filters_mode'], ModeFiltrageChecklist.INCLUSION.name)
        self.assertEqual(
            results[1]['checklist_filters'],
            [
                [] if index not in {0, 3} else ['A_TRAITER']
                for index, tab_name in enumerate(OngletsChecklist.get_names())
            ],
        )
        self.assertEqual(
            results[1]['admission_statuses'],
            [
                ChoixStatutPropositionGenerale.EN_BROUILLON.name,
                ChoixStatutPropositionGenerale.ANNULEE.name,
            ],
        )
        self.assertEqual(results[1]['admission_type'], TypeDemande.INSCRIPTION.name)
        self.assertEqual(results[1]['quarantine'], True)

    def test_filter_working_lists_by_name_in_fr(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url, {'q': 'Ma liste 1'})

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['id'], self.working_list_without_checklist_filters.id)

    def test_filter_working_lists_by_name_in_en(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url, {'q': 'My list 2'})

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 0)

        with override_settings(LANGUAGE_CODE=settings.LANGUAGE_CODE_EN):
            response = self.client.get(self.url, {'q': 'My list 2'})

            self.assertEqual(response.status_code, 200)

            results = response.json()['results']

            self.assertEqual(len(results), 1)

            self.assertEqual(results[0]['id'], self.working_list_with_checklist_filters.id)
