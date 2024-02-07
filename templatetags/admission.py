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
import re
from dataclasses import dataclass
from functools import wraps
from inspect import getfullargspec
from typing import Union, Optional, List, Dict

from django import template
from django.conf import settings
from django.core.validators import EMPTY_VALUES
from django.shortcuts import resolve_url
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import get_language, gettext_lazy as _, pgettext
from osis_comment.models import CommentEntry
from osis_document.api.utils import get_remote_metadata, get_remote_token
from osis_history.models import HistoryEntry
from rules.templatetags import rules

from admission.auth.constants import READ_ACTIONS_BY_TAB, UPDATE_ACTIONS_BY_TAB
from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.program_manager import ProgramManager
from admission.auth.roles.sic_management import SicManagement
from admission.constants import IMAGE_MIME_TYPES, PDF_MIME_TYPE
from admission.contrib.models import ContinuingEducationAdmission, DoctorateAdmission, GeneralEducationAdmission
from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    STATUTS_PROPOSITION_AVANT_INSCRIPTION,
)
from admission.ddd.admission.doctorat.preparation.dtos import ExperienceAcademiqueDTO
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceNonAcademiqueDTO
from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.dtos import EtudesSecondairesDTO, CoordonneesDTO, IdentificationDTO
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.dtos.titre_acces_selectionnable import TitreAccesSelectionnableDTO
from admission.ddd.admission.enums import TypeItemFormulaire, Onglets
from admission.ddd.admission.enums.emplacement_document import StatutReclamationEmplacementDocument
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    STATUTS_PROPOSITION_GENERALE_SOUMISE,
    RegleDeFinancement,
    RegleCalculeResultatAvecFinancable,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import INDEX_ONGLETS_CHECKLIST
from admission.ddd.admission.formation_generale.dtos.proposition import PropositionGestionnaireDTO, PropositionDTO
from admission.ddd.admission.repository.i_proposition import formater_reference
from admission.ddd.parcours_doctoral.formation.domain.model.enums import (
    CategorieActivite,
    ChoixTypeEpreuve,
    StatutActivite,
)
from admission.exports.admission_recap.section import (
    get_educational_experience_context,
    get_secondary_studies_context,
    get_non_educational_experience_context,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE,
    AnneeInscriptionFormationTranslator,
)
from admission.utils import format_academic_year, get_access_conditions_url
from base.models.person import Person
from osis_role.contrib.permissions import _get_roles_assigned_to_user
from osis_role.templatetags.osis_role import has_perm
from reference.models.country import Country

CONTEXT_ADMISSION = 'admission'
CONTEXT_DOCTORATE = 'doctorate'
CONTEXT_GENERAL = 'general-education'
CONTEXT_CONTINUING = 'continuing-education'

PERMISSION_BY_ADMISSION_CLASS = {
    DoctorateAdmission: 'doctorateadmission',
    GeneralEducationAdmission: 'generaleducationadmission',
    ContinuingEducationAdmission: 'continuingeducationadmission',
}

NAMUR = 'Namur'
TOURNAI = 'Tournai'
MONS = 'Mons'
CHARLEROI = 'Charleroi'
WOLUWE = 'Bruxelles Woluwe'
SAINT_LOUIS = 'Bruxelles Saint-Louis'
SAINT_GILLES = 'Bruxelles Saint-Gilles'

register = template.Library()


class PanelNode(template.library.InclusionNode):
    def __init__(self, nodelist: dict, func, takes_context, args, kwargs, filename):
        super().__init__(func, takes_context, args, kwargs, filename)
        self.nodelist_dict = nodelist

    def render(self, context):
        for context_name, nodelist in self.nodelist_dict.items():
            context[context_name] = nodelist.render(context)
        return super().render(context)


def register_panel(filename, takes_context=None, name=None):
    def dec(func):
        params, varargs, varkw, defaults, kwonly, kwonly_defaults, _ = getfullargspec(func)
        function_name = name or getattr(func, '_decorated_function', func).__name__

        @wraps(func)
        def compile_func(parser, token):
            # {% panel %} and its arguments
            bits = token.split_contents()[1:]
            args, kwargs = template.library.parse_bits(
                parser, bits, params, varargs, varkw, defaults, kwonly, kwonly_defaults, takes_context, function_name
            )
            nodelist_dict = {'panel_body': parser.parse(('footer', 'endpanel'))}
            token = parser.next_token()

            # {% footer %} (optional)
            if token.contents == 'footer':
                nodelist_dict['panel_footer'] = parser.parse(('endpanel',))
                parser.next_token()

            return PanelNode(nodelist_dict, func, takes_context, args, kwargs, filename)

        register.tag(function_name, compile_func)
        return func

    return dec


@register.simple_tag
def display(*args):
    """Display args if their value is not empty, can be wrapped by parenthesis, or separated by comma or dash"""
    ret = []
    iterargs = iter(args)
    nextarg = next(iterargs)
    while nextarg != StopIteration:
        if nextarg == "(":
            reduce_wrapping = [next(iterargs, None)]
            while reduce_wrapping[-1] != ")":
                reduce_wrapping.append(next(iterargs, None))
            ret.append(reduce_wrapping_parenthesis(*reduce_wrapping[:-1]))
        elif nextarg == ",":
            ret, val = ret[:-1], next(iter(ret[-1:]), '')
            ret.append(reduce_list_separated(val, next(iterargs, None)))
        elif nextarg in ["-", ':', ' - ']:
            ret, val = ret[:-1], next(iter(ret[-1:]), '')
            ret.append(reduce_list_separated(val, next(iterargs, None), separator=f" {nextarg} "))
        elif isinstance(nextarg, str) and len(nextarg) > 1 and re.match(r'\s', nextarg[0]):
            ret, suffixed_val = ret[:-1], next(iter(ret[-1:]), '')
            ret.append(f"{suffixed_val}{nextarg}" if suffixed_val else "")
        else:
            ret.append(SafeString(nextarg) if nextarg else '')
        nextarg = next(iterargs, StopIteration)
    return SafeString("".join(ret))


