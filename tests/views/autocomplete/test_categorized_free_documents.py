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
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.translation import override

from admission.constants import CONTEXT_GENERAL, CONTEXT_DOCTORATE, CONTEXT_CONTINUING
from admission.contrib.models.categorized_free_document import CategorizedFreeDocument
from admission.ddd.admission.formation_generale.domain.model.enums import (
    OngletsChecklist,
)
from admission.tests.factories.categorized_free_document import CategorizedFreeDocumentFactory


class CategorizedFreeDocumentsAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        CategorizedFreeDocument.objects.all().delete()

        # Mocked data
        cls.uclouvain_document = CategorizedFreeDocumentFactory(
            checklist_tab='',
            short_label_fr='Mon document 31',
            short_label_en='My document 31',
            long_label_fr='La description de mon premier document uclouvain',
            long_label_en='The description of my first uclouvain document',
            admission_context=CONTEXT_DOCTORATE,
        )
        cls.first_personal_data_document = CategorizedFreeDocumentFactory(
            checklist_tab=OngletsChecklist.donnees_personnelles.name,
            short_label_fr='Mon document 11',
            short_label_en='My document 11',
            long_label_fr='La description de mon premier document des données personnelles',
            long_label_en='The description of my first document of the personal data',
            admission_context=CONTEXT_GENERAL,
        )
        cls.second_personal_data_document = CategorizedFreeDocumentFactory(
            checklist_tab=OngletsChecklist.donnees_personnelles.name,
            short_label_fr='Mon document 12',
            short_label_en='My document 12',
            long_label_fr='La description de mon deuxième document des données personnelles',
            long_label_en='The description of my second document of the personal data',
            admission_context=CONTEXT_CONTINUING,
        )
        cls.assimilation_document = CategorizedFreeDocumentFactory(
            checklist_tab=OngletsChecklist.assimilation.name,
            short_label_fr='Mon document 21',
            short_label_en='My document 21',
            long_label_fr='La description de mon premier document d\'assimilation',
            long_label_en='The description of my first document of the assimilation',
            admission_context='',
        )

        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )

        cls.url = reverse('admission:autocomplete:categorized-free-documents')

    def test_get_categorized_free_documents(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 4)

        self.assertEqual(results[0]['id'], self.first_personal_data_document.pk)
        self.assertEqual(results[1]['id'], self.second_personal_data_document.pk)
        self.assertEqual(results[2]['id'], self.assimilation_document.pk)
        self.assertEqual(results[3]['id'], self.uclouvain_document.pk)

        self.assertEqual(results[0]['text'], 'Mon document 11')
        self.assertEqual(results[0]['selected_text'], 'Mon document 11')
        self.assertEqual(results[0]['with_academic_year'], False)
        self.assertEqual(results[0]['full_text'], 'La description de mon premier document des données personnelles')

    def test_get_categorized_free_documents_in_current_language(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url, data={}, headers={"accept-language": settings.LANGUAGE_CODE_EN})

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 4)

        self.assertEqual(results[0]['id'], self.first_personal_data_document.pk)
        self.assertEqual(results[0]['text'], 'Mon document 11')
        self.assertEqual(results[0]['selected_text'], 'Mon document 11')
        self.assertEqual(results[0]['with_academic_year'], False)
        self.assertEqual(results[0]['full_text'], 'The description of my first document of the personal data')

    def test_get_categorized_free_documents_in_specified_language(self):
        self.client.force_login(user=self.user)

        data = {
            'forward': json.dumps({'language': settings.LANGUAGE_CODE_EN}),
        }

        with override(language=settings.LANGUAGE_CODE_FR):
            response = self.client.get(self.url, data=data)

            self.assertEqual(response.status_code, 200)

            results = response.json()['results']

            self.assertEqual(len(results), 4)

            self.assertEqual(results[0]['id'], self.first_personal_data_document.pk)
            self.assertEqual(results[0]['text'], 'Mon document 11')
            self.assertEqual(results[0]['selected_text'], 'Mon document 11')
            self.assertEqual(results[0]['with_academic_year'], False)
            self.assertEqual(results[0]['full_text'], 'The description of my first document of the personal data')

    def test_get_categorized_free_documents_with_checklist_tab(self):
        self.client.force_login(user=self.user)

        # A checklist tab is specified so only the documents in that tab should be returned
        data = {
            'forward': json.dumps({'checklist_tab': OngletsChecklist.donnees_personnelles.name}),
        }

        response = self.client.get(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]['id'], self.first_personal_data_document.pk)
        self.assertEqual(results[1]['id'], self.second_personal_data_document.pk)

        # An empty string is specified so only the documents that are not related to a tab should be returned
        data = {
            'forward': json.dumps({'checklist_tab': ''}),
        }

        response = self.client.get(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['id'], self.uclouvain_document.pk)

    def test_get_categorized_free_documents_with_admission_context(self):
        self.client.force_login(user=self.user)

        # An admission context is specified so only the documents in that context should be returned
        data = {
            'forward': json.dumps({'admission_context': CONTEXT_GENERAL}),
        }

        response = self.client.get(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.first_personal_data_document.pk)

        # An empty string is specified so only the documents that are not related to a context should be returned
        data = {
            'forward': json.dumps({'admission_context': ''}),
        }

        response = self.client.get(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['id'], self.assimilation_document.pk)

    def test_get_categorized_free_documents_with_a_search_term(self):
        self.client.force_login(user=self.user)

        data = {
            'q': '2',
        }

        response = self.client.get(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]['id'], self.second_personal_data_document.pk)
        self.assertEqual(results[1]['id'], self.assimilation_document.pk)
