# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import Mock, patch, MagicMock

import freezegun
import mock
from django.conf import settings
from django.http import HttpResponse
from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import path, reverse
from django.utils import translation
from django.utils.translation import gettext as _, pgettext
from django.views import View

from admission.constants import PDF_MIME_TYPE, JPEG_MIME_TYPE, PNG_MIME_TYPE
from admission.contrib.models import ContinuingEducationAdmissionProxy, DoctorateAdmission
from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.domain.enums import TypeFormation
from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.enums import TypeItemFormulaire, Onglets
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.test.factory.profil import (
    ExperienceAcademiqueDTOFactory,
    ExperienceNonAcademiqueDTOFactory, EtudesSecondairesDTOFactory,
)
from admission.ddd.admission.test.factory.question_specifique import QuestionSpecifiqueDTOFactory
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
    get_first_truthy_value,
    get_item,
    interpolate,
    admission_training_type,
    admission_url,
    admission_status,
    get_image_file_url,
    get_country_name,
    formatted_language,
    get_item_or_default,
    has_value,
    document_component,
    get_item_or_none,
    part_of_dict,
    need_to_display_specific_questions,
    authentication_css_class,
    experience_details_template,
    is_list,
    label_with_user_icon,
    candidate_language,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory, MainEntityVersionFactory