@register.simple_tag
def reduce_wrapping_parenthesis(*args):
    """Display args given their value, wrapped by parenthesis"""
    ret = display(*args)
    if ret:
        return SafeString(f"({ret})")
    return ret


@register.simple_tag
def reduce_list_separated(arg1, arg2, separator=", "):
    """Display args given their value, joined by separator"""
    if arg1 and arg2:
        return separator.join([SafeString(arg1), SafeString(arg2)])
    elif arg1:
        return SafeString(arg1)
    elif arg2:
        return SafeString(arg2)
    return ""


@register_panel('panel.html', takes_context=True)
def panel(context, title='', title_level=4, additional_class='', edit_link_button='', **kwargs):
    """
    Template tag for panel
    :param title: the panel title
    :param title_level: the title level
    :param additional_class: css class to add
    :param edit_link_button: url of the edit button
    :type context: django.template.context.RequestContext
    """
    context['title'] = title
    context['title_level'] = title_level
    context['additional_class'] = additional_class
    if edit_link_button:
        context['edit_link_button'] = edit_link_button
    context['attributes'] = {k.replace('_', '-'): v for k, v in kwargs.items()}
    return context


@register.inclusion_tag('admission/includes/sortable_header_div.html', takes_context=True)
def sortable_header_div(context, order_field_name, order_field_label):
    # Ascending sorting by default
    asc_ordering = True
    ordering_class = 'sort'

    query_params = getattr(context.get('view'), 'query_params', None) or context.request.GET

    query_order_param = query_params.get('o')

    # An order query parameter is already specified
    if query_order_param:
        current_order = query_order_param[0]
        current_order_field = query_order_param.lstrip('-')

        # The current field is already used to sort
        if order_field_name == current_order_field:
            if current_order == '-':
                ordering_class = 'sort-down'
            else:
                asc_ordering = False
                ordering_class = 'sort-up'

    new_params = query_params.copy()
    new_params['o'] = '{}{}'.format('' if asc_ordering else '-', order_field_name)
    new_params.pop('page', None)
    return {
        'field_label': order_field_label,
        'url': context.request.path + '?' + new_params.urlencode(),
        'ordering_class': ordering_class,
    }


# Manage the tabs
@dataclass
class Tab:
    name: str
    label: str = ''
    icon: str = ''
    badge: str = ''

    def __hash__(self):
        # Only hash the name, as lazy strings have different memory addresses
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name


TAB_TREES = {
    CONTEXT_ADMISSION: {
        Tab('personal', _('Personal data'), 'user'): [
            Tab('person', _('Identification')),
            Tab('coordonnees', _('Contact details')),
        ],
        # TODO Education choice
        Tab('experience', _('Previous experience'), 'list-alt'): [
            Tab('education', _('Secondary studies')),
            Tab('curriculum', _('Curriculum')),
            Tab('languages', _('Knowledge of languages')),
        ],
        Tab('doctorate', pgettext('tab', 'PhD project'), 'graduation-cap'): [
            Tab('project', _('Research project')),
            Tab('cotutelle', _('Cotutelle')),
            Tab('supervision', _('Supervision')),
        ],
        # TODO Specific aspects
        # TODO Completion
        Tab('management', pgettext('tab', 'Management'), 'gear'): [
            Tab('history-all', _('All history')),
            Tab('history', _('Status changes')),
            Tab('send-mail', _('Send a mail')),
            Tab('internal-note', _('Internal notes'), 'note-sticky'),
            Tab('debug', _('Debug'), 'bug'),
        ],
        Tab('comments', pgettext('tab', 'Comments'), 'comments'): [
            Tab('comments', pgettext('tab', 'Comments'), 'comments')
        ],
        # TODO Documents
    },
    CONTEXT_DOCTORATE: {
        Tab('person', _('Personal data'), 'user'): [
            Tab('person', _('Personal data'), 'user'),
            Tab('coordonnees', _('Contact details')),
        ],
        Tab('education', _('Previous experience'), 'list-alt'): [
            Tab('education', _('Previous experience'), 'list-alt'),
        ],
        Tab('doctorate', pgettext('tab', 'PhD project'), 'graduation-cap'): [
            Tab('project', pgettext('tab', 'Research project')),
            Tab('cotutelle', _('Cotutelle')),
            Tab('supervision', _('Supervision')),
        ],
        Tab('confirmation', pgettext('tab', 'Confirmation'), 'award'): [
            Tab('confirmation', _('Confirmation exam')),
            Tab('extension-request', _('New deadline')),
        ],
        Tab('training', pgettext('admission', 'Course'), 'book-open-reader'): [
            Tab('doctoral-training', _('PhD training')),
            Tab('complementary-training', _('Complementary training')),
            Tab('course-enrollment', _('Course unit enrolment')),
        ],
        Tab('defense', pgettext('doctorate tab', 'Defense'), 'person-chalkboard'): [
            Tab('jury-preparation', pgettext('admission tab', 'Defense method')),
            Tab('jury', _('Jury composition')),
        ],
        Tab('management', pgettext('tab', 'Management'), 'gear'): [
            Tab('history-all', _('All history')),
            Tab('history', _('Status changes')),
            Tab('send-mail', _('Send a mail')),
            Tab('debug', _('Debug'), 'bug'),
        ],
        Tab('comments', pgettext('tab', 'Comments'), 'comments'): [
            Tab('comments', pgettext('tab', 'Comments'), 'comments')
        ],
        # TODO Documents
    },
    CONTEXT_GENERAL: {
        Tab('checklist', _('Checklist'), 'list-check'): [
            Tab('checklist', _('Checklist'), 'list-check'),
        ],
        Tab('documents', _('Documents'), 'folder-open'): [
            Tab('documents', _('Documents'), 'folder-open'),
        ],
        Tab('comments', pgettext('tab', 'Comments'), 'comments'): [
            Tab('comments', pgettext('tab', 'Comments'), 'comments')
        ],
        Tab('history', pgettext('tab', 'History'), 'history'): [
            Tab('history-all', _('All history')),
            Tab('history', _('Status changes')),
        ],
        Tab('person', _('Personal data'), 'user'): [
            Tab('person', _('Identification'), 'user'),
            Tab('coordonnees', _('Contact details'), 'user'),
        ],
        Tab('general-education', _('Course choice'), 'person-chalkboard'): [
            Tab('training-choice', _('Course choice')),
        ],
        Tab('additional-information', _('Additional information'), 'puzzle-piece'): [
            Tab('accounting', _('Accounting')),
            Tab('specific-questions', _('Specific aspects')),
        ],
    },
    CONTEXT_CONTINUING: {
        Tab('person', _('Personal data'), 'user'): [
            Tab('person', _('Identification'), 'user'),
            Tab('coordonnees', _('Contact details'), 'user'),
        ],
        Tab('management', pgettext('tab', 'Management'), 'gear'): [
            Tab('debug', _('Debug'), 'bug'),
        ],
        Tab('comments', pgettext('tab', 'Comments'), 'comments'): [
            Tab('comments', pgettext('tab', 'Comments'), 'comments')
        ],
    },
}


