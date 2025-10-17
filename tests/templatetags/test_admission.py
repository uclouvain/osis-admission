# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import MagicMock, Mock, patch

import freezegun
import mock
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import resolve_url
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import path, reverse
from django.utils.translation import gettext as _
from django.utils.translation import pgettext
from django.views import View

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import (
    message_candidat_avec_pae_avant_2015,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixMoyensDecouverteFormation,
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.shared_kernel.domain.enums import TypeFormation
from admission.ddd.admission.shared_kernel.domain.model.enums.authentification import (
    EtatAuthentificationParcours,
)
from admission.ddd.admission.shared_kernel.enums import Onglets, TypeItemFormulaire
from admission.ddd.admission.shared_kernel.tests.factory.profil import (
    AnneeExperienceAcademiqueDTOFactory,
    EtudesSecondairesDTOFactory,
    ExperienceAcademiqueDTOFactory,
    ExperienceNonAcademiqueDTOFactory,
)
from admission.ddd.admission.shared_kernel.tests.factory.question_specifique import QuestionSpecifiqueDTOFactory
from admission.models import ContinuingEducationAdmissionProxy, DoctorateAdmission
from admission.templatetags.admission import (
    TAB_TREES,
    Tab,
    admission_status,
    admission_training_type,
    admission_url,
    authentication_css_class,
    candidate_language,
    checklist_experience_action_links_context,
    cotutelle_institute,
    current_subtabs,
    detail_tab_path_from_update,
    display,
    document_component,
    experience_details_template,
    experience_valuation_url,
    format_ways_to_find_out_about_the_course,
    formatted_language,
    formatted_reference,
    get_active_parent,
    get_document_details_url,
    get_first_truthy_value,
    get_image_file_url,
    get_item,
    get_item_or_default,
    has_value,
    interpolate,
    is_list,
    label_with_user_icon,
    need_to_display_specific_questions,
    part_of_dict,
    sortable_header_div,
    update_tab_path_from_detail,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.templatetags.format import strip
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import (
    EntityVersionFactory,
    MainEntityVersionFactory,
)
from base.tests.factories.entity_version_address import EntityVersionAddressFactory
from osis_profile import BE_ISO_CODE, FR_ISO_CODE
from osis_profile.constants import JPEG_MIME_TYPE, PNG_MIME_TYPE
from osis_profile.models.enums.curriculum import (
    CURRICULUM_ACTIVITY_LABEL,
    EvaluationSystem,
)
from osis_profile.tests.factories.curriculum import ExperienceParcoursInterneDTOFactory
from reference.tests.factories.university import UniversityFactory


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
            TAB_TREES['doctorate'][Tab('doctorate', pgettext('tab', 'Research'), 'graduation-cap')],
        )


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
                'template': 'osis_document_components/editor.html',
                'value': 'token',
                'base_url': settings.OSIS_DOCUMENT_BASE_URL,
                'attrs': {},
            },
        )

        # With metadata for a PDF file in read_only mode
        component = document_component(
            'token',
            {
                'mimetype': PDF_MIME_TYPE,
            },
            can_edit=False,
        )
        self.assertEqual(
            component,
            {
                'template': 'osis_document_components/editor.html',
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


    def test_experience_details_template_with_an_educational_experience(self):
        general_admission = GeneralEducationAdmissionFactory()
        proposition_uuid = general_admission.uuid
        experience = ExperienceAcademiqueDTOFactory(
            pays=BE_ISO_CODE,
            regime_linguistique=FR_ISO_CODE,
            systeme_evaluation=EvaluationSystem.ECTS_CREDITS.name,
            annees=[AnneeExperienceAcademiqueDTOFactory(uuid=uuid.uuid4())],
        )

        perms = {
            'admission.change_admission_curriculum': True,
            'admission.change_admission_secondary_studies': True,
            'admission.delete_admission_curriculum': True,
            'profil.can_edit_parcours_externe': True,
            'profil.can_see_parcours_externe': True,
        }

        kwargs = {
            'context': {
                'request': Mock(
                    path='mypath',
                    user=MagicMock(
                        _computed_permissions=perms,
                    ),
                ),
                'view': MagicMock(
                    admission=general_admission,
                    proposition=MagicMock(
                        uuid=proposition_uuid,
                        noma_candidat='0123456',
                        formation=MagicMock(),
                    ),
                ),
            },
            'resume_proposition': MagicMock(
                est_proposition_generale=True,
                est_proposition_continue=False,
                est_proposition_doctorale=False,
                proposition=MagicMock(
                    uuid=proposition_uuid,
                    formation=MagicMock(),
                ),
            ),
            'experience': experience,
        }

        template_params = experience_details_template(**kwargs)

        self.assertEqual(
            template_params['custom_base_template'],
            'admission/exports/recap/includes/curriculum_educational_experience.html',
        )
        self.assertEqual(template_params['title'], _('Academic experience'))
        self.assertEqual(template_params['curex_link_button'], '')
        self.assertEqual(
            template_params['edit_link_button'],
            '/admissions/general-education/{proposition_uuid}/update/curriculum/educational/{experience_uuid}'
            '?next=mypath&next_hash_url=parcours_anterieur__{experience_uuid}'.format(
                proposition_uuid=proposition_uuid,
                experience_uuid=experience.uuid,
            ),
        )
        self.assertEqual(
            template_params['duplicate_link_button'],
            '/admissions/general-education/{proposition_uuid}/update/curriculum/educational/{experience_uuid}'
            '/duplicate?next=mypath&next_hash_url=parcours_anterieur__{experience_uuid}'.format(
                proposition_uuid=proposition_uuid,
                experience_uuid=experience.uuid,
            ),
        )
        self.assertEqual(
            template_params['delete_link_button'],
            '/admissions/general-education/{proposition_uuid}/update/curriculum/educational/{experience_uuid}'
            '/delete?next=mypath&next_hash_url=parcours_anterieur'.format(
                proposition_uuid=proposition_uuid,
                experience_uuid=experience.uuid,
            ),
        )
        self.assertEqual(template_params['experience'], experience)
        self.assertEqual(template_params['with_single_header_buttons'], True)
        self.assertEqual(template_params['is_foreign_experience'], False)
        self.assertEqual(template_params['is_belgian_experience'], True)
        self.assertEqual(template_params['translation_required'], False)
        self.assertEqual(template_params['evaluation_system_with_credits'], True)

        # Without the right to delete an experience
        perms['admission.delete_admission_curriculum'] = False
        template_params = experience_details_template(**kwargs)

        self.assertEqual(template_params['delete_link_button'], '')

        perms['admission.delete_admission_curriculum'] = True

        # With an EPC experience
        kwargs['experience'] = ExperienceAcademiqueDTOFactory(
            pays=BE_ISO_CODE,
            regime_linguistique=FR_ISO_CODE,
            systeme_evaluation=EvaluationSystem.ECTS_CREDITS.name,
            annees=[AnneeExperienceAcademiqueDTOFactory(uuid=uuid.uuid4())],
            identifiant_externe='EPC-1',
        )

        template_params = experience_details_template(**kwargs)

        self.assertEqual(
            template_params['curex_link_button'],
            '/osis_profile/{noma}/parcours_externe/edit/experience_academique/{annee_experience_uuid}'.format(
                noma='0123456',
                annee_experience_uuid=kwargs['experience'].annees[0].uuid,
                experience_uuid=kwargs['experience'].uuid,
            ),
        )
        self.assertEqual(template_params['edit_link_button'], '')
        self.assertEqual(template_params['duplicate_link_button'], '')
        self.assertEqual(template_params['delete_link_button'], '')

        # Without the right to see the experience from the profile
        perms['profil.can_see_parcours_externe'] = False
        template_params = experience_details_template(**kwargs)

        self.assertEqual(
            template_params['curex_link_button'],
            '/osis_profile/{noma}/parcours_externe/edit/experience_academique/{annee_experience_uuid}'.format(
                noma='0123456',
                annee_experience_uuid=kwargs['experience'].annees[0].uuid,
                experience_uuid=kwargs['experience'].uuid,
            ),
        )
        self.assertEqual(template_params['edit_link_button'], '')
        self.assertEqual(template_params['duplicate_link_button'], '')
        self.assertEqual(template_params['delete_link_button'], '')

        # Without the right to update the experience from the profile
        perms['profil.can_edit_parcours_externe'] = False
        template_params = experience_details_template(**kwargs)

        self.assertEqual(template_params['curex_link_button'], '')
        self.assertEqual(template_params['edit_link_button'], '')
        self.assertEqual(template_params['duplicate_link_button'], '')
        self.assertEqual(template_params['delete_link_button'], '')

        # Without the right to update education
        perms['admission.change_admission_curriculum'] = False

        template_params = experience_details_template(**kwargs)

        self.assertEqual(template_params['edit_link_button'], '')
        self.assertEqual(template_params['duplicate_link_button'], '')
        self.assertEqual(template_params['delete_link_button'], '')

    def test_experience_details_with_a_non_educational_experience(self):
        general_admission = GeneralEducationAdmissionFactory()
        proposition_uuid = general_admission.uuid
        experience = ExperienceNonAcademiqueDTOFactory()

        perms = {
            'admission.change_admission_curriculum': True,
            'admission.change_admission_secondary_studies': True,
            'admission.delete_admission_curriculum': True,
            'profil.can_edit_parcours_externe': True,
            'profil.can_see_parcours_externe': True,
        }

        kwargs = {
            'context': {
                'request': Mock(
                    path='mypath',
                    user=MagicMock(
                        _computed_permissions=perms,
                    ),
                ),
                'view': MagicMock(
                    admission=general_admission,
                    proposition=MagicMock(
                        uuid=proposition_uuid,
                        noma_candidat='0123456',
                        formation=MagicMock(),
                    ),
                ),
            },
            'resume_proposition': MagicMock(
                est_proposition_generale=True,
                est_proposition_continue=False,
                est_proposition_doctorale=False,
                proposition=MagicMock(
                    uuid=proposition_uuid,
                    formation=MagicMock(),
                ),
            ),
            'experience': experience,
        }

        template_params = experience_details_template(**kwargs)

        self.assertEqual(
            template_params['custom_base_template'],
            'admission/exports/recap/includes/curriculum_professional_experience.html',
        )
        self.assertEqual(template_params['title'], _('Non-academic activity'))
        self.assertEqual(template_params['curex_link_button'], '')
        self.assertEqual(
            template_params['edit_link_button'],
            '/admissions/general-education/{proposition_uuid}/update/curriculum/non_educational/{experience_uuid}'
            '?next=mypath&next_hash_url=parcours_anterieur__{experience_uuid}'.format(
                proposition_uuid=proposition_uuid,
                experience_uuid=experience.uuid,
            ),
        )
        self.assertEqual(
            template_params['duplicate_link_button'],
            '/admissions/general-education/{proposition_uuid}/update/curriculum/non_educational/{experience_uuid}'
            '/duplicate?next=mypath&next_hash_url=parcours_anterieur__{experience_uuid}'.format(
                proposition_uuid=proposition_uuid,
                experience_uuid=experience.uuid,
            ),
        )
        self.assertEqual(
            template_params['delete_link_button'],
            '/admissions/general-education/{proposition_uuid}/update/curriculum/non_educational/{experience_uuid}'
            '/delete?next=mypath&next_hash_url=parcours_anterieur'.format(
                proposition_uuid=proposition_uuid,
                experience_uuid=experience.uuid,
            ),
        )
        self.assertEqual(template_params['experience'], experience)
        self.assertEqual(template_params['with_single_header_buttons'], True)
        self.assertEqual(template_params['CURRICULUM_ACTIVITY_LABEL'], CURRICULUM_ACTIVITY_LABEL)

        # Without the right to delete an experience
        perms['admission.delete_admission_curriculum'] = False
        template_params = experience_details_template(**kwargs)

        self.assertEqual(template_params['delete_link_button'], '')

        perms['admission.delete_admission_curriculum'] = True

        # With an EPC experience
        kwargs['experience'] = ExperienceNonAcademiqueDTOFactory(identifiant_externe='EPC-1')

        template_params = experience_details_template(**kwargs)

        self.assertEqual(
            template_params['curex_link_button'],
            '/osis_profile/{noma}/parcours_externe/edit/experience_non_academique/{experience_uuid}'.format(
                noma='0123456',
                experience_uuid=kwargs['experience'].uuid,
            ),
        )
        self.assertEqual(template_params['edit_link_button'], '')
        self.assertEqual(template_params['duplicate_link_button'], '')
        self.assertEqual(template_params['delete_link_button'], '')

        # Without the right to update the experience from the profile
        perms['profil.can_edit_parcours_externe'] = False
        template_params = experience_details_template(**kwargs)

        self.assertEqual(template_params['curex_link_button'], '')
        self.assertEqual(template_params['edit_link_button'], '')
        self.assertEqual(template_params['duplicate_link_button'], '')
        self.assertEqual(template_params['delete_link_button'], '')

        # Without the right to update the experience
        perms['admission.change_admission_curriculum'] = False

        template_params = experience_details_template(**kwargs)

        self.assertEqual(template_params['curex_link_button'], '')
        self.assertEqual(template_params['edit_link_button'], '')
        self.assertEqual(template_params['duplicate_link_button'], '')
        self.assertEqual(template_params['delete_link_button'], '')

    def test_experience_details_with_secondary_studies(self):
        general_admission = GeneralEducationAdmissionFactory()
        proposition_uuid = general_admission.uuid
        experience = EtudesSecondairesDTOFactory()
        specific_questions = {Onglets.ETUDES_SECONDAIRES.name: [QuestionSpecifiqueDTOFactory()]}

        perms = {
            'admission.change_admission_secondary_studies': True,
            'profil.can_edit_parcours_externe': True,
            'profil.can_see_parcours_externe': True,
        }

        kwargs = {
            'context': {
                'request': Mock(
                    path='mypath',
                    user=MagicMock(
                        _computed_permissions=perms,
                    ),
                ),
                'view': MagicMock(
                    admission=general_admission,
                    proposition=MagicMock(
                        uuid=proposition_uuid,
                        noma_candidat='0123456',
                        formation=MagicMock(),
                    ),
                ),
            },
            'resume_proposition': MagicMock(
                est_proposition_generale=True,
                est_proposition_continue=False,
                est_proposition_doctorale=False,
                proposition=MagicMock(
                    uuid=proposition_uuid,
                    formation=MagicMock(),
                ),
            ),
            'experience': experience,
            'specific_questions': specific_questions,
        }
        template_params = experience_details_template(**kwargs)
        self.assertEqual(template_params['custom_base_template'], 'admission/exports/recap/includes/education.html')
        self.assertEqual(template_params['curex_link_button'], '')
        self.assertEqual(
            template_params['edit_link_button'],
            '/admissions/general-education/{proposition_uuid}/update/education'
            '?next=mypath&next_hash_url=parcours_anterieur__{experience_uuid}'.format(
                proposition_uuid=proposition_uuid,
                experience_uuid=experience.uuid,
            ),
        )
        self.assertEqual(template_params['duplicate_link_button'], '')
        self.assertEqual(template_params['delete_link_button'], '')
        self.assertEqual(template_params['specific_questions'], specific_questions[Onglets.ETUDES_SECONDAIRES.name])

        # With an EPC experience
        kwargs['experience'] = EtudesSecondairesDTOFactory(identifiant_externe='EPC-1')

        template_params = experience_details_template(**kwargs)

        self.assertEqual(template_params['edit_link_button'], '')
        self.assertEqual(
            template_params['curex_link_button'],
            '/osis_profile/{noma}/parcours_externe/edit/etudes_secondaires'.format(
                noma='0123456',
            ),
        )
        self.assertEqual(template_params['duplicate_link_button'], '')
        self.assertEqual(template_params['delete_link_button'], '')

        # Without the right to update education
        perms['admission.change_admission_secondary_studies'] = False

        template_params = experience_details_template(**kwargs)

        self.assertEqual(template_params['curex_link_button'], '')
        self.assertEqual(template_params['edit_link_button'], '')
        self.assertEqual(template_params['duplicate_link_button'], '')
        self.assertEqual(template_params['delete_link_button'], '')

    def test_checklist_experience_action_links_context_with_an_educational_experience(self):
        general_admission = GeneralEducationAdmissionFactory()
        proposition_uuid = general_admission.uuid

        experience = ExperienceAcademiqueDTOFactory(
            annees=[AnneeExperienceAcademiqueDTOFactory(uuid=uuid.uuid4(), annee=2020)],
            valorisee_par_admissions=[proposition_uuid],
        )

        perms = {
            'admission.change_admission_curriculum': True,
            'admission.change_admission_secondary_studies': True,
            'admission.delete_admission_curriculum': True,
            'profil.can_edit_parcours_externe': True,
            'profil.can_see_parcours_externe': True,
        }

        kwargs = {
            'context': {
                'request': Mock(
                    path='mypath',
                    user=MagicMock(
                        _computed_permissions=perms,
                    ),
                ),
                'view': MagicMock(
                    base_namespace='admission:general-education',
                    kwargs={'uuid': proposition_uuid},
                    admission=general_admission,
                    proposition=MagicMock(noma_candidat='0123456'),
                ),
            },
            'prefix': 'prefix',
            'experience': experience,
            'current_year': 2020,
            'parcours_tab_id': 'tabID',
        }

        next_url_suffix = f'?next=mypath&next_hash_url=tabID'

        context = checklist_experience_action_links_context(**kwargs)

        self.assertEqual(context['prefix'], 'prefix')
        self.assertEqual(
            context['update_url'],
            f'/admissions/general-education/{proposition_uuid}/update/curriculum/educational'
            f'/{experience.uuid}{next_url_suffix}',
        )
        self.assertEqual(
            context['delete_url'],
            f'/admissions/general-education/{proposition_uuid}/update/curriculum/educational'
            f'/{experience.uuid}/delete{next_url_suffix}',
        )
        self.assertEqual(
            context['duplicate_url'],
            f'/admissions/general-education/{proposition_uuid}/update/curriculum/educational'
            f'/{experience.uuid}/duplicate',
        )
        self.assertEqual(context['experience_uuid'], str(experience.uuid))
        self.assertEqual(context['edit_link_button_in_new_tab'], False)

        perms['admission.delete_admission_curriculum'] = False
        context = checklist_experience_action_links_context(**kwargs)

        self.assertEqual(context['delete_url'], '')

        perms['admission.delete_admission_curriculum'] = False

        # With a valuated experience
        experience = ExperienceAcademiqueDTOFactory(
            annees=[AnneeExperienceAcademiqueDTOFactory(uuid=uuid.uuid4(), annee=2020)],
            valorisee_par_admissions=[proposition_uuid],
            identifiant_externe='EPC-1',
        )
        kwargs['experience'] = experience

        context = checklist_experience_action_links_context(**kwargs)

        self.assertEqual(context['edit_link_button_in_new_tab'], True)
        self.assertEqual(
            context['curex_url'],
            f'/osis_profile/0123456/parcours_externe/edit/experience_academique/{experience.annees[0].uuid}',
        )
        self.assertEqual(context['delete_url'], '')

    def test_checklist_experience_action_links_context_with_a_non_educational_experience(self):
        general_admission = GeneralEducationAdmissionFactory()
        proposition_uuid = general_admission.uuid

        experience = ExperienceNonAcademiqueDTOFactory(
            valorisee_par_admissions=[proposition_uuid],
            date_fin=datetime.date(2020, 12, 31),
        )

        perms = {
            'admission.change_admission_curriculum': True,
            'admission.change_admission_secondary_studies': True,
            'admission.delete_admission_curriculum': True,
            'profil.can_edit_parcours_externe': True,
            'profil.can_see_parcours_externe': True,
        }

        kwargs = {
            'context': {
                'request': Mock(
                    path='mypath',
                    user=MagicMock(
                        _computed_permissions=perms,
                    ),
                ),
                'view': MagicMock(
                    base_namespace='admission:general-education',
                    kwargs={'uuid': proposition_uuid},
                    admission=general_admission,
                    proposition=MagicMock(noma_candidat='0123456'),
                ),
            },
            'prefix': 'prefix',
            'experience': experience,
            'current_year': 2020,
            'parcours_tab_id': 'tabID',
        }

        next_url_suffix = f'?next=mypath&next_hash_url=tabID'

        context = checklist_experience_action_links_context(**kwargs)

        self.assertEqual(context['prefix'], 'prefix')
        self.assertEqual(
            context['update_url'],
            f'/admissions/general-education/{proposition_uuid}/update/curriculum/non_educational'
            f'/{experience.uuid}{next_url_suffix}',
        )
        self.assertEqual(
            context['delete_url'],
            f'/admissions/general-education/{proposition_uuid}/update/curriculum/non_educational'
            f'/{experience.uuid}/delete{next_url_suffix}',
        )
        self.assertEqual(
            context['duplicate_url'],
            f'/admissions/general-education/{proposition_uuid}/update/curriculum/non_educational'
            f'/{experience.uuid}/duplicate',
        )
        self.assertEqual(context['experience_uuid'], str(experience.uuid))
        self.assertEqual(context['edit_link_button_in_new_tab'], False)

        perms['admission.delete_admission_curriculum'] = False
        context = checklist_experience_action_links_context(**kwargs)

        self.assertEqual(context['delete_url'], '')

        perms['admission.delete_admission_curriculum'] = True

        # With a valuated experience
        experience = ExperienceNonAcademiqueDTOFactory(
            valorisee_par_admissions=[proposition_uuid],
            date_fin=datetime.date(2020, 12, 31),
            identifiant_externe='EPC-1',
        )
        kwargs['experience'] = experience

        context = checklist_experience_action_links_context(**kwargs)

        self.assertEqual(context['edit_link_button_in_new_tab'], True)
        self.assertEqual(
            context['curex_url'],
            f'/osis_profile/0123456/parcours_externe/edit/experience_non_academique/{experience.uuid}',
        )
        self.assertEqual(context['delete_url'], '')

    def test_checklist_experience_action_links_context_with_secondary_studies(self):
        general_admission = GeneralEducationAdmissionFactory()
        proposition_uuid = general_admission.uuid

        experience = EtudesSecondairesDTOFactory()

        perms = {
            'admission.change_admission_curriculum': True,
            'admission.change_admission_secondary_studies': True,
            'admission.delete_admission_curriculum': True,
            'profil.can_edit_parcours_externe': True,
            'profil.can_see_parcours_externe': True,
        }

        kwargs = {
            'context': {
                'request': Mock(
                    path='mypath',
                    user=MagicMock(
                        _computed_permissions=perms,
                    ),
                ),
                'view': MagicMock(
                    base_namespace='admission:general-education',
                    kwargs={'uuid': proposition_uuid},
                    admission=general_admission,
                    proposition=MagicMock(noma_candidat='0123456'),
                ),
            },
            'prefix': 'prefix',
            'experience': experience,
            'current_year': 2020,
            'parcours_tab_id': 'tabID',
        }

        next_url_suffix = f'?next=mypath&next_hash_url=tabID'

        context = checklist_experience_action_links_context(**kwargs)

        self.assertEqual(context['prefix'], 'prefix')
        self.assertEqual(
            context['update_url'],
            f'/admissions/general-education/{proposition_uuid}/update/education{next_url_suffix}',
        )
        self.assertEqual(context['experience_uuid'], str(experience.uuid))
        self.assertEqual(context['edit_link_button_in_new_tab'], False)

        # With a valuated experience
        experience = EtudesSecondairesDTOFactory(identifiant_externe='EPC-1')
        kwargs['experience'] = experience

        context = checklist_experience_action_links_context(**kwargs)

        self.assertEqual(context['edit_link_button_in_new_tab'], True)
        self.assertEqual(
            context['curex_url'],
            f'/osis_profile/0123456/parcours_externe/edit/etudes_secondaires',
        )

    def test_checklist_experience_action_links_context_with_an_internal_experience(self):
        general_admission = GeneralEducationAdmissionFactory()
        proposition_uuid = general_admission.uuid

        experience = ExperienceParcoursInterneDTOFactory(annees=[])

        perms = {
            'admission.change_admission_curriculum': True,
            'admission.change_admission_secondary_studies': True,
            'admission.delete_admission_curriculum': True,
            'profil.can_edit_parcours_externe': True,
            'profil.can_see_parcours_externe': True,
        }

        kwargs = {
            'context': {
                'request': Mock(
                    path='mypath',
                    user=MagicMock(
                        _computed_permissions=perms,
                    ),
                ),
                'view': MagicMock(
                    base_namespace='admission:general-education',
                    kwargs={'uuid': proposition_uuid},
                    admission=general_admission,
                    proposition=MagicMock(noma_candidat='0123456'),
                ),
            },
            'prefix': 'prefix',
            'experience': experience,
            'current_year': 2020,
            'parcours_tab_id': 'tabID',
        }

        context = checklist_experience_action_links_context(**kwargs)

        self.assertEqual(context['prefix'], 'prefix')
        self.assertEqual(context['update_url'], '')
        self.assertEqual(context['delete_url'], '')
        self.assertEqual(context['duplicate_url'], '')
        self.assertEqual(context['experience_uuid'], str(experience.uuid))
        self.assertEqual(context['edit_link_button_in_new_tab'], False)

    def test_checklist_experience_action_links_context_with_a_curriculum_message(self):
        general_admission = GeneralEducationAdmissionFactory()
        proposition_uuid = general_admission.uuid

        perms = {
            'admission.change_admission_curriculum': True,
            'admission.change_admission_secondary_studies': True,
            'admission.delete_admission_curriculum': True,
            'profil.can_edit_parcours_externe': True,
            'profil.can_see_parcours_externe': True,
        }

        kwargs = {
            'context': {
                'request': Mock(
                    path='mypath',
                    user=MagicMock(
                        _computed_permissions=perms,
                    ),
                ),
                'view': MagicMock(
                    base_namespace='admission:general-education',
                    kwargs={'uuid': proposition_uuid},
                    admission=general_admission,
                    proposition=MagicMock(noma_candidat='0123456'),
                ),
            },
            'prefix': 'prefix',
            'experience': message_candidat_avec_pae_avant_2015,
            'current_year': 2020,
            'parcours_tab_id': 'tabID',
        }

        context = checklist_experience_action_links_context(**kwargs)

        self.assertEqual(context['prefix'], 'prefix')
        self.assertEqual(context['update_url'], '')
        self.assertEqual(context['delete_url'], '')
        self.assertEqual(context['duplicate_url'], '')
        self.assertEqual(context['experience_uuid'], '')
        self.assertEqual(context['edit_link_button_in_new_tab'], False)

    def test_experience_valuation_url_with_an_educational_experience(self):
        proposition_uuid = uuid.uuid4()
        experience = ExperienceAcademiqueDTOFactory()
        self.assertEqual(
            experience_valuation_url(
                context={
                    'view': Mock(
                        kwargs={'uuid': proposition_uuid},
                        base_namespace='admission:general-education',
                    ),
                    'request': Mock(path='mypath'),
                },
                experience=experience,
            ),
            f'/admissions/general-education/{proposition_uuid}/update/curriculum/educational/'
            f'{experience.uuid}/valuate?next=mypath&next_hash_url=parcours_anterieur__{experience.uuid}',
        )

    def test_experience_valuation_url_with_a_non_educational_experience(self):
        proposition_uuid = uuid.uuid4()
        experience = ExperienceNonAcademiqueDTOFactory()
        self.assertEqual(
            experience_valuation_url(
                context={
                    'view': Mock(
                        kwargs={'uuid': proposition_uuid},
                        base_namespace='admission:general-education',
                    ),
                    'request': Mock(path='mypath'),
                },
                experience=experience,
            ),
            f'/admissions/general-education/{proposition_uuid}/update/curriculum/non_educational/'
            f'{experience.uuid}/valuate?next=mypath&next_hash_url=parcours_anterieur__{experience.uuid}',
        )

    def test_experience_valuation_url_with_secondary_studies(self):
        proposition_uuid = uuid.uuid4()
        experience = EtudesSecondairesDTOFactory()
        self.assertEqual(
            experience_valuation_url(
                context={
                    'view': Mock(
                        kwargs={'uuid': proposition_uuid},
                        base_namespace='admission:general-education',
                    ),
                    'request': Mock(path='mypath'),
                },
                experience=experience,
            ),
            '',
        )


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

    def test_format_ways_to_find_out_about_the_course(self):
        self.assertEqual(
            format_ways_to_find_out_about_the_course(
                MagicMock(
                    moyens_decouverte_formation=[
                        ChoixMoyensDecouverteFormation.SITE_FORMATION_CONTINUE.name,
                        ChoixMoyensDecouverteFormation.ANCIENS_ETUDIANTS.name,
                    ],
                    autre_moyen_decouverte_formation='Other way',
                )
            ),
            f'\t<li>{ChoixMoyensDecouverteFormation.SITE_FORMATION_CONTINUE.value}</li>\n'
            f'\t<li>{ChoixMoyensDecouverteFormation.ANCIENS_ETUDIANTS.value}</li>',
        )

        self.assertEqual(
            format_ways_to_find_out_about_the_course(
                MagicMock(
                    moyens_decouverte_formation=[
                        ChoixMoyensDecouverteFormation.SITE_FORMATION_CONTINUE.name,
                        ChoixMoyensDecouverteFormation.AUTRE.name,
                    ],
                    autre_moyen_decouverte_formation='Other way',
                )
            ),
            f'\t<li>{ChoixMoyensDecouverteFormation.SITE_FORMATION_CONTINUE.value}</li>\n' f'\t<li>Other way</li>',
        )

        self.assertEqual(
            format_ways_to_find_out_about_the_course(
                MagicMock(
                    moyens_decouverte_formation=[
                        ChoixMoyensDecouverteFormation.SITE_FORMATION_CONTINUE.name,
                        ChoixMoyensDecouverteFormation.AUTRE.name,
                    ],
                    autre_moyen_decouverte_formation='',
                )
            ),
            f'\t<li>{ChoixMoyensDecouverteFormation.SITE_FORMATION_CONTINUE.value}</li>\n'
            f'\t<li>{ChoixMoyensDecouverteFormation.AUTRE.value}</li>',
        )

    def test_get_document_details_url(self):
        admission_uuid = str(uuid.uuid4())
        context = {
            'request': Mock(
                resolver_match=Mock(namespace='admission:general-education'),
            ),
            'view': Mock(kwargs={'uuid': admission_uuid}),
        }

        document = Mock(
            identifiant='foo',
            requis_automatiquement=None,
        )

        base_url = resolve_url(
            'admission:general-education:document:detail',
            uuid=admission_uuid,
            identifier='foo',
        )

        self.assertEqual(
            get_document_details_url(context, document),
            base_url,
        )

        document.requis_automatiquement = True
        self.assertEqual(
            get_document_details_url(context, document),
            f'{base_url}?mandatory=1',
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

    def test_cotutelle_institute(self):
        # Known institute
        entity: Entity = EntityWithVersionFactory(
            organization=UniversityFactory(
                name='UCL',
            ),
        )
        entity_version_address = EntityVersionAddressFactory(
            entity_version=entity.entityversion_set.first(),
            city='Louvain-la-Neuve',
            street='Avenue de l\'Université',
            street_number='1',
            postal_code='1348',
        )

        admission: DoctorateAdmission = DoctorateAdmissionFactory(
            cotutelle_institution=entity.organization.uuid,
        )

        self.assertEqual(
            cotutelle_institute(admission),
            'UCL (Avenue de l\'Université 1, 1348 Louvain-la-Neuve)',
        )

        # Custom institute
        admission.cotutelle_institution = None
        admission.cotutelle_other_institution_name = 'UCL'
        admission.cotutelle_other_institution_address = 'Avenue de l\'Université 1, 1348 Louvain-la-Neuve'
        admission.save()

        self.assertEqual(
            cotutelle_institute(admission),
            'UCL (Avenue de l\'Université 1, 1348 Louvain-la-Neuve)',
        )

        # No institute
        admission.cotutelle_institution = None
        admission.cotutelle_other_institution_name = ''
        admission.cotutelle_other_institution_address = ''
        admission.save()

        self.assertEqual(
            cotutelle_institute(admission),
            '',
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
            get_image_file_url(file_uuid=None),
            '',
        )

    def test_get_image_file_url_with_not_accessible_token(self):
        self.token_patcher.return_value = None
        self.assertEqual(
            get_image_file_url(file_uuid='file_uuid'),
            '',
        )

    def test_get_image_file_url_with_not_accessible_metadata(self):
        self.metadata_patcher.return_value = None
        self.assertEqual(
            get_image_file_url(file_uuid='file_uuid'),
            '',
        )

    def test_get_image_file_url_with_pdf_file(self):
        self.metadata_patcher.return_value['mimetype'] = PDF_MIME_TYPE
        self.assertEqual(
            get_image_file_url(file_uuid='file_uuid'),
            '',
        )

    def test_get_image_file_url_with_jpeg_file(self):
        self.metadata_patcher.return_value['mimetype'] = JPEG_MIME_TYPE
        self.assertEqual(
            get_image_file_url(file_uuid='file_uuid'),
            self.image_url,
        )

    def test_get_image_file_url_with_png_file(self):
        self.metadata_patcher.return_value['mimetype'] = PNG_MIME_TYPE
        self.assertEqual(
            get_image_file_url(file_uuid='file_uuid'),
            self.image_url,
        )
