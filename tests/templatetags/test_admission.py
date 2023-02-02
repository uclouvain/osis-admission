# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
import uuid
from unittest.mock import Mock

import freezegun
import mock
from django.http import HttpResponse
from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import path, reverse
from django.utils.translation import gettext as _
from django.views import View

from admission.contrib.models import ContinuingEducationAdmissionProxy
from admission.ddd.admission.domain.enums import TypeFormation
from admission.templatetags.admission import (
    TAB_TREES,
    Tab,
    current_subtabs,
    detail_tab_path_from_update,
    display,
    field_data,
    formatted_reference,
    get_active_parent,
    sortable_header_div,
    strip,
    update_tab_path_from_detail,
    multiple_field_data,
    get_first_truthy_value,
    get_item,
    interpolate, admission_training_type,
)
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.form_item import (
    DocumentAdmissionFormItemFactory,
    AdmissionFormItemInstantiationFactory,
    MessageAdmissionFormItemFactory,
    TextAdmissionFormItemFactory,
    RadioButtonSelectionAdmissionFormItemFactory,
    CheckboxSelectionAdmissionFormItemFactory,
)
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory, MainEntityVersionFactory


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
            'view': Mock(),
        }
        result = current_subtabs(context)
        self.assertEqual(result['subtabs'], TAB_TREES['doctorate'][Tab('doctorate', _('Doctorate'), 'graduation-cap')])

    def test_current_tabs_with_hidden_tab(self):
        context = {
            'request': Mock(
                resolver_match=Mock(
                    namespaces=['admission', 'doctorate', 'confirmation'],
                    url_name='failure',
                ),
            ),
            'view': Mock(),
        }
        result = current_subtabs(context)
        self.assertEqual(result['subtabs'], TAB_TREES['doctorate'][Tab('confirmation', '')])


class AdmissionPanelTagTestCase(TestCase):
    def test_normal_panel(self):
        template = Template("{% load admission %}{% panel 'Coucou' %}{% endpanel %}")
        rendered = template.render(Context())
        self.assertIn('<h4 class="panel-title">', rendered)
        self.assertIn('Coucou', rendered)
        self.assertIn('<div class="panel-body">', rendered)

    def test_panel_no_title(self):
        template = Template("{% load admission %}{% panel %}{% endpanel %}")
        rendered = template.render(Context())
        self.assertNotIn('<h4 class="panel-title">', rendered)
        self.assertIn('<div class="panel-body">', rendered)