def get_active_parent(tab_tree, tab_name):
    return next(
        (parent for parent, children in tab_tree.items() if any(child.name == tab_name for child in children)),
        None,
    )


def get_valid_tab_tree(context, permission_obj, tab_tree):
    """
    Return a tab tree based on the specified one but whose tabs depending on the permissions.
    """
    valid_tab_tree = {}

    # Loop over the tabs of the original tab tree
    for parent_tab, sub_tabs in tab_tree.items():
        # Get the accessible sub tabs depending on the user permissions
        valid_sub_tabs = [tab for tab in sub_tabs if can_read_tab(context, tab.name, permission_obj)]

        # Checklist is available for submitted admissions only
        if Tab('checklist') in valid_sub_tabs:
            if permission_obj.status not in STATUTS_PROPOSITION_GENERALE_SOUMISE:
                valid_sub_tabs.remove(Tab('checklist'))

        # Add dynamic badge for comments
        if parent_tab == Tab('comments'):
            from admission.views.common.detail_tabs.comments import COMMENT_TAG_FAC, COMMENT_TAG_SIC, COMMENT_TAG_GLOBAL

            roles = _get_roles_assigned_to_user(context['request'].user)
            qs = CommentEntry.objects.filter(object_uuid=context['view'].kwargs['uuid'])
            if {SicManagement, CentralManager} & set(roles):
                parent_tab.badge = qs.filter(tags__contains=[COMMENT_TAG_SIC, COMMENT_TAG_GLOBAL]).count()
            elif {ProgramManager} & set(roles):
                parent_tab.badge = qs.filter(tags__contains=[COMMENT_TAG_FAC, COMMENT_TAG_GLOBAL]).count()

        # Only add the parent tab if at least one sub tab is allowed
        if len(valid_sub_tabs) > 0:
            valid_tab_tree[parent_tab] = valid_sub_tabs

    return valid_tab_tree


@register.simple_tag(takes_context=True)
def default_tab_context(context):
    match = context['request'].resolver_match
    active_tab = match.url_name

    if len(match.namespaces) > 2 and match.namespaces[2] != 'update':
        active_tab = match.namespaces[2]
    elif len(match.namespaces) > 3 and match.namespaces[3] == 'jury-member':
        active_tab = 'jury'

    tab_tree = TAB_TREES[get_current_context(context['view'].get_permission_object())]
    active_parent = get_active_parent(tab_tree, active_tab)

    return {
        'active_parent': active_parent,
        'active_tab': active_tab,
        'admission_uuid': context['view'].kwargs.get('uuid', ''),
        'namespace': ':'.join(match.namespaces[:2]),
        'request': context['request'],
        'view': context['view'],
    }


@register.inclusion_tag('admission/includes/admission_tabs_bar.html', takes_context=True)
def admission_tabs(context):
    tab_context = default_tab_context(context)
    admission = context['view'].get_permission_object()
    current_tab_tree = get_valid_tab_tree(context, admission, TAB_TREES[get_current_context(admission)]).copy()
    tab_context['tab_tree'] = current_tab_tree
    return tab_context


