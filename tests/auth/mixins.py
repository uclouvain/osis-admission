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
from django.http import HttpResponse
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import path, reverse
from django.views import View

from admission.auth.mixins import CddRequiredMixin
from admission.tests.factories.roles import CddManagerFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory


# Mock views
class TestCddRequiredView(CddRequiredMixin, View):
    raise_exception = True

    def get(self, request, *args, **kwargs):
        return HttpResponse('ok')


# Mock urls
urlpatterns = [
    path(
        'cdd-view',
        TestCddRequiredView.as_view(),
        name='cdd_view',
    ),
]


@override_settings(ROOT_URLCONF=__name__)
class CddRequiredMixinTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        cls.user_without_person = UserFactory()
        cls.user_with_person = PersonFactory().user
        cls.cdd_user = CddManagerFactory().person.user

    def test_with_user_not_related_to_a_person(self):
        response = self.client.get(reverse('cdd_view'))
        self.assertEqual(response.status_code, 403)

    def test_with_no_cdd_user(self):
        self.client.force_login(
            user=self.user_with_person,
        )
        response = self.client.get(reverse('cdd_view'))
        self.assertEqual(response.status_code, 403)

    def test_with_cdd_user(self):
        self.client.force_login(user=self.cdd_user)
        response = self.client.get(reverse('cdd_view'))
        self.assertEqual(response.status_code, 200)
