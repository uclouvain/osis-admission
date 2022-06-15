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
import uuid
from unittest.mock import Mock

import mock
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import path, reverse
from django.utils.translation import gettext as _
from django.views import View

from admission.templatetags.admission import (
    TAB_TREES,
    Tab,
    current_subtabs,
    detail_tab_path_from_update,
    display,
    field_data,
    get_active_parent,
    sortable_header_div,
    strip,
    update_tab_path_from_detail,
)


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
class AdmissionSortableHeaderDivTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.field_name = 'my_field'
        cls.field_label = 'My field label'

    def test_sortable_header_div_without_query_order_param(self):
        context = mock.Mock(request=self.factory.get('', data={}))
        value = sortable_header_div(
            context=context,
            order_field_name=self.field_name,
            order_field_label=self.field_label,
        )
        self.assertEqual(
            value,
            {
                'field_label': self.field_label,
                'ordering_class': 'sort',
                'url': '/?o={}'.format(self.field_name),
            },
        )

    def test_sortable_header_div_with_asc_query_order_param(self):
        context = mock.Mock(
            request=self.factory.get(
                '',
                data={
                    'o': self.field_name,
                },
            )
        )
        value = sortable_header_div(
            context=context,
            order_field_name=self.field_name,
            order_field_label=self.field_label,
        )
        self.assertEqual(
            value,
            {'field_label': self.field_label, 'ordering_class': 'sort-up', 'url': '/?o=-{}'.format(self.field_name)},
        )

    def test_sortable_header_div_with_desc_query_order_param(self):
        context = mock.Mock(
            request=self.factory.get(
                '',
                data={
                    'o': '-' + self.field_name,
                },
            )
        )
        value = sortable_header_div(
            context=context,
            order_field_name=self.field_name,
            order_field_label=self.field_label,
        )
        self.assertEqual(
            value,
            {
                'field_label': self.field_label,
                'ordering_class': 'sort-down',
                'url': '/?o={}'.format(self.field_name),
            },
        )

    def test_sortable_header_div_with_other_query_order_param(self):
        context = mock.Mock(
            request=self.factory.get(
                '',
                data={
                    'o': '-other_field_name',
                    'other_param': '10',
                },
            )
        )
        value = sortable_header_div(
            context=context,
            order_field_name=self.field_name,
            order_field_label=self.field_label,
        )
        self.assertEqual(
            value,
            {
                'field_label': self.field_label,
                'ordering_class': 'sort',
                'url': '/?o={}&other_param=10'.format(self.field_name),
            },
        )


class AdmissionTabsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tab_tree = {
            Tab('t1', 'tab 1'): [
                Tab('t11', 'tab 11'),
                Tab('t12', 'tab 12'),
            ],
            Tab('t2', 'tab 2'): [
                Tab('t21', 'tab 21'),
                Tab('t22', 'tab 22'),
            ],
        }

    def test_get_active_parent_with_valid_tab_name(self):
        result = get_active_parent(tab_tree=self.tab_tree, tab_name='t21')
        self.assertEqual(result, Tab('t2', 'tab 2'))

    def test_get_active_parent_with_invalid_tab_name(self):
        result = get_active_parent(tab_tree=self.tab_tree, tab_name='t00')
        self.assertIsNone(result)

    def test_update_tab_path_from_detail(self):
        current_uuid = uuid.uuid4()

        # admission:doctorate:project ->  admission:doctorate:update:project
        context = {'request': Mock(resolver_match=Mock(namespaces=['admission', 'doctorate'], url_name='project'))}
        result = update_tab_path_from_detail(context, current_uuid)
        self.assertEqual(result, reverse('admission:doctorate:update:project', args=[current_uuid]))

        # admission:doctorate:confirmation ->  admission:doctorate:update:confirmation
        context = {'request': Mock(resolver_match=Mock(namespaces=['admission', 'doctorate'], url_name='confirmation'))}
        result = update_tab_path_from_detail(context, current_uuid)
        self.assertEqual(result, reverse('admission:doctorate:update:confirmation', args=[current_uuid]))

        # admission:doctorate:confirmation:opinion ->  admission:doctorate:confirmation
        context = {
            'request': Mock(
                resolver_match=Mock(namespaces=['admission', 'doctorate', 'confirmation'], url_name='opinion')
            )
        }
        result = update_tab_path_from_detail(context, current_uuid)
        self.assertEqual(result, reverse('admission:doctorate:confirmation', args=[current_uuid]))

        # admission:doctorate:send-mail ->  admission:doctorate:send-mail
        context = {'request': Mock(resolver_match=Mock(namespaces=['admission', 'doctorate'], url_name='send-mail'))}
        result = update_tab_path_from_detail(context, current_uuid)
        self.assertEqual(result, reverse('admission:doctorate:send-mail', args=[current_uuid]))

    def test_detail_tab_path_from_update(self):
        context = {
            'request': Mock(
                resolver_match=Mock(
                    namespaces=['admission', 'doctorate', 'update'],
                    url_name='project',
                ),
            ),
        }
        current_uuid = uuid.uuid4()
        result = detail_tab_path_from_update(context, current_uuid)
        self.assertEqual(
            result,
            reverse('admission:doctorate:project', args=[current_uuid]),
        )

    def test_current_tabs_with_visible_tab(self):
        context = {
            'request': Mock(
                resolver_match=Mock(
                    namespaces=['admission', 'doctorate', 'update'],
                    url_name='project',
                ),
            ),
        }
        result = current_subtabs(context)
        self.assertEqual(result, TAB_TREES['doctorate'][Tab('doctorate', _('Doctorate'), 'graduation-cap')])

    def test_current_tabs_with_hidden_tab(self):
        context = {
            'request': Mock(
                resolver_match=Mock(
                    namespaces=['admission', 'doctorate', 'confirmation'],
                    url_name='failure',
                ),
            ),
        }
        result = current_subtabs(context)
        self.assertEqual(result, TAB_TREES['doctorate'][Tab('doctorate', _('Doctorate'), 'graduation-cap')])