@register.simple_tag(takes_context=True)
def current_subtabs(context):
    tab_context = default_tab_context(context)
    permission_obj = context['view'].get_permission_object()
    tab_tree = TAB_TREES[get_current_context(admission=permission_obj)]
    tab_context['subtabs'] = (
        [tab for tab in tab_tree[tab_context['active_parent']] if can_read_tab(context, tab.name, permission_obj)]
        if tab_context['active_parent']
        else []
    )
    return tab_context


def get_current_context(admission: Union[DoctorateAdmission, GeneralEducationAdmission, ContinuingEducationAdmission]):
    if isinstance(admission, DoctorateAdmission):
        if admission.status in STATUTS_PROPOSITION_AVANT_INSCRIPTION:
            return CONTEXT_ADMISSION
        return CONTEXT_DOCTORATE
    elif isinstance(admission, GeneralEducationAdmission):
        return CONTEXT_GENERAL
    elif isinstance(admission, ContinuingEducationAdmission):
        return CONTEXT_CONTINUING


@register.inclusion_tag('admission/includes/doctorate_subtabs_bar.html', takes_context=True)
def doctorate_subtabs_bar(context):
    return current_subtabs(context)


@register.simple_tag(takes_context=True)
def update_tab_path_from_detail(context, admission_uuid):
    """From a detail page, get the path of the update page."""
    match = context['request'].resolver_match
    try:
        return reverse(
            '{}:update:{}'.format(':'.join(match.namespaces), match.url_name),
            args=[admission_uuid],
        )
    except NoReverseMatch:
        if len(match.namespaces) > 2:
            path = ':'.join(match.namespaces[:3])
        else:
            path = '{}:{}'.format(':'.join(match.namespaces), match.url_name)
        return reverse(
            path,
            args=[admission_uuid],
        )


@register.simple_tag(takes_context=True)
def detail_tab_path_from_update(context, admission_uuid):
    """From an update page, get the path of the detail page."""
    match = context['request'].resolver_match
    current_tab_name = match.url_name
    if len(match.namespaces) > 2 and match.namespaces[2] != 'update':
        current_tab_name = match.namespaces[2]
    return reverse(
        '{}:{}'.format(':'.join(match.namespaces[:-1]), current_tab_name),
        args=[admission_uuid],
    )


@register.inclusion_tag('admission/includes/field_data.html', takes_context=True)
def field_data(
    context,
    name,
    data=None,
    css_class=None,
    hide_empty=False,
    translate_data=False,
    inline=False,
    html_tag='',
    tooltip=None,
):
    if context.get('all_inline') is True:
        inline = True

    if isinstance(data, list):
        if context.get('hide_files') is True:
            data = None
            hide_empty = True
        elif context.get('load_files') is False:
            data = _('Specified') if data else _('Incomplete field')
        elif data:
            template_string = "{% load osis_document %}{% document_visualizer files for_modified_upload=True %}"
            template_context = {'files': data}
            data = template.Template(template_string).render(template.Context(template_context))
        else:
            data = ''
    elif type(data) == bool:
        data = _('Yes') if data else _('No')
    elif translate_data is True:
        data = _(data)

    if inline is True:
        if name and name[-1] not in ':?!.':
            name = _("%(label)s:") % {'label': name}
        css_class = (css_class + ' inline-field-data') if css_class else 'inline-field-data'

    return {
        'name': name,
        'data': data,
        'css_class': css_class,
        'hide_empty': hide_empty,
        'html_tag': html_tag,
        'inline': inline,
        'tooltip': tooltip,
    }


@register.simple_tag
def get_image_file_url(file_uuids):
    """Returns the url of the file whose uuid is the first of the specified ones, if it is an image."""
    if file_uuids:
        token = get_remote_token(file_uuids[0], for_modified_upload=True)
        if token:
            metadata = get_remote_metadata(token)
            if metadata and metadata.get('mimetype') in IMAGE_MIME_TYPES:
                return metadata.get('url')
    return ''


@register.inclusion_tag('admission/dummy.html')
def document_component(document_write_token, document_metadata, can_edit=True):
    """Display the right editor component depending on the file type."""
    if document_metadata:
        if document_metadata.get('mimetype') == PDF_MIME_TYPE:
            attrs = {}
            if not can_edit:
                attrs = {action: False for action in ['pagination', 'zoom', 'rotation']}
            return {
                'template': 'osis_document/editor.html',
                'value': document_write_token,
                'base_url': settings.OSIS_DOCUMENT_BASE_URL,
                'attrs': attrs
            }
        elif document_metadata.get('mimetype') in IMAGE_MIME_TYPES:
            return {
                'template': 'admission/image.html',
                'url': document_metadata.get('url'),
                'alt': document_metadata.get('name'),
            }
    return {
        'template': 'admission/no_document.html',
        'message': _('Non-retrievable document') if document_write_token else _('No document'),
    }


@register.filter
def phone_spaced(phone, with_optional_zero=False):
    if not phone:
        return ""
    # Taken from https://github.com/daviddrysdale/python-phonenumbers/blob/dev/python/phonenumbers/data/region_BE.py#L14
    if with_optional_zero and phone[0] == "0":
        return "(0)" + re.sub('(\\d{2})(\\d{2})(\\d{2})(\\d{2})', '\\1 \\2 \\3 \\4', phone[1:])
    return re.sub('(\\d{3})(\\d{2})(\\d{2})(\\d{2})', '\\1 \\2 \\3 \\4', phone)