from osis_profile import BE_ISO_CODE, CURRICULUM_ACTIVITY_LABEL
from osis_profile.models.enums.curriculum import EvaluationSystem
from reference.tests.factories.country import CountryFactory


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
        context = mock.Mock(
            request=self.factory.get('', data={}),
            get=lambda elt: None,
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
                'url': '/?o={}'.format(self.field_name),
            },
        )

    def test_sortable_header_div_with_asc_query_order_param(self):
        context = mock.Mock(
            request=self.factory.get('', data={'o': self.field_name}),
            get=lambda elt: None,
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
            request=self.factory.get('', data={'o': '-' + self.field_name}),
            get=lambda elt: None,
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
            ),
            get=lambda elt: None,
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
        doctorate_admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
        )
        cls.doctorate_admission = DoctorateAdmission.objects.get(uuid=doctorate_admission.uuid)

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
            'view': Mock(
                get_permission_object=Mock(return_value=self.doctorate_admission),
            ),
        }
        result = current_subtabs(context)
        self.assertEqual(
            result['subtabs'],
            TAB_TREES['doctorate'][Tab('doctorate', pgettext('tab', 'PhD project'), 'graduation-cap')],
        )

    def test_current_tabs_with_hidden_tab(self):
        context = {
            'request': Mock(
                resolver_match=Mock(
                    namespaces=['admission', 'doctorate', 'confirmation'],
                    url_name='failure',
                ),
            ),
            'view': Mock(
                get_permission_object=Mock(return_value=self.doctorate_admission),
            ),
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

    def test_field_data_with_all_inline(self):
        result = field_data(
            context={'all_inline': True},
            name='My field label',
            data='value',
        )
        self.assertEqual(result['inline'], True)

        result = field_data(
            context={'all_inline': True},
            name='My field label',
            data='value',
            inline=False,
        )
        self.assertEqual(result['inline'], True)

    def test_field_data_without_files(self):
        result = field_data(
            context={'hide_files': True},
            name='My field label',
            data=['my_file'],
        )
        self.assertEqual(result['data'], None)
        self.assertEqual(result['hide_empty'], True)

    def test_field_data_without_files_load(self):
        result = field_data(
            context={'load_files': False},
            name='My field label',
            data=['my_file'],
        )
        self.assertEqual(result['data'], _('Specified'))

        result = field_data(
            context={'load_files': False},
            name='My field label',
            data=[],
        )
        self.assertEqual(result['data'], _('Incomplete field'))


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

    def test_document_component(self):
        # No metadata and no token
        component = document_component('', {})
        self.assertEqual(component, {'template': 'admission/no_document.html', 'message': _('No document')})

        # No metadata with a token
        component = document_component('token', {})
        self.assertEqual(
            component, {'template': 'admission/no_document.html', 'message': _('Non-retrievable document')}
        )

        # With metadata for a PDF file
        component = document_component(
            'token',
            {
                'mimetype': PDF_MIME_TYPE,
            },
        )
        self.assertEqual(
            component,
            {
                'template': 'osis_document/editor.html',
                'value': 'token',
                'base_url': settings.OSIS_DOCUMENT_BASE_URL,
                'attrs': {}
            },
        )

        # With metadata for a PDF file in read_only mode
        component = document_component(
            'token',
            {
                'mimetype': PDF_MIME_TYPE,
            },
            can_edit=False
        )
        self.assertEqual(
            component,
            {
                'template': 'osis_document/editor.html',
                'value': 'token',
                'base_url': settings.OSIS_DOCUMENT_BASE_URL,
                'attrs': {'pagination': False, 'zoom': False, 'comment': False, 'highlight': False, 'rotation': False},
            },
        )

        # With metadata for a PNG file
        component = document_component(
            'token',
            {
                'mimetype': PNG_MIME_TYPE,
                'url': 'url',
                'name': 'name',
            },
        )
        self.assertEqual(component, {'template': 'admission/image.html', 'url': 'url', 'alt': 'name'})

    def test_get_item_or_none(self):
        dictionary = {
            'a': 1,
        }
        self.assertEqual(get_item_or_none(dictionary, 'a'), 1)
        self.assertEqual(get_item_or_none(dictionary, 'b'), None)

    def test_experience_details_template_with_an_educational_experience(self):
        proposition_uuid = uuid.uuid4()
        experience = ExperienceAcademiqueDTOFactory(
            pays=BE_ISO_CODE,
            regime_linguistique=FR_ISO_CODE,
            systeme_evaluation=EvaluationSystem.ECTS_CREDITS.name,
        )
        template_params = experience_details_template(
            resume_proposition=MagicMock(
                est_proposition_generale=True,
                est_proposition_continue=False,
                est_proposition_doctorale=False,
                proposition=MagicMock(
                    uuid=proposition_uuid,
                    formation=MagicMock(),
                ),
            ),
            experience=experience,
        )
        self.assertEqual(
            template_params['custom_base_template'],
            'admission/exports/recap/includes/curriculum_educational_experience.html',
        )
        self.assertEqual(template_params['title'], _('Academic experience'))
        self.assertEqual(
            template_params['edit_link_button'],
            '/admissions/general-education/{}/update/curriculum/educational/{}'.format(
                proposition_uuid,
                experience.uuid,
            ),
        )
        self.assertEqual(template_params['experience'], experience)
        self.assertEqual(template_params['is_foreign_experience'], False)
        self.assertEqual(template_params['is_belgian_experience'], True)
        self.assertEqual(template_params['translation_required'], False)
        self.assertEqual(template_params['evaluation_system_with_credits'], True)

    def test_experience_details_with_a_non_educational_experience(self):
        proposition_uuid = uuid.uuid4()
        experience = ExperienceNonAcademiqueDTOFactory()
        template_params = experience_details_template(
            resume_proposition=MagicMock(
                est_proposition_generale=True,
                est_proposition_continue=False,
                est_proposition_doctorale=False,
                proposition=MagicMock(
                    uuid=proposition_uuid,
                    formation=MagicMock(),
                ),
            ),
            experience=experience,
        )
        self.assertEqual(
            template_params['custom_base_template'],
            'admission/exports/recap/includes/curriculum_professional_experience.html',
        )
        self.assertEqual(template_params['title'], _('Non-academic experience'))
        self.assertEqual(
            template_params['edit_link_button'],
            '/admissions/general-education/{}/update/curriculum/non_educational/{}'.format(
                proposition_uuid,
                experience.uuid,
            ),
        )
        self.assertEqual(template_params['experience'], experience)
        self.assertEqual(template_params['CURRICULUM_ACTIVITY_LABEL'], CURRICULUM_ACTIVITY_LABEL)

    def test_experience_details_with_secondary_studies(self):
        proposition_uuid = uuid.uuid4()
        experience = EtudesSecondairesDTOFactory()
        specific_questions = {Onglets.ETUDES_SECONDAIRES.name: [QuestionSpecifiqueDTOFactory()]}
        template_params = experience_details_template(
            resume_proposition=MagicMock(
                est_proposition_generale=True,
                est_proposition_continue=False,
                est_proposition_doctorale=False,
                proposition=MagicMock(
                    uuid=proposition_uuid,
                    formation=MagicMock(),
                ),
            ),
            experience=experience,
            specific_questions=specific_questions,
        )
        self.assertEqual(template_params['custom_base_template'], 'admission/exports/recap/includes/education.html')
        self.assertEqual(
            template_params['edit_link_button'],
            '/admissions/general-education/{}/update/education'.format(proposition_uuid),
        )
        self.assertEqual(template_params['specific_questions'], specific_questions[Onglets.ETUDES_SECONDAIRES.name])


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

    def test_get_item_or_default_with_key_in_dict_returns_the_related_value(self):
        self.assertEqual(get_item_or_default({'key': 'value'}, 'key'), 'value')

    def test_get_item_or_default_with_key_not_in_dict_returns_the_default_value_if_specified(self):
        self.assertEqual(get_item_or_default({'key1': 'value'}, 'key2', 'default'), 'default')

    def test_get_item_or_default_with_key_not_in_dict_returns_none_if_the_default_value_is_not_specified(self):
        self.assertEqual(get_item_or_default({'key1': 'value'}, 'key2'), None)

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

    def test_get_country_name_with_no_country(self):
        self.assertEqual(get_country_name(None), '')

    def test_get_country_name_with_country_fr(self):
        with translation.override(settings.LANGUAGE_CODE_FR):
            country = CountryFactory(name='Belgique', name_en='Belgium')
            self.assertEqual(get_country_name(country), 'Belgique')

    def test_get_country_name_with_country_en(self):
        with translation.override(settings.LANGUAGE_CODE_EN):
            country = CountryFactory(name='Belgique', name_en='Belgium')
            self.assertEqual(get_country_name(country), 'Belgium')

    def test_formatted_language_with_fr_be(self):
        self.assertEqual(
            formatted_language(settings.LANGUAGE_CODE_FR),
            'FR',
        )

    def test_formatted_language_with_en(self):
        self.assertEqual(
            formatted_language(settings.LANGUAGE_CODE_EN),
            'EN',
        )

    def test_formatted_language_with_empty_language(self):
        self.assertEqual(
            formatted_language(''),
            '',
        )

    def test_has_value_with_list(self):
        self.assertFalse(has_value([], ['value1']))
        self.assertFalse(has_value([], []))
        self.assertFalse(has_value(['value2'], ['value1']))
        self.assertTrue(has_value(['value1'], ['value1']))

    def test_has_value_with_dict(self):
        self.assertFalse(has_value({}, ['value1']))
        self.assertFalse(has_value({'value2': 10}, ['value1']))
        self.assertTrue(has_value({'value1': False}, ['value1']))

    def test_part_of_dict(self):
        self.assertTrue(part_of_dict({}, {}))
        self.assertTrue(part_of_dict({'a': 1}, {'a': 1}))
        self.assertTrue(part_of_dict({'a': 1}, {'a': 1, 'b': 2}))
        self.assertFalse(part_of_dict({'a': 1}, {'a': 2}))
        self.assertFalse(part_of_dict({'a': 1}, {'b': 1}))
        self.assertTrue(part_of_dict({}, {'a': 1}))
        self.assertFalse(part_of_dict({'a': 1}, {}))

    def test_need_to_display_specific_questions(self):
        configurations = []

        # With no specific question
        self.assertFalse(need_to_display_specific_questions(configurations, False))
        self.assertFalse(need_to_display_specific_questions(configurations, True))

        # With only one document question
        configurations = [
            MagicMock(type=TypeItemFormulaire.DOCUMENT.name),
        ]
        self.assertTrue(need_to_display_specific_questions(configurations, False))
        self.assertFalse(need_to_display_specific_questions(configurations, True))

        # With several document questions
        configurations = [
            MagicMock(type=TypeItemFormulaire.DOCUMENT.name),
            MagicMock(type=TypeItemFormulaire.DOCUMENT.name),
            MagicMock(type=TypeItemFormulaire.DOCUMENT.name),
        ]
        self.assertTrue(need_to_display_specific_questions(configurations, False))
        self.assertFalse(need_to_display_specific_questions(configurations, True))

        # With text question
        configurations = [
            MagicMock(type=TypeItemFormulaire.TEXTE.name),
        ]
        self.assertTrue(need_to_display_specific_questions(configurations, False))
        self.assertTrue(need_to_display_specific_questions(configurations, True))

        # With several text questions
        configurations = [
            MagicMock(type=TypeItemFormulaire.TEXTE.name),
            MagicMock(type=TypeItemFormulaire.TEXTE.name),
            MagicMock(type=TypeItemFormulaire.TEXTE.name),
        ]
        self.assertTrue(need_to_display_specific_questions(configurations, False))
        self.assertTrue(need_to_display_specific_questions(configurations, True))

        # With both document and text questions
        configurations = [
            MagicMock(type=TypeItemFormulaire.DOCUMENT.name),
            MagicMock(type=TypeItemFormulaire.TEXTE.name),
        ]
        self.assertTrue(need_to_display_specific_questions(configurations, False))
        self.assertTrue(need_to_display_specific_questions(configurations, True))

    def test_authentication_css_class(self):
        self.assertEqual(
            '',
            authentication_css_class(EtatAuthentificationParcours.NON_CONCERNE.name),
        )
        self.assertEqual(
            'fa-solid fa-file-circle-question text-orange',
            authentication_css_class(EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name),
        )
        self.assertEqual(
            'fa-solid fa-file-circle-question text-orange',
            authentication_css_class(EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name),
        )
        self.assertEqual(
            'fa-solid fa-file-circle-xmark text-danger',
            authentication_css_class(EtatAuthentificationParcours.FAUX.name),
        )
        self.assertEqual(
            'fa-solid fa-file-circle-check text-success',
            authentication_css_class(EtatAuthentificationParcours.VRAI.name),
        )

    def test_is_list(self):
        self.assertFalse(is_list(None))
        self.assertFalse(is_list(False))
        self.assertFalse(is_list(0))
        self.assertFalse(is_list(0.0))
        self.assertFalse(is_list(''))
        self.assertTrue(is_list([]))

    def test_label_with_user_icon(self):
        label = (
            '{} <i class="fas fa-user" data-content="Information communiquée au candidat." '
            'data-toggle="popover" data-trigger="hover"></i>'
        )
        self.assertEqual(
            label_with_user_icon('foo'),
            label.format('foo'),
        )
        self.assertEqual(
            label_with_user_icon(''),
            label.format(''),
        )

    def test_candidate_language(self):
        self.assertEqual(
            candidate_language(''),
            f' <strong>(langue de contact </strong><span class="label label-admission-primary"></span>)',
        )

        self.assertEqual(
            candidate_language(settings.LANGUAGE_CODE_FR),
            f' <strong>(langue de contact </strong><span class="label label-admission-primary">FR</span>)',
        )

        self.assertEqual(
            candidate_language(settings.LANGUAGE_CODE_EN),
            f' <strong>(langue de contact </strong><span class="label label-admission-primary">EN</span>)',
        )


class AdmissionTagsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctorate_training_type = TrainingType.PHD.name
        cls.general_training_type = TrainingType.BACHELOR.name
        cls.continuing_training_type = TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name
        cls.admission_uuid = str(uuid.uuid4())

    def test_admission_url_for_a_doctorate(self):
        self.assertEqual(
            admission_url(admission_uuid=self.admission_uuid, osis_education_type=self.doctorate_training_type),
            reverse('admission:doctorate', kwargs={'uuid': self.admission_uuid}),
        )

    def test_admission_url_for_a_general_training(self):
        self.assertEqual(
            admission_url(admission_uuid=self.admission_uuid, osis_education_type=self.general_training_type),
            reverse('admission:general-education', kwargs={'uuid': self.admission_uuid}),
        )

    def test_admission_url_for_a_continuing_education(self):
        self.assertEqual(
            admission_url(admission_uuid=self.admission_uuid, osis_education_type=self.continuing_training_type),
            reverse('admission:continuing-education', kwargs={'uuid': self.admission_uuid}),
        )

    def test_admission_status_for_a_doctorate(self):
        status = ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE
        self.assertEqual(
            admission_status(
                status=status.name,
                osis_education_type=self.doctorate_training_type,
            ),
            status.value,
        )

    def test_admission_status_for_a_general_training(self):
        status = ChoixStatutPropositionGenerale.RETOUR_DE_FAC
        self.assertEqual(
            admission_status(
                status=status.name,
                osis_education_type=self.general_training_type,
            ),
            status.value,
        )

    def test_admission_status_for_a_continuing_education(self):
        status = ChoixStatutPropositionContinue.EN_BROUILLON
        self.assertEqual(
            admission_status(
                status=status.name,
                osis_education_type=self.continuing_training_type,
            ),
            status.value,
        )


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class AdmissionGetImageFileUrlTestCase(TestCase):
    def setUp(self) -> None:
        patcher = patch('admission.templatetags.admission.get_remote_token', return_value='foobar')
        self.token_patcher = patcher.start()
        self.addCleanup(patcher.stop)

        self.image_url = 'http://dummyurl/img.png'
        patcher = patch('admission.templatetags.admission.get_remote_metadata', return_value={'url': self.image_url})
        self.metadata_patcher = patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_image_file_url_without_file_uuid(self):
        self.assertEqual(
            get_image_file_url(file_uuids=[]),
            '',
        )

    def test_get_image_file_url_with_not_accessible_token(self):
        self.token_patcher.return_value = None
        self.assertEqual(
            get_image_file_url(file_uuids=['file_uuid']),
            '',
        )

    def test_get_image_file_url_with_not_accessible_metadata(self):
        self.metadata_patcher.return_value = None
        self.assertEqual(
            get_image_file_url(file_uuids=['file_uuid']),
            '',
        )

    def test_get_image_file_url_with_pdf_file(self):
        self.metadata_patcher.return_value['mimetype'] = PDF_MIME_TYPE
        self.assertEqual(
            get_image_file_url(file_uuids=['file_uuid']),
            '',
        )

    def test_get_image_file_url_with_jpeg_file(self):
        self.metadata_patcher.return_value['mimetype'] = JPEG_MIME_TYPE
        self.assertEqual(
            get_image_file_url(file_uuids=['file_uuid']),
            self.image_url,
        )

    def test_get_image_file_url_with_png_file(self):
        self.metadata_patcher.return_value['mimetype'] = PNG_MIME_TYPE
        self.assertEqual(
            get_image_file_url(file_uuids=['file_uuid']),
            self.image_url,
        )
