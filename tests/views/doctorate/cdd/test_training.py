# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from admission.contrib.models.doctoral_training import Activity
from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import CategorieActivite
from admission.tests.factories.activity import ActivityFactory, ConferenceFactory, ServiceFactory
from admission.tests.factories.roles import CddManagerFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DoctorateTrainingActivityViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.conference = ConferenceFactory(ects=10)
        cls.doctorate = cls.conference.doctorate
        cls.service = ServiceFactory(doctorate=cls.doctorate)
        cls.manager = CddManagerFactory(entity=cls.doctorate.doctorate.management_entity)
        cls.url = resolve_url('admission:doctorate:training', uuid=cls.doctorate.uuid)

    def test_view(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.get(self.url)
        self.assertContains(response, self.conference.title)
        self.assertContains(response, _("NON_SOUMISE"))
        self.assertEqual(str(self.conference), "Conférences, colloques (10 ects, Non soumise)")

    def test_form(self):
        add_url = resolve_url('admission:doctorate:training:add', uuid=self.doctorate.uuid, category='service')
        self.client.force_login(self.manager.person.user)
        with translation.override(settings.LANGUAGE_CODE_FR):
            response = self.client.get(add_url)
            self.assertContains(response, "Coopération internationale")

        # Field is other
        response = self.client.post(add_url, {'type': "Foobar"}, follow=True)
        just_created = Activity.objects.first()
        self.assertIn(self.url, response.redirect_chain[-1][0])
        self.assertIn(str(just_created.uuid), response.redirect_chain[-1][0])
        self.assertEqual(just_created.type, "Foobar")

        # Field is one of provided values
        response = self.client.post(add_url, {'type': "Coopération internationale"}, follow=True)
        self.assertEqual(Activity.objects.first().type, "Coopération internationale")
        self.assertIn(self.url, response.redirect_chain[-1][0])

    def test_missing_form(self):
        add_url = resolve_url('admission:doctorate:training:add', uuid=self.doctorate.uuid, category='foobar')
        self.client.force_login(self.manager.person.user)
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_parent(self):
        add_url = resolve_url('admission:doctorate:training:add', uuid=self.doctorate.uuid, category='publication')
        self.client.force_login(self.manager.person.user)

        # test inexistent parent
        response = self.client.get(f"{add_url}?parent={uuid.uuid4()}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # test inexistent form combination
        response = self.client.get(f"{add_url}?parent={self.service.uuid}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # test normal behavior
        response = self.client.get(f"{add_url}?parent={self.conference.uuid}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(f"{add_url}?parent={self.conference.uuid}", {}, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_edit(self):
        self.client.force_login(self.manager.person.user)
        # Test edit
        edit_url = resolve_url(
            'admission:doctorate:training:edit',
            uuid=self.doctorate.uuid,
            activity_id=self.service.uuid,
        )
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(edit_url, {'type': "Foobar"})
        self.assertRedirects(response, f"{self.url}#{self.service.uuid}")
        self.service.refresh_from_db()
        self.assertEqual(self.service.type, "Foobar")
        response = self.client.get(edit_url)
        self.assertContains(response, "Foobar")

        # Test edit a child activity
        child = ActivityFactory(
            doctorate=self.doctorate,
            category=CategorieActivite.PUBLICATION.name,
            parent=self.conference,
        )
        edit_url = resolve_url('admission:doctorate:training:edit', uuid=self.doctorate.uuid, activity_id=child.uuid)
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