@register.filter
def strip(value):
    if isinstance(value, str):
        return value.strip()
    return value


@register.filter
def status_list(admission):
    statuses = {str(admission.status)}
    for child in admission.children.all():
        statuses.add(str(child.status))
    return ','.join(statuses)


@register.filter
def status_as_class(activity):
    return {
        StatutActivite.SOUMISE.name: "warning",
        StatutActivite.ACCEPTEE.name: "success",
        StatutActivite.REFUSEE.name: "danger",
    }.get(getattr(activity, 'status', activity), 'info')


@register.inclusion_tag('admission/includes/bootstrap_field_with_tooltip.html')
def bootstrap_field_with_tooltip(field, classes='', show_help=False, html_tooltip=False):
    return {
        'field': field,
        'classes': classes,
        'show_help': show_help,
        'html_tooltip': html_tooltip,
    }


@register.simple_tag(takes_context=True)
def has_perm(context, perm, obj=None):
    if not obj:
        obj = context['view'].get_permission_object()
    perm = perm % {'[context]': PERMISSION_BY_ADMISSION_CLASS[type(obj)]}
    return rules.has_perm(perm, context['request'].user, obj)


@register.simple_tag
def not_bool(value: bool):
    return not value


@register.simple_tag(takes_context=True)
def can_read_tab(context, tab_name, obj=None):
    """Return true if the specified tab can be opened in reading mode for this admission, otherwise return False"""
    return has_perm(context, READ_ACTIONS_BY_TAB[tab_name], obj)


@register.simple_tag(takes_context=True)
def can_update_tab(context, tab_name, obj=None):
    """Return true if the specified tab can be opened in update mode for this admission, otherwise return False"""
    return has_perm(context, UPDATE_ACTIONS_BY_TAB[tab_name], obj)


@register.inclusion_tag('admission/doctorate/includes/training_categories.html')
def training_categories(activities):
    added, validated = 0, 0

    categories = {
        _("Participation to symposium/conference"): [0, 0],
        _("Oral communication"): [0, 0],
        _("Seminar taken"): [0, 0],
        _("Publications"): [0, 0],
        _("Courses taken"): [0, 0],
        _("Services"): [0, 0],
        _("VAE"): [0, 0],
        _("Scientific residencies"): [0, 0],
        _("Confirmation exam"): [0, 0],
        _("Thesis defense"): [0, 0],
    }
    for activity in activities:
        # Increment global counts
        if activity.status != StatutActivite.REFUSEE.name:
            added += activity.ects
        if activity.status == StatutActivite.ACCEPTEE.name:
            validated += activity.ects
        if activity.status not in [StatutActivite.SOUMISE.name, StatutActivite.ACCEPTEE.name]:
            continue

        # Increment category counts
        index = int(activity.status == StatutActivite.ACCEPTEE.name)
        if activity.category == CategorieActivite.CONFERENCE.name:
            categories[_("Participation to symposium/conference")][index] += activity.ects
        elif activity.category == CategorieActivite.SEMINAR.name:
            categories[_("Seminar taken")][index] += activity.ects
        elif activity.category == CategorieActivite.COMMUNICATION.name and (
            activity.parent_id is None or activity.parent.category == CategorieActivite.CONFERENCE.name
        ):
            categories[_("Oral communication")][index] += activity.ects
        elif activity.category == CategorieActivite.PUBLICATION.name and (
            activity.parent_id is None or activity.parent.category == CategorieActivite.CONFERENCE.name
        ):
            categories[_("Publications")][index] += activity.ects
        elif activity.category == CategorieActivite.SERVICE.name:
            categories[_("Services")][index] += activity.ects
        elif (
            activity.category == CategorieActivite.RESIDENCY.name
            or activity.parent_id
            and activity.parent.category == CategorieActivite.RESIDENCY.name
        ):
            categories[_("Scientific residencies")][index] += activity.ects
        elif activity.category == CategorieActivite.VAE.name:
            categories[_("VAE")][index] += activity.ects
        elif activity.category in [CategorieActivite.COURSE.name, CategorieActivite.UCL_COURSE.name]:
            categories[_("Courses taken")][index] += activity.ects
        elif (
            activity.category == CategorieActivite.PAPER.name
            and activity.type == ChoixTypeEpreuve.CONFIRMATION_PAPER.name
        ):
            categories[_("Confirmation exam")][index] += activity.ects
        elif activity.category == CategorieActivite.PAPER.name:
            categories[_("Thesis defense")][index] += activity.ects
    if not added:
        return {}
    return {
        'display_table': any(cat_added + cat_validated for cat_added, cat_validated in categories.values()),
        'categories': categories,
        'added': added,
        'validated': validated,
    }


@register.filter
def formatted_reference(admission: BaseAdmission):
    return formater_reference(
        reference=admission.reference,
        nom_campus_inscription=admission.training.enrollment_campus.name,
        sigle_entite_gestion=admission.training_management_faculty or admission.sigle_entite_gestion,  # From annotation
        annee=admission.training.academic_year.year,
    )


@register.filter
def formatted_language(language: str):
    return language[:2].upper() if language else ''


@register.filter
def get_academic_year(year: Union[int, str, float]):
    """Return the academic year related to a specific year."""
    return format_academic_year(year)


@register.filter
def get_short_academic_year(year: Union[int, str, float]):
    """Return the academic year related to a specific year with only two digits for the end year."""
    return format_academic_year(year, short=True)


