# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.shortcuts import resolve_url
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.test import APITestCase

from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CandidateFactory
from reference.tests.factories.language import LanguageFactory, FrenchLanguageFactory, EnglishLanguageFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class LanguagesKnowledgeTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CandidateFactory().person.user
        cls.url = resolve_url("languages-knowledge")
        cls.french_knowledge_data = {
            "certificate": [],
            "language": "FR",
            "listening_comprehension": "C2",
            "speaking_ability": "C2",
            "writing_ability": "C2",
        }
        cls.english_knowledge_data = {
            "certificate": [],
            "language": "EN",
            "listening_comprehension": "C2",
            "speaking_ability": "B2",
            "writing_ability": "C1",
        }
        cls.germany_knowledge_data = {
            "certificate": [],
            "language": "DE",
            "listening_comprehension": "C2",
            "speaking_ability": "C2",
            "writing_ability": "C2",
        }
        FrenchLanguageFactory()
        EnglishLanguageFactory()
        LanguageFactory(code="DE", name="Allemand")

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.user)
        methods_not_allowed = ["delete", "put", "patch"]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def create_languages_knowledge(self, data):
        self.client.force_authenticate(self.user)
        return self.client.post(self.url, data)

    def test_languages_knowledge_get(self):
        self.create_languages_knowledge([self.french_knowledge_data, self.english_knowledge_data])
        response = self.client.get(self.url)
        self.assertDictEqual(response.json()[0], self.english_knowledge_data)
        self.assertDictEqual(response.json()[1], self.french_knowledge_data)

    def test_languages_knowledge_create(self):
        response = self.create_languages_knowledge(
            [self.french_knowledge_data, self.english_knowledge_data, self.germany_knowledge_data]
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        languages_knowledge = self.user.person.languages_knowledge.all()
        self.assertEqual(languages_knowledge.count(), 3)

    def test_languages_knowledge_update_from_admission(self):
        admission = DoctorateAdmissionFactory()
        admission_url = resolve_url("languages-knowledge", uuid=admission.uuid)
        self.client.force_authenticate(admission.candidate.user)
        response = self.client.post(
            admission_url,
            [self.french_knowledge_data, self.english_knowledge_data, self.germany_knowledge_data],
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        languages_knowledge = admission.candidate.languages_knowledge.all()
        self.assertEqual(languages_knowledge.count(), 3)

        response = self.client.post(
            admission_url,
            [self.french_knowledge_data, self.english_knowledge_data, self.germany_knowledge_data],
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        languages_knowledge = admission.candidate.languages_knowledge.all()
        self.assertEqual(languages_knowledge.count(), 3)

    def test_languages_knowledge_create_should_fail_if_language_set_more_than_once(self):
        with self.assertRaises(
            ValidationError,
            msg=_("You cannot fill in a language more than once, please correct the form."),
        ):
            self.create_languages_knowledge(
                [
                    self.french_knowledge_data,
                    self.english_knowledge_data,
                    self.germany_knowledge_data,
                    self.germany_knowledge_data,
                ]
            )

    def test_languages_knowledge_create_should_fail_if_mandatory_languages_not_set(self):
        with self.assertRaises(ValidationError, msg=_("Mandatory languages are missing.")):
            self.create_languages_knowledge(
                [
                    self.english_knowledge_data,
                    self.germany_knowledge_data,
                ]
            )