class AdmissionFieldsDataTestCase(TestCase):
    def test_field_data_with_string_value_default_params(self):
        result = field_data(
            name='My field label',
            data='value',
        )
        self.assertEqual(result['name'], 'My field label')
        self.assertEqual(result['data'], 'value')
        self.assertIsNone(result['css_class'])
        self.assertFalse(result['hide_empty'])

    def test_field_data_with_translated_string_value(self):
        result = field_data(
            name='My field label',
            data='From',
            translate_data=True,
        )
        self.assertEqual(result['name'], 'My field label')
        self.assertEqual(result['data'], 'De')

    def test_field_data_with_empty_list_value(self):
        result = field_data(
            name='My field label',
            data=[],
        )
        self.assertEqual(result['name'], 'My field label')
        self.assertEqual(result['data'], '')


class DisplayTagTestCase(TestCase):
    def test_comma(self):
        self.assertEqual(display('', ',', None), '')
        self.assertEqual(display('', ',', 0), '')
        self.assertEqual(display('', ',', ''), '')
        self.assertEqual(display('Foo', ',', []), 'Foo')
        self.assertEqual(display('', ',', "bar"), 'bar')
        self.assertEqual(display('foo', '-', "", '-', ''), 'foo')
        self.assertEqual(display('foo', '-', "bar", '-', ''), 'foo - bar')
        self.assertEqual(display('foo', '-', None, '-', ''), 'foo')
        self.assertEqual(display('foo', '-', None, '-', 'baz'), 'foo - baz')
        self.assertEqual(display('foo', '-', "bar", '-', 'baz'), 'foo - bar - baz')

    def test_parenthesis(self):
        self.assertEqual(display('(', '', ")"), '')
        self.assertEqual(display('(', None, ")"), '')
        self.assertEqual(display('(', 0, ")"), '')
        self.assertEqual(display('(', 'lol', ")"), '(lol)')

    def test_suffix(self):
        self.assertEqual(display('', ' grammes'), '')
        self.assertEqual(display(5, ' grammes'), '5 grammes')
        self.assertEqual(display(5, ' grammes'), '5 grammes')
        self.assertEqual(display(0.0, ' g'), '')

    def test_both(self):
        self.assertEqual(display('(', '', ")", '-', 0), '')
        self.assertEqual(display('(', '', ",", "", ")", '-', 0), '')
        self.assertEqual(display('(', 'jean', ",", "", ")", '-', 0), '(jean)')
        self.assertEqual(display('(', 'jean', ",", "michel", ")", '-', 0), '(jean, michel)')
        self.assertEqual(display('(', 'jean', ",", "michel", ")", '-', 100), '(jean, michel) - 100')

    def test_strip(self):
        self.assertEqual(strip(' coucou '), 'coucou')
        self.assertEqual(strip(0), 0)
        self.assertEqual(strip(None), None)