@register.filter
def get_last_inscription_date(year: Union[int, str, float]):
    """Return the academic year related to a specific year."""
    return datetime.date(year, 9, 30)


@register.filter(is_safe=False)
def default_if_none_or_empty(value, arg):
    """If value is None or empty, use given default."""
    return value if value not in EMPTY_VALUES else arg


@register.simple_tag
def concat(*args):
    """Concatenate a list of strings."""
    return ''.join(args)


@register.inclusion_tag('admission/includes/multiple_field_data.html', takes_context=True)
def multiple_field_data(context, configurations: List[QuestionSpecifiqueDTO], title=_('Specific aspects'), **kwargs):
    """Display the answers of the specific questions based on a list of configurations."""
    return {
        'fields': configurations,
        'title': title,
        'all_inline': context.get('all_inline'),
        'load_files': context.get('load_files'),
        'hide_files': context.get('hide_files'),
        'edit_link_button': kwargs.get('edit_link_button'),
    }


@register.simple_tag
def need_to_display_specific_questions(configurations: List[QuestionSpecifiqueDTO], hide_files=False):
    return bool(
        configurations
        and (
            not hide_files
            or any(configuration.type != TypeItemFormulaire.DOCUMENT.name for configuration in configurations)
        )
    )


@register.filter
def admission_training_type(osis_training_type: str):
    """Returns the admission training type based on the osis training type."""
    return AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.get(osis_training_type)


@register.simple_tag
def get_first_truthy_value(*args):
    """Returns the first truthy value"""
    return next((arg for arg in args if arg), None)


@register.filter
def get_item(dictionary, value):
    """Returns the value of a key in a dictionary if it exists else the value itself"""
    return dictionary.get(value, value)


@register.filter
def get_item_or_none(dictionary, value):
    """Returns the value of a key in a dictionary if it exists else None"""
    return dictionary.get(value)


@register.simple_tag
def get_item_or_default(dictionary, value, default=None):
    """Returns the value of a key in a dictionary if it exists else the default value itself"""
    return dictionary.get(value, default)


@register.filter
def part_of_dict(member, container):
    """Check if a dict is containing into another one"""
    return member.items() <= container.items()


@register.simple_tag
def is_current_checklist_status(current, state, extra):
    return current.get('statut') == state and part_of_dict(extra, current.get('extra', {}))


@register.simple_tag
def has_value(iterable, values):
    return any(value in iterable for value in values)


@register.simple_tag
def interpolate(string, **kwargs):
    """Interpolate variables inside a string"""
    return string % kwargs


@register.simple_tag
def admission_url(admission_uuid: str, osis_education_type: str):
    """Get the base URL of a specific admission"""
    admission_context = ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE.get(osis_education_type)
    if admission_context is None:
        return None
    return reverse(f'admission:{admission_context}', kwargs={'uuid': admission_uuid})


@register.simple_tag
def admission_status(status: str, osis_education_type: str):
    """Get the status of a specific admission"""
    admission_context = ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE.get(osis_education_type)
    return (
        {
            'general-education': ChoixStatutPropositionGenerale,
            'continuing-education': ChoixStatutPropositionContinue,
            'doctorate': ChoixStatutPropositionDoctorale,
        }
        .get(admission_context)
        .get_value(status)
    )


@register.simple_tag
def get_country_name(country: Optional[Country]):
    """Return the country name."""
    if not country:
        return ''
    return getattr(country, 'name' if get_language() == settings.LANGUAGE_CODE_FR else 'name_en')


@register.filter
def get_ordered_checklist_items(checklist_items: dict):
    """Return the ordered checklist items."""
    return sorted(checklist_items.items(), key=lambda tab: INDEX_ONGLETS_CHECKLIST[tab[0]])


@register.filter
def is_list(value) -> bool:
    return isinstance(value, list)


@register.inclusion_tag('admission/checklist_state_button.html', takes_context=True)
def checklist_state_button(context, **kwargs):
    expected_attrs = {
        arg_name: kwargs.pop(arg_name, None)
        for arg_name in [
            'label',
            'icon',
            'state',
            'class',
            'tab',
            'tooltip',
            'disabled',
            'open_modal',
            'htmx_post',
            'sub_id',
        ]
    }

    if context.get('can_update_checklist_tab') is False:
        expected_attrs['disabled'] = True

    return {
        'current': context['current'] or context['initial'],
        **expected_attrs,
        'extra': kwargs,
        'view': context['view'],
        'submitted_extra': {
            **kwargs,
            'status': expected_attrs['state'],
        },
    }


@register.filter
def edit_button(string, url):
    return (
        str(string)
        + f'<a class="btn btn-default" href="{url}"><i class="fas fa-{"edit" if "update" in url else "eye"}"></i></a>'
    )


@register.filter
def tab_edit_button(string, tab_hash):
    return (
        str(string) + f'<a class="btn btn-default tab-edit-button" data-toggle="checklist-tab" href="{tab_hash}">'
        f'<i class="fas fa-edit"></i></a>'
    )


@register.filter
def history_entry_message(history_entry: Optional[HistoryEntry]):
    if history_entry:
        return {
            settings.LANGUAGE_CODE_FR: history_entry.message_fr,
            settings.LANGUAGE_CODE_EN: history_entry.message_en,
        }[get_language()]
    return ''


@register.filter
def label_with_user_icon(label):
    return mark_safe(f'{label} <i class="fas fa-user"></i>')