class AdmissionFieldsDataTestCase(TestCase):
    def test_field_data_with_string_value_default_params(self):
        result = field_data(
            context={},
            name='My field label',
            data='value',
        )
        self.assertEqual(result['name'], 'My field label')
        self.assertEqual(result['data'], 'value')
        self.assertIsNone(result['css_class'])
        self.assertFalse(result['hide_empty'])

    def test_field_data_with_translated_string_value(self):
        result = field_data(
            context={},
            name='My field label',
            data='From',
            translate_data=True,
        )
        self.assertEqual(result['name'], 'My field label')
        self.assertEqual(result['data'], 'De')

    def test_field_data_with_empty_list_value(self):
        result = field_data(
            context={},
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
        self.assertEqual(display('-'), '')
        self.assertEqual(display('', '-', ''), '')
        self.assertEqual(display('-', '-'), '-')
        self.assertEqual(display('-', '-', '-'), '-')

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

    @freezegun.freeze_time('2023-01-01')
    def test_formatted_reference(self):
        root = MainEntityVersionFactory(parent=None, entity_type='')
        # With school as management entity
        faculty = EntityVersionFactory(
            entity_type=EntityType.FACULTY.name,
            acronym='FFC',
            parent=root.entity,
            end_date=datetime.date(2023, 1, 2),
        )
        school = EntityVersionFactory(
            entity_type=EntityType.SCHOOL.name,
            acronym='SFC',
            parent=root.entity,
            end_date=datetime.date(2023, 1, 2),
        )

        # With school as management entity
        created_admission = ContinuingEducationAdmissionFactory(training__management_entity=school.entity)
        admission = ContinuingEducationAdmissionProxy.objects.for_dto().get(uuid=created_admission.uuid)
        self.assertEqual(admission.sigle_entite_gestion, 'SFC')
        self.assertEqual(admission.training_management_faculty, None)
        self.assertEqual(formatted_reference(admission), f'M-SFC22-{str(admission)}')

        # With faculty as parent entity of the school
        school.parent = faculty.entity
        school.save()
        EntityVersion.objects.filter(uuid=school.uuid).update(parent=faculty.entity)
        admission = ContinuingEducationAdmissionProxy.objects.for_dto().get(uuid=created_admission.uuid)
        self.assertEqual(admission.sigle_entite_gestion, 'SFC')
        self.assertEqual(admission.training_management_faculty, 'FFC')
        self.assertEqual(formatted_reference(admission), f'M-FFC22-{str(admission)}')


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/', LANGUAGE_CODE='en')
class MultipleFieldDataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.configurations = [
            AdmissionFormItemInstantiationFactory(
                form_item=MessageAdmissionFormItemFactory(),
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=TextAdmissionFormItemFactory(),
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=DocumentAdmissionFormItemFactory(),
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=RadioButtonSelectionAdmissionFormItemFactory(),
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=CheckboxSelectionAdmissionFormItemFactory(),
            ),
        ]

    def test_multiple_field_data_return_right_values_with_valid_data(self):
        first_uuid = uuid.uuid4()
        result = multiple_field_data(
            context={'for_pdf': False},
            configurations=self.configurations,
            data={
                str(self.configurations[1].form_item.uuid): 'My response',
                str(self.configurations[2].form_item.uuid): [str(first_uuid), 'other-token'],
                str(self.configurations[3].form_item.uuid): '1',
                str(self.configurations[4].form_item.uuid): ['1', '2'],
            },
        )
        self.assertEqual(result['fields'][0].form_item.value, 'My very short message.')
        self.assertEqual(result['fields'][1].form_item.value, 'My response')
        self.assertEqual(result['fields'][2].form_item.value, [first_uuid, 'other-token'])
        self.assertEqual(result['fields'][3].form_item.value, 'One')
        self.assertEqual(result['fields'][4].form_item.value, 'One, Two')

    def test_multiple_field_data_return_right_values_with_empty_data(self):
        result = multiple_field_data(
            context={'for_pdf': False},
            configurations=self.configurations,
            data={},
        )
        self.assertEqual(result['fields'][0].form_item.value, 'My very short message.')
        self.assertEqual(result['fields'][1].form_item.value, None)
        self.assertEqual(result['fields'][2].form_item.value, [])
        self.assertEqual(result['fields'][3].form_item.value, '')
        self.assertEqual(result['fields'][4].form_item.value, '')


class SimpleAdmissionTemplateTagsTestCase(TestCase):
    def test_get_first_truthy_value_with_no_arg_returns_none(self):
        self.assertIsNone(get_first_truthy_value())

    def test_get_first_truthy_value_with_no_truthy_value_returns_none(self):
        self.assertIsNone(get_first_truthy_value(False, 0, ''))

    def test_get_first_truthy_value_with_one_truthy_value_returns_it(self):
        self.assertEqual(get_first_truthy_value(False, 1, ''), 1)

    def test_get_first_truthy_value_with_two_truthy_values_returns_the_first_one(self):
        self.assertEqual(get_first_truthy_value(False, 1, 2, None), 1)

    def test_get_item_with_key_in_dict_returns_the_related_value(self):
        self.assertEqual(get_item({'key': 'value'}, 'key'), 'value')

    def test_get_item_with_key_not_in_dict_returns_the_specified_key(self):
        self.assertEqual(get_item({'key1': 'value'}, 'key2'), 'key2')

    def test_interpolate_a_string(self):
        self.assertEqual(
            interpolate('my-str-with-value: %(value)s', value=1),
            'my-str-with-value: 1',
        )

    def test_admission_training_type(self):
        self.assertEqual(
            admission_training_type(TrainingType.PHD.name),
            TypeFormation.DOCTORAT.name,
        )
