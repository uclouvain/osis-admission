# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

import datetime
import re
from dataclasses import dataclass
from functools import wraps
from inspect import getfullargspec
from typing import Dict, List, Optional, Union
from urllib.parse import urlencode

import attr
from django import template
from django.conf import settings
from django.core.validators import EMPTY_VALUES
from django.db.models import Q
from django.shortcuts import resolve_url
from django.template.defaultfilters import unordered_list
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import get_language, gettext
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext
from osis_comment.models import CommentEntry
from osis_document.api.utils import get_remote_metadata, get_remote_token
from osis_history.models import HistoryEntry
from rules.templatetags import rules

from admission.auth.constants import READ_ACTIONS_BY_TAB, UPDATE_ACTIONS_BY_TAB
from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.program_manager import ProgramManager
from admission.auth.roles.sic_management import SicManagement
from admission.constants import (
    CONTEXT_CONTINUING,
    CONTEXT_DOCTORATE,
    CONTEXT_GENERAL,
    IMAGE_MIME_TYPES,
    ORDERED_CAMPUSES_UUIDS,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    INDEX_ONGLETS_CHECKLIST as INDEX_ONGLETS_CHECKLIST_DOCTORALE,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixSexe
from admission.ddd.admission.domain.model.enums.authentification import (
    EtatAuthentificationParcours,
)
from admission.ddd.admission.dtos import (
    CoordonneesDTO,
    EtudesSecondairesAdmissionDTO,
    IdentificationDTO,
)
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.dtos.titre_acces_selectionnable import (
    TitreAccesSelectionnableDTO,
)
from admission.ddd.admission.enums import (
    LABEL_AFFILIATION_SPORT_SI_NEGATIF_SELON_SITE,
    ChoixAffiliationSport,
    Onglets,
    TypeItemFormulaire,
)
from admission.ddd.admission.enums.emplacement_document import (
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixMoyensDecouverteFormation,
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_continue.domain.model.statut_checklist import (
    INDEX_ONGLETS_CHECKLIST as INDEX_ONGLETS_CHECKLIST_CONTINUE,
)
from admission.ddd.admission.formation_continue.dtos.proposition import (
    PropositionDTO as PropositionContinueDTO,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC,
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    INDEX_ONGLETS_CHECKLIST as INDEX_ONGLETS_CHECKLIST_GENERALE,
)
from admission.ddd.admission.formation_generale.dtos.proposition import (
    PropositionDTO as PropositionGeneraleDTO,
)
from admission.ddd.admission.formation_generale.dtos.proposition import (
    PropositionGestionnaireDTO,
)
from admission.ddd.admission.repository.i_proposition import formater_reference
from admission.exports.admission_recap.section import (
    get_educational_experience_context,
    get_non_educational_experience_context,
    get_secondary_studies_context,
)
from admission.forms.admission.doctorate.supervision import (
    DoctorateAdmissionMemberSupervisionForm,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE,
    AnneeInscriptionFormationTranslator,
)
from admission.models import (
    ContinuingEducationAdmission,
    DoctorateAdmission,
    GeneralEducationAdmission,
)
from admission.models.base import BaseAdmission
from admission.utils import (
    format_address,
    format_school_title,
    get_access_conditions_url,
    get_experience_urls,
    get_superior_institute_queryset,
)
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.civil_state import CivilState
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from ddd.logic.financabilite.domain.model.enums.situation import SituationFinancabilite
from ddd.logic.shared_kernel.campus.dtos import UclouvainCampusDTO
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import (
    ExperienceAcademiqueDTO,
    ExperienceNonAcademiqueDTO,
    MessageCurriculumDTO,
)
from ddd.logic.shared_kernel.profil.dtos.parcours_interne import (
    ExperienceParcoursInterneDTO,
)
from osis_role.contrib.permissions import _get_roles_assigned_to_user
from osis_role.templatetags.osis_role import has_perm
from reference.models.country import Country
from reference.models.language import Language

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
def panel(
    context,
    title='',
    title_level=4,
    additional_class='',
    edit_link_button='',
    edit_link_button_in_new_tab=False,
    **kwargs,
):
    """
    Template tag for panel
    :param title: the panel title
    :param title_level: the title level
    :param additional_class: css class to add
    :param edit_link_button: url of the edit button
    :param edit_link_button_in_new_tab: open the edit link in a new tab
    :type context: django.template.context.RequestContext
    """
    context['title'] = title
    context['title_level'] = title_level
    context['additional_class'] = additional_class
    if edit_link_button:
        context['edit_link_button'] = edit_link_button
        context['edit_link_button_in_new_tab'] = edit_link_button_in_new_tab
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
    icon_after: str = ''

    def __hash__(self):
        # Only hash the name, as lazy strings have different memory addresses
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name


TAB_TREES = {
    CONTEXT_DOCTORATE: {
        Tab('checklist', _('Checklist'), 'list-check'): [
            Tab('checklist', _('Checklist'), 'list-check'),
        ],
        Tab('documents', _('Documents'), 'folder-open'): [
            Tab('documents', _('Documents'), 'folder-open'),
        ],
        Tab('send-mail', _('Send a mail'), 'envelope'): [
            Tab('send-mail', _('Send a mail'), 'envelope'),
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
        Tab('doctorate-education', _('Course choice'), 'person-chalkboard'): [
            Tab('training-choice', _('Course choice')),
        ],
        Tab('doctorate', pgettext('tab', 'Research'), 'graduation-cap'): [
            Tab('project', pgettext('tab', 'Research')),
            Tab('cotutelle', _('Cotutelle')),
            Tab('supervision', _('Supervision')),
        ],
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
        Tab('checklist', _('Checklist'), 'list-check'): [
            Tab('checklist', _('Checklist'), 'list-check'),
        ],
        Tab('documents', _('Documents'), 'folder-open'): [
            Tab('documents', _('Documents'), 'folder-open'),
        ],
        Tab('person', _('Personal data'), 'user'): [
            Tab('person', _('Identification'), 'user'),
            Tab('coordonnees', _('Contact details'), 'user'),
        ],
        Tab('continuing-education', _('Course choice'), 'person-chalkboard'): [
            Tab('training-choice', _('Course choice')),
        ],
        Tab('experience', _('Previous experience'), 'list-alt'): [
            Tab('education', _('Secondary studies')),
            Tab('curriculum', _('Curriculum')),
        ],
        Tab('additional-information', _('Additional information'), 'puzzle-piece'): [
            Tab('specific-questions', _('Specific aspects')),
        ],
        Tab('comments', pgettext('tab', 'Comments'), 'comments'): [
            Tab('comments', pgettext('tab', 'Comments'), 'comments')
        ],
        Tab('history', pgettext('tab', 'History'), 'history'): [
            Tab('history-all', _('All history')),
            Tab('history', _('Status changes')),
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

        # Add dynamic badge for comments
        if parent_tab == Tab('comments'):
            from admission.views.common.detail_tabs.comments import (
                COMMENT_TAG_FAC,
                COMMENT_TAG_GLOBAL,
                COMMENT_TAG_SIC,
            )

            roles = _get_roles_assigned_to_user(context['request'].user)
            qs = CommentEntry.objects.filter(object_uuid=context['view'].kwargs['uuid'])
            if {SicManagement, CentralManager} & set(roles):
                parent_tab.badge = qs.filter(tags__contains=[COMMENT_TAG_SIC, COMMENT_TAG_GLOBAL]).count()
            elif {ProgramManager} & set(roles):
                parent_tab.badge = qs.filter(tags__contains=[COMMENT_TAG_FAC, COMMENT_TAG_GLOBAL]).count()

        # Add icon when folder in quarantine
        if parent_tab == Tab('person') and getattr(permission_obj, 'candidate_id', None):
            demande_est_en_quarantaine = (
                PersonMergeProposal.objects.filter(
                    original_person_id=permission_obj.candidate_id,
                )
                .filter(Q(Q(status__in=PersonMergeStatus.quarantine_statuses()) | ~Q(validation__valid=True)))
                .exists()
            )
            if demande_est_en_quarantaine:
                parent_tab.icon_after = 'fas fa-warning text-warning'

        # Only add the parent tab if at least one sub tab is allowed
        if len(valid_sub_tabs) > 0:
            valid_tab_tree[parent_tab] = valid_sub_tabs

    return valid_tab_tree


@register.simple_tag(takes_context=True)
def default_tab_context(context):
    match = context['request'].resolver_match
    active_tab = match.url_name

    if 'curriculum' in match.namespaces:
        active_tab = 'curriculum'
    elif len(match.namespaces) > 2 and match.namespaces[2] != 'update':
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
        return CONTEXT_DOCTORATE
    elif isinstance(admission, GeneralEducationAdmission):
        return CONTEXT_GENERAL
    elif isinstance(admission, ContinuingEducationAdmission):
        return CONTEXT_CONTINUING


@register.inclusion_tag('admission/includes/subtabs_bar.html', takes_context=True)
def subtabs_bar(context):
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
                attrs = {action: False for action in ['pagination', 'zoom', 'comment', 'highlight', 'rotation']}
            return {
                'template': 'osis_document/editor.html',
                'value': document_write_token,
                'base_url': settings.OSIS_DOCUMENT_BASE_URL,
                'attrs': attrs,
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


@register.inclusion_tag('admission/includes/bootstrap_field_with_tooltip.html')
def bootstrap_field_with_tooltip(field, classes='', show_help=False, html_tooltip=False, label=None, label_class=''):
    return {
        'field': field,
        'classes': classes,
        'show_help': show_help,
        'html_tooltip': html_tooltip,
        'label': label,
        'label_class': label_class,
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
def get_last_inscription_date(year: Union[int, str, float]):
    """Return the academic year related to a specific year."""
    return datetime.date(year, 9, 30)


@register.filter(is_safe=False)
def default_if_none_or_empty(value, arg):
    """If value is None or empty, use given default."""
    return value if value not in EMPTY_VALUES else arg


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


@register.filter
def get_bound_field(form, field_name):
    """Returns the bound field of a form"""
    return form[field_name]


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
    return (
        current.get('statut') == state and part_of_dict(extra, current.get('extra', {})) if current and state else False
    )


@register.simple_tag
def has_value(iterable, values):
    return any(value in iterable for value in values)


@register.simple_tag
def interpolate(string, **kwargs):
    """Interpolate variables inside a string"""
    return string % kwargs


@register.simple_tag
def admission_url(admission_uuid: str, osis_education_type: str = '', admission_context: str = ''):
    """Get the base URL of a specific admission"""
    if not admission_context:
        admission_context = ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE.get(osis_education_type)
        if admission_context is None:
            return None
    return reverse(f'admission:{admission_context}', kwargs={'uuid': admission_uuid})


@register.simple_tag
def list_other_admissions_url(admission_uuid: str, osis_education_type: str):
    """Get the URL of the list view displaying the other admissions of a candidate of a specific admission"""
    admission_context = ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE.get(osis_education_type)
    if admission_context is None:
        return None
    return reverse(f'admission:{admission_context}:other-admissions-list', kwargs={'uuid': admission_uuid})


@register.simple_tag
def admission_status(status: str, osis_education_type: str):
    """Get the status of a specific admission"""
    admission_context = ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE.get(osis_education_type)

    if admission_context is None:
        return status

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
def country_name_from_iso_code(iso_code: str):
    """Return the country name from an iso code."""
    if not iso_code:
        return ''
    country = Country.objects.filter(iso_code=iso_code).values('name', 'name_en').first()
    if not country:
        return ''
    if get_language() == settings.LANGUAGE_CODE_FR:
        return country['name']
    return country['name_en']


@register.filter
def get_ordered_checklist_items_general_education(checklist_items: dict):
    """Return the ordered checklist items."""
    return sorted(checklist_items.items(), key=lambda tab: INDEX_ONGLETS_CHECKLIST_GENERALE[tab[0]])


@register.filter
def get_ordered_checklist_items_doctorate(checklist_items: dict):
    """Return the ordered checklist items."""
    return sorted(checklist_items.items(), key=lambda tab: INDEX_ONGLETS_CHECKLIST_DOCTORALE[tab[0]])


@register.filter
def get_ordered_checklist_items_continuing_education(checklist_items: dict):
    """Return the ordered checklist items."""
    return sorted(checklist_items.items(), key=lambda tab: INDEX_ONGLETS_CHECKLIST_CONTINUE[tab[0]])


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
        + f'<a class="btn btn-default btn-sm" href="{url}"><i class="fas fa-{"edit" if "update" in url else "eye"}">'
        f'</i></a>'
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
    title = gettext('Information provided to the candidate.')
    return mark_safe(
        f'{label} <i class="fas fa-user" data-content="{title}" data-toggle="popover" data-trigger="hover"></i>'
    )


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


@register.filter
def render_display_field_name(field_name: str, context: str = None) -> str:
    msg = field_name.replace('_', ' ').capitalize()
    return pgettext(context, msg) if context else _(msg)


@register.filter
def to_niss_format(s):
    return f"{s[:2]}.{s[2:4]}.{s[4:6]}-{s[6:9]}.{s[9:]}"


@register.filter
def map_fields_items(digit_fields):

    mapping = {
        "first_name": "firstName",
        "middle_name": "",
        "last_name": "lastName",
        "national_number": "nationalRegister",
        "sex": "gender",
        "birth_date": "birthDate",
        "email": "private_email",
        "civil_state": "",
        "birth_place": "placeOfBirth",
        "country_of_citizenship__name": "nationality",
        "id_card_number": "",
        "passport_number": "",
        "id_card_expiry_date": "",
        "passport_expiry_date": "",
    }

    mapped_fields = {}
    for admission_field, digit_field in mapping.items():
        mapped_fields[admission_field] = digit_fields.get('person').get(digit_field)

    mapped_fields['birth_date'] = datetime.datetime.strptime(mapped_fields['birth_date'], "%Y-%m-%d")

    if mapped_fields['country_of_citizenship__name']:
        mapped_fields['country_of_citizenship__name'] = Country.objects.get(
            iso_code=mapped_fields['country_of_citizenship__name']
        ).name

    return mapped_fields.items()


@register.inclusion_tag('admission/includes/input_field_data.html')
def input_field_data(label, value, editable=True, mask=None, select_key=None):
    if isinstance(value, datetime.date):
        value = value.strftime("%d/%m/%Y")
    if label == 'sex' and value is not None:
        select_key = value
        value = ChoixSexe.get_value(select_key)
    if label == 'civil_state' and value is not None:
        select_key = value
        value = CivilState.get_value(select_key)
    if 'country_of_citizenship' in label and value:
        select_key = Country.objects.get(name=value).id
    return {
        'label': label,
        'value': str(value) if value else None,
        'editable': editable,
        'mask': mask,
        'context': 'admission' if label == 'email' else None,
        'select_key': select_key,
    }


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
            'can_choose_access_title_tooltip': context.get('can_choose_access_title_tooltip'),
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
    if not value:
        return ''
    if value in SituationFinancabilite.get_names():
        return SituationFinancabilite[value].value
    return EtatFinancabilite[value].value


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
        EtudesSecondairesAdmissionDTO: 'bg-warning',
    }.get(experience.__class__, '')


@register.simple_tag(takes_context=True)
def experience_valuation_url(context, experience):
    base_namespace = context['view'].base_namespace
    admission_uuid = context['view'].kwargs.get('uuid', '')
    next_url_suffix = f'?next={context.get("request").path}&next_hash_url=parcours_anterieur__{experience.uuid}'

    if isinstance(experience, ExperienceAcademiqueDTO):
        return (
            resolve_url(
                f'{base_namespace}:update:curriculum:educational_valuate',
                uuid=admission_uuid,
                experience_uuid=experience.uuid,
            )
            + next_url_suffix
        )
    if isinstance(experience, ExperienceNonAcademiqueDTO):
        return (
            resolve_url(
                f'{base_namespace}:update:curriculum:non_educational_valuate',
                uuid=admission_uuid,
                experience_uuid=experience.uuid,
            )
            + next_url_suffix
        )
    return ''


@register.inclusion_tag('admission/includes/custom_base_template.html', takes_context=True)
def experience_details_template(
    context,
    resume_proposition: ResumePropositionDTO,
    experience,
    specific_questions: Dict[str, List[QuestionSpecifiqueDTO]] = None,
    with_edit_link_button=True,
    hide_files=True,
):
    """
    Return the template used to render the experience details.
    :param context: The template context
    :param resume_proposition: The proposition resume
    :param experience: The experience
    :param specific_questions: The specific questions related to the experience (only used for secondary studies)
    :param with_edit_link_button: Specify if the edit link button should be displayed
    :param hide_files: Specify if the files should be hidden
    :return: The rendered template
    """
    next_url_suffix = f'?next={context.get("request").path}&next_hash_url=parcours_anterieur__{experience.uuid}'
    delete_next_url_suffix = f'?next={context.get("request").path}&next_hash_url=parcours_anterieur'
    res_context = {
        'is_general': resume_proposition.est_proposition_generale,
        'is_continuing': resume_proposition.est_proposition_continue,
        'is_doctorate': resume_proposition.est_proposition_doctorale,
        'formation': resume_proposition.proposition.formation,
        'hide_files': hide_files,
        'checklist_display': True,
        'curex_link_button': '',
        'edit_link_button': '',
        'duplicate_link_button': '',
        'delete_link_button': '',
        'edit_link_button_in_new_tab': experience.epc_experience,
    }

    if with_edit_link_button:
        experience_urls = get_experience_urls(
            user=context['request'].user,
            admission=context['view'].admission,
            experience=experience,
            candidate_noma=context['view'].proposition.noma_candidat,
        )

        if experience_urls['curex_url']:
            res_context['curex_link_button'] = experience_urls['curex_url']

        elif experience_urls['edit_url']:
            res_context['edit_link_button'] = experience_urls['edit_url'] + next_url_suffix

        if experience_urls['delete_url']:
            res_context['delete_link_button'] = experience_urls['delete_url'] + delete_next_url_suffix

        if experience_urls['duplicate_url']:
            res_context['duplicate_link_button'] = experience_urls['duplicate_url'] + next_url_suffix

    if experience.__class__ == ExperienceAcademiqueDTO:
        res_context['custom_base_template'] = 'admission/exports/recap/includes/curriculum_educational_experience.html'
        res_context['title'] = _('Academic experience')
        res_context['with_single_header_buttons'] = True
        res_context.update(get_educational_experience_context(resume_proposition, experience))

    elif experience.__class__ == ExperienceNonAcademiqueDTO:
        res_context['custom_base_template'] = 'admission/exports/recap/includes/curriculum_professional_experience.html'
        res_context['title'] = _('Non-academic activity')
        res_context['with_single_header_buttons'] = True
        res_context.update(get_non_educational_experience_context(experience))

    elif experience.__class__ == EtudesSecondairesAdmissionDTO:
        res_context['custom_base_template'] = 'admission/exports/recap/includes/education.html'
        res_context['etudes_secondaires'] = experience
        res_context.update(
            get_secondary_studies_context(
                resume_proposition,
                specific_questions[Onglets.ETUDES_SECONDAIRES.name],
            )
        )

    return res_context


@register.simple_tag(takes_context=True)
def checklist_experience_action_links_context(
    context,
    experience: Union[
        ExperienceAcademiqueDTO,
        ExperienceNonAcademiqueDTO,
        EtudesSecondairesAdmissionDTO,
        ExperienceParcoursInterneDTO,
    ],
    current_year,
    prefix,
    parcours_tab_id='',
):
    next_url_suffix = f'?next={context["request"].path}&next_hash_url={parcours_tab_id}'
    proposition_uuid = context['view'].kwargs['uuid']

    result_context = {
        'prefix': prefix,
        'experience_uuid': str(experience.uuid),
        'edit_link_button_in_new_tab': getattr(experience, 'epc_experience', False),
        'update_url': '',
        'delete_url': '',
        'duplicate_url': '',
    }

    if isinstance(experience, (ExperienceParcoursInterneDTO, MessageCurriculumDTO)):
        return result_context

    elif (
        experience.__class__ == EtudesSecondairesAdmissionDTO
        or experience.valorisee_par_admissions
        and proposition_uuid in experience.valorisee_par_admissions
        and experience.derniere_annee == current_year
    ):
        experience_urls = get_experience_urls(
            user=context['request'].user,
            admission=context['view'].admission,
            experience=experience,
            candidate_noma=context['view'].proposition.noma_candidat,
        )

        if experience_urls['curex_url']:
            result_context['curex_url'] = experience_urls['curex_url']

        elif experience_urls['edit_url']:
            result_context['update_url'] = experience_urls['edit_url'] + next_url_suffix

        if experience_urls['delete_url']:
            result_context['delete_url'] = experience_urls['delete_url'] + next_url_suffix

        result_context['duplicate_url'] = experience_urls['duplicate_url']

    return result_context


@register.inclusion_tag(
    'admission/general_education/includes/checklist/parcours_row_actions_links.html',
    takes_context=True,
)
def checklist_experience_action_links(
    context,
    experience: Union[ExperienceAcademiqueDTO, ExperienceNonAcademiqueDTO, EtudesSecondairesAdmissionDTO],
    current_year,
    prefix,
    parcours_tab_id,
):
    return checklist_experience_action_links_context(context, experience, current_year, prefix, parcours_tab_id)


@register.simple_tag(takes_context=True)
def experience_urls(
    context,
    experience: Union[ExperienceAcademiqueDTO, ExperienceNonAcademiqueDTO, EtudesSecondairesAdmissionDTO],
):
    return get_experience_urls(
        user=context['request'].user,
        admission=context['view'].admission,
        experience=experience,
        candidate_noma=context['view'].proposition.noma_candidat,
    )


@register.filter
def display_academic_years_range(ac_years):
    ac_years = sorted(ac_years, key=lambda x: x.annee)
    return '{} - {}'.format(ac_years[0].annee, ac_years[-1].annee) if ac_years else "-"


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


@register.inclusion_tag('admission/exports/includes/refusal_footer_campus.html')
def refusal_footer_campus(campus: UclouvainCampusDTO):
    return {
        'campus': campus,
        'ORDERED_CAMPUSES_UUIDS': ORDERED_CAMPUSES_UUIDS,
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
def access_conditions_url(proposition: PropositionGeneraleDTO):
    training = BaseAdmission.objects.values(
        'training__education_group_type__name', 'training__acronym', 'training__partial_acronym'
    ).get(uuid=proposition.uuid)
    return get_access_conditions_url(
        training_type=training['training__education_group_type__name'],
        training_acronym=training['training__acronym'],
        partial_training_acronym=training['training__partial_acronym'],
    )


@register.filter
def format_matricule(matricule):
    prefix_fgs = (8 - len(matricule)) * '0'
    user_fgs = ''.join([prefix_fgs, matricule])
    return user_fgs


@register.filter
def format_ways_to_find_out_about_the_course(proposition: PropositionContinueDTO):
    """
    Format the list of ways to find out about the course of a proposition.
    :param proposition: The proposition
    :return: An unordered list of ways to find out about the course (including the "other" case, if any)
    """
    return unordered_list(
        [
            (
                ChoixMoyensDecouverteFormation.get_value(way)
                if way != ChoixMoyensDecouverteFormation.AUTRE.name
                else proposition.autre_moyen_decouverte_formation or ChoixMoyensDecouverteFormation.AUTRE.value
            )
            for way in proposition.moyens_decouverte_formation
        ]
    )


@register.simple_tag(takes_context=True)
def get_document_details_url(context, document: EmplacementDocumentDTO):
    """From a document, return the url to the document detail page."""
    match = context['request'].resolver_match
    base_url = resolve_url(
        f'{match.namespace}:document:detail',
        uuid=context['view'].kwargs['uuid'],
        identifier=document.identifiant,
    )

    query_params = {}

    if document.lecture_seule:
        query_params['read-only'] = '1'

    if document.requis_automatiquement:
        query_params['mandatory'] = '1'

    if query_params:
        return f'{base_url}?{urlencode(query_params)}'

    return base_url


@register.filter
def sport_affiliation_value(affiliation: Optional[str], campus_name: Optional[str]) -> str:
    """Return the label of the sport affiliation based on the affiliation value and the campus."""
    if not affiliation:
        return ''

    if not campus_name or affiliation != ChoixAffiliationSport.NON.name:
        return ChoixAffiliationSport.get_value(affiliation)

    return LABEL_AFFILIATION_SPORT_SI_NEGATIF_SELON_SITE.get(campus_name, ChoixAffiliationSport.NON.value)


@register.filter
def osis_language_name(code):
    if not code:
        return ''
    try:
        language = Language.objects.get(code=code)
    except Language.DoesNotExist:
        return code
    if get_language() == settings.LANGUAGE_CODE_FR:
        return language.name
    else:
        return language.name_en


@register.filter
def superior_institute_name(organization_uuid):
    if not organization_uuid:
        return ''
    institute = (
        get_superior_institute_queryset().filter(organization_uuid=organization_uuid).order_by('-start_date').first()
    )
    if not institute:
        return organization_uuid
    return mark_safe(format_school_title(institute))


@register.filter
def cotutelle_institute(admission: DoctorateAdmission):
    if admission.cotutelle_institution:
        institute = (
            get_superior_institute_queryset()
            .filter(organization_uuid=admission.cotutelle_institution)
            .order_by('-start_date')
            .first()
        )

        if institute:
            return '{institute_name} ({institute_address})'.format(
                institute_name=institute.name,
                institute_address=format_address(
                    street=institute.street,
                    street_number=institute.street_number,
                    postal_code=institute.zipcode,
                    city=institute.city,
                ),
            )

    elif admission.cotutelle_other_institution_name and admission.cotutelle_other_institution_address:
        return f'{admission.cotutelle_other_institution_name} ({admission.cotutelle_other_institution_address})'

    return ''


@register.simple_tag(takes_context=True)
def edit_external_member_form(context, membre):
    """Get an edit form"""
    initial = attr.asdict(membre)
    initial['pays'] = initial['code_pays']
    return DoctorateAdmissionMemberSupervisionForm(
        prefix=f"member-{membre.uuid}",
        initial=initial,
    )


@register.inclusion_tag('admission/includes/comment_form.html')
def htmx_comment_form(form, disabled=None):
    """
    Return the HTML form for a comment form whose content will be preserved after an htmx request.
    The input will be visually disabled if necessary (if specified by the param or if the form field is disabled).
    :param form: The comment form
    :param disabled: If True, visually disabled the comment input.
    """
    if disabled is None:
        disabled = form.fields['comment'].disabled

    # As the input content is preserved, we must be sure the input will be editable if necessary
    form.fields['comment'].disabled = False

    return {
        'form': form,
        'disabled': disabled,
    }