@register.filter
def diplomatic_post_name(diplomatic_post):
    """Get the name of a diplomatic post"""
    if diplomatic_post:
        return getattr(
            diplomatic_post,
            'nom_francais' if get_language() == settings.LANGUAGE_CODE_FR else 'nom_anglais',
        )


@register.filter
def is_profile_identification_different(
    profil_candidat: ProfilCandidatDTO,
    identification: Union[Person, IdentificationDTO],
):
    if profil_candidat is None or identification is None:
        return False
    if isinstance(identification, Person):
        return any(
            (
                profil_candidat.nom != identification.last_name,
                profil_candidat.prenom != identification.first_name,
                profil_candidat.genre != identification.gender,
                profil_candidat.nationalite
                != (identification.country_of_citizenship.iso_code if identification.country_of_citizenship else ''),
            )
        )
    return any(
        (
            profil_candidat.nom != identification.nom,
            profil_candidat.prenom != identification.prenom,
            profil_candidat.genre != identification.genre,
            profil_candidat.nationalite != identification.pays_nationalite,
        )
    )


@register.filter
def is_profile_coordinates_different(profil_candidat: ProfilCandidatDTO, coordonnees: Union[CoordonneesDTO, dict]):
    if profil_candidat is None or coordonnees is None:
        return False
    if isinstance(coordonnees, CoordonneesDTO):
        if coordonnees.domicile_legal is None:
            return False
        if coordonnees.adresse_correspondance is not None:
            adresse = coordonnees.adresse_correspondance
        else:
            adresse = coordonnees.domicile_legal
        if not adresse:
            return False
        return any(
            (
                str(profil_candidat.numero_rue) != str(adresse.numero_rue),
                profil_candidat.rue != adresse.rue,
                profil_candidat.boite_postale != adresse.boite_postale,
                profil_candidat.code_postal != adresse.code_postal,
                profil_candidat.ville != adresse.ville,
                profil_candidat.pays != adresse.pays,
            )
        )
    if coordonnees['contact'] is not None:
        adresse = coordonnees['contact']
    else:
        adresse = coordonnees['residential']
    if not adresse:
        return False
    return any(
        (
            str(profil_candidat.numero_rue) != adresse.street_number,
            profil_candidat.rue != adresse.street,
            profil_candidat.boite_postale != adresse.postal_box,
            profil_candidat.code_postal != adresse.postal_code,
            profil_candidat.ville != adresse.city,
            profil_candidat.pays != adresse.country.iso_code,
        )
    )


@register.inclusion_tag(
    'admission/general_education/includes/checklist/parcours_row_access_title.html',
    takes_context=True,
)
def access_title_checkbox(context, experience_uuid, experience_type, current_year):
    access_title: Optional[TitreAccesSelectionnableDTO] = context['access_titles'].get(experience_uuid)
    if access_title and access_title.annee == current_year:
        return {
            'url': f'{context["access_title_url"]}?experience_uuid={experience_uuid}&experience_type={experience_type}',
            'checked': access_title.selectionne,
            'experience_uuid': experience_uuid,
            'can_choose_access_title': context['can_choose_access_title'],
        }


@register.filter
def document_request_status_css_class(document_request_status):
    return {
        StatutReclamationEmplacementDocument.IMMEDIATEMENT.name: 'text-dark',
        StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT.name: 'text-danger',
        StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name: 'text-orange',
    }.get(document_request_status, '')


@register.filter
def financability_enum_display(value):
    if value in RegleDeFinancement.get_names():
        return '{} - {}'.format(_('Financable'), RegleDeFinancement[value].value)
    return RegleCalculeResultatAvecFinancable[value].value


@register.filter
def authentication_css_class(authentication_status):
    """
    Return the CSS classes to apply to the authentication icon
    :param authentication_status: The authentication status
    :return: A string containing the CSS classes
    """
    return (
        {
            EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name: 'fa-solid fa-file-circle-question text-orange',
            EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name: 'fa-solid fa-file-circle-question text-orange',
            EtatAuthentificationParcours.FAUX.name: 'fa-solid fa-file-circle-xmark text-danger',
            EtatAuthentificationParcours.VRAI.name: 'fa-solid fa-file-circle-check text-success',
        }.get(authentication_status, '')
        if authentication_status
        else ''
    )


@register.filter
def bg_class_by_checklist_experience(experience):
    return {
        ExperienceAcademiqueDTO: 'bg-info',
        EtudesSecondairesDTO: 'bg-warning',
    }.get(experience.__class__, '')


