##############################################################################
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
##############################################################################
import mock
from django.http import HttpResponse

from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import path
from django.views import View

from admission.templatetags.admission import sortable_header_div


# Mock views
class TestCddRequiredView(View):
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
class AdmissionTestCase(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.factory = RequestFactory()
        cls.field_name = 'my_field'
        cls.field_label = 'My field label'

    def test_sortable_header_div_without_query_order_param(self):
        context = mock.Mock(
            request=self.factory.get('', data={})
        )
        value = sortable_header_div(
            context=context,
            order_field_name=self.field_name,
            order_field_label=self.field_label,
        )
        self.assertEqual(value, {
            'field_label': self.field_label,
            'ordering_class': 'sort',
            'url': '/?o={}'.format(self.field_name),
        })

    def test_sortable_header_div_with_asc_query_order_param(self):
        context = mock.Mock(
            request=self.factory.get('', data={
                'o': self.field_name,
            })
        )
        value = sortable_header_div(
            context=context,
            order_field_name=self.field_name,
            order_field_label=self.field_label,
        )
        self.assertEqual(value, {
            'field_label': self.field_label,
            'ordering_class': 'sort-up',
            'url': '/?o=-{}'.format(self.field_name)
        })

    def test_sortable_header_div_with_desc_query_order_param(self):
        context = mock.Mock(
            request=self.factory.get('', data={
                'o': '-' + self.field_name,
            })
        )
        value = sortable_header_div(
            context=context,
            order_field_name=self.field_name,
            order_field_label=self.field_label,
        )
        self.assertEqual(value, {
            'field_label': self.field_label,
            'ordering_class': 'sort-down',
            'url': '/?o={}'.format(self.field_name),
        })

    def test_sortable_header_div_with_other_query_order_param(self):
        context = mock.Mock(
            request=self.factory.get('', data={
                'o': '-other_field_name',
                'other_param': '10'
            })
        )
        value = sortable_header_div(
            context=context,
            order_field_name=self.field_name,
            order_field_label=self.field_label,
        )
        self.assertEqual(value, {
            'field_label': self.field_label,
            'ordering_class': 'sort',
            'url': '/?o={}&other_param=10'.format(self.field_name),
        })