@register.inclusion_tag('admission/includes/custom_base_template.html')
def experience_details_template(
    resume_proposition: ResumePropositionDTO,
    experience,
    specific_questions: Dict[str, List[QuestionSpecifiqueDTO]] = None,
    with_edit_link_button=True,
    hide_files=True,
):
    """
    Return the template used to render the experience details.
    :param resume_proposition: The proposition resume
    :param experience: The experience
    :param specific_questions: The specific questions related to the experience (only used for secondary studies)
    :return: The rendered template
    """
    context = {
        'is_general': resume_proposition.est_proposition_generale,
        'is_continuing': resume_proposition.est_proposition_continue,
        'is_doctorate': resume_proposition.est_proposition_doctorale,
        'formation': resume_proposition.proposition.formation,
        'hide_files': hide_files,
        'checklist_display': True,
    }
    if experience.__class__ == ExperienceAcademiqueDTO:
        context['custom_base_template'] = 'admission/exports/recap/includes/curriculum_educational_experience.html'
        context['title'] = _('Academic experience')
        context['edit_link_button'] = (
            reverse(
                'admission:general-education:update:curriculum:educational',
                args=[resume_proposition.proposition.uuid, experience.uuid],
            )
            if with_edit_link_button
            else None
        )
        context.update(get_educational_experience_context(resume_proposition, experience))

    elif experience.__class__ == ExperienceNonAcademiqueDTO:
        context['custom_base_template'] = 'admission/exports/recap/includes/curriculum_professional_experience.html'
        context['title'] = _('Non-academic experience')
        context['edit_link_button'] = (
            reverse(
                'admission:general-education:update:curriculum:non_educational',
                args=[resume_proposition.proposition.uuid, experience.uuid],
            )
            if with_edit_link_button
            else None
        )
        context.update(get_non_educational_experience_context(experience))

    elif experience.__class__ == EtudesSecondairesDTO:
        context['custom_base_template'] = 'admission/exports/recap/includes/education.html'
        context['etudes_secondaires'] = experience
        context['edit_link_button'] = (
            reverse(
                'admission:general-education:update:education',
                args=[resume_proposition.proposition.uuid],
            )
            if with_edit_link_button
            else None
        )
        context.update(
            get_secondary_studies_context(
                resume_proposition,
                specific_questions[Onglets.ETUDES_SECONDAIRES.name],
            )
        )

    return context


@register.inclusion_tag(
    'admission/general_education/includes/checklist/parcours_row_actions_links.html',
    takes_context=True,
)
def checklist_experience_action_links(
    context,
    experience: Union[ExperienceAcademiqueDTO, ExperienceNonAcademiqueDTO, EtudesSecondairesDTO],
    current_year,
):
    base_namespace = context['view'].base_namespace
    proposition_uuid = context['view'].kwargs['uuid']
    proposition_uuid_str = str(proposition_uuid)
    if experience.__class__ == EtudesSecondairesDTO:
        return {
            'update_url': resolve_url(
                f'{base_namespace}:update:education',
                uuid=proposition_uuid_str,
            ),
        }
    elif proposition_uuid in experience.valorisee_par_admissions and experience.derniere_annee == current_year:
        if experience.__class__ == ExperienceAcademiqueDTO:
            return {
                'update_url': resolve_url(
                    f'{base_namespace}:update:curriculum:educational',
                    uuid=proposition_uuid_str,
                    experience_uuid=experience.uuid,
                ),
            }
        elif experience.__class__ == ExperienceNonAcademiqueDTO:
            return {
                'update_url': resolve_url(
                    f'{base_namespace}:update:curriculum:non_educational',
                    uuid=proposition_uuid_str,
                    experience_uuid=experience.uuid,
                ),
            }


@register.filter
def est_premiere_annee(admission: Union[PropositionGestionnaireDTO, DemandeRechercheDTO]):
    if isinstance(admission, PropositionGestionnaireDTO):
        return admission.poursuite_de_cycle == 'TO_BE_DETERMINED' or admission.poursuite_de_cycle == 'NO'
    elif isinstance(admission, DemandeRechercheDTO):
        return admission.est_premiere_annee
    return None


@register.filter
def intitule_premiere_annee(intitule: str):
    return _("First year of") + ' ' + intitule.lower()


@register.inclusion_tag('admission/exports/includes/footer_campus.html')
def footer_campus(proposition):
    CAMPUS = {
        NAMUR: 'NAMUR',
        TOURNAI: 'TOURNAI',
        MONS: 'MONS',
        CHARLEROI: 'CHARLEROI',
        WOLUWE: 'BRUXELLES',
        SAINT_LOUIS: 'BRUXELLES',
        SAINT_GILLES: 'BRUXELLES',
    }

    return {
        'campus': CAMPUS.get(proposition.formation.campus_inscription.nom, 'LLN'),
        'proposition': proposition,
    }


@register.simple_tag
def candidate_language(language):
    return mark_safe(
        f' <strong>({_("contact language")} </strong>'
        f'<span class="label label-admission-primary">{formatted_language(language)}</span>)'
    )


@register.filter
def admission_has_refusal(admission):
    return admission.type_de_refus and (admission.motifs_refus or admission.autres_motifs_refus)


@register.filter
def get_intitule_in_candidate_language(proposition: PropositionGestionnaireDTO):
    if proposition.langue_contact_candidat == settings.LANGUAGE_CODE_FR:
        return proposition.formation.intitule_fr
    return proposition.formation.intitule_en


@register.filter
def sic_can_edit(proposition: PropositionGestionnaireDTO):
    return proposition.statut in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC


@register.filter
def sic_in_final_statut(checklist_statut):
    return checklist_statut['statut'] == ChoixStatutChecklist.GEST_REUSSITE.name or (
        checklist_statut['statut'] == ChoixStatutChecklist.GEST_BLOCAGE.name
        and checklist_statut['extra']['blocage'] != 'to_be_completed'
    )


@register.filter
def access_conditions_url(proposition: PropositionDTO):
    training = BaseAdmission.objects.values(
        'training__education_group_type__name', 'training__acronym', 'training__partial_acronym'
    ).get(uuid=proposition.uuid)
    return get_access_conditions_url(
        training_type=training['training__education_group_type__name'],
        training_acronym=training['training__acronym'],
        partial_training_acronym=training['training__partial_acronym'],
    )
