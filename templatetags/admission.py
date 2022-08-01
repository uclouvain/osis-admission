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
import re
from dataclasses import dataclass
from functools import wraps
from inspect import getfullargspec

from django import template
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _
from rules.templatetags import rules

from admission.auth.constants import READ_ACTIONS_BY_TAB, UPDATE_ACTIONS_BY_TAB
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import (
    CategorieActivite,
    ChoixTypeEpreuve,
    StatutActivite,
)
from admission.utils import get_cached_admission_perm_obj
from osis_role.templatetags.osis_role import has_perm

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
            ret.append(reduce_list_separated(ret.pop(), next(iterargs, None)))
        elif nextarg in ["-", ':']:
            ret.append(reduce_list_separated(ret.pop(), next(iterargs, None), separator=f" {nextarg} "))
        elif isinstance(nextarg, str) and len(nextarg) > 1 and re.match(r'\s', nextarg[0]):
            suffixed_val = ret.pop()
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
def panel(context, title='', title_level=4, additional_class='', **kwargs):
    """
    Template tag for panel
    :param title: the panel title
    :param title_level: the title level
    :param additional_class: css class to add
    :type context: django.template.context.RequestContext
    """
    context['title'] = title
    context['title_level'] = title_level
    context['additional_class'] = additional_class
    context['attributes'] = {k.replace('_', '-'): v for k, v in kwargs.items()}
    return context


@register.inclusion_tag('admission/includes/sortable_header_div.html', takes_context=True)
def sortable_header_div(context, order_field_name, order_field_label):
    # Ascending sorting by default
    asc_ordering = True
    ordering_class = 'sort'

    query_order_param = context.request.GET.get('o')

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

    new_params = context.request.GET.copy()
    new_params['o'] = '{}{}'.format('' if asc_ordering else '-', order_field_name)
    new_params.pop('page', None)
    return {
        'field_label': order_field_label,
        'url': context.request.path + '?' + new_params.urlencode(),
        'ordering_class': ordering_class,
    }


# Manage the tabs
@dataclass(frozen=True)
class Tab:
    name: str
    label: str
    icon: str = ''
    badge: str = ''

    def __hash__(self):
        # Only hash the name, as lazy strings have different memory addresses
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name


MESSAGE_TAB = Tab('messages', _('Send a mail'), 'envelope')
INTERNAL_NOTE_TAB = Tab('internal-note', _('Internal notes'), 'note-sticky')

TAB_TREES = {
    'doctorate': {
        Tab('personal', _('Personal data'), 'user'): [
            Tab('person', _('Identification')),
            Tab('coordonnees', _('Contact details')),
        ],
        Tab('experience', _('Previous experience'), 'list-alt'): [
            Tab('education', _('Secondary studies')),
            Tab('curriculum', _('Curriculum')),
            Tab('languages', _('Languages knowledge')),
        ],
        Tab('doctorate', _('Doctorate'), 'graduation-cap'): [
            Tab('project', _('Doctoral project')),
            Tab('cotutelle', _('Cotutelle')),
            Tab('supervision', _('Supervision')),
            Tab('confirmation', _('Confirmation paper')),
            Tab('extension-request', _('New deadline')),
            Tab('training', _('Training')),
        ],
        Tab('history', _('History'), 'clock'): [
            Tab('history', _('Status changes')),
            Tab('history-all', _('All history')),
        ],
        MESSAGE_TAB: [
            Tab('send-mail', _('Send a mail')),
        ],
        INTERNAL_NOTE_TAB: [
            INTERNAL_NOTE_TAB,
        ],
    },
}

PARENT_TAB_BY_CHILD_TAB = {}
for tree in TAB_TREES:
    PARENT_TAB_BY_CHILD_TAB[tree] = {
        child.name: parent for parent, children in TAB_TREES[tree].items() for child in children
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
    for (parent_tab, sub_tabs) in tab_tree.items():
        # Get the accessible sub tabs depending on the user permissions
        valid_sub_tabs = [tab for tab in sub_tabs if can_read_tab(context, tab.name, permission_obj)]
        # Only add the parent tab if at least one sub tab is allowed
        if len(valid_sub_tabs) > 0:
            valid_tab_tree[parent_tab] = valid_sub_tabs

    # Add dynamic badges
    sub_tabs_internal_notes = valid_tab_tree.pop(INTERNAL_NOTE_TAB, None)
    if sub_tabs_internal_notes:
        valid_tab_tree[
            Tab(
                name=INTERNAL_NOTE_TAB.name,
                label=INTERNAL_NOTE_TAB.label,
                icon=INTERNAL_NOTE_TAB.icon,
                badge=permission_obj.internalnote_set.count(),
            )
        ] = sub_tabs_internal_notes

    return valid_tab_tree


@register.simple_tag(takes_context=True)
def default_tab_context(context):
    match = context['request'].resolver_match
    active_tab = match.url_name

    if len(match.namespaces) > 2 and match.namespaces[2] != 'update':
        active_tab = match.namespaces[2]

    active_parent = PARENT_TAB_BY_CHILD_TAB['doctorate'][active_tab]

    return {
        'active_parent': active_parent,
        'active_tab': active_tab,
        'admission_uuid': context['view'].kwargs.get('uuid', ''),
        'namespace': ':'.join(match.namespaces[:2]),
        'request': context['request'],
        'view': context['view'],
    }


@register.inclusion_tag('admission/includes/doctorate_tabs_bar.html', takes_context=True)
def doctorate_tabs_bar(context):
    tab_context = default_tab_context(context)
    admission = get_cached_admission_perm_obj(tab_context['admission_uuid'])
    current_tab_tree = get_valid_tab_tree(context, admission, TAB_TREES['doctorate']).copy()

    # Prevent showing message tab when candidate is not enrolled
    if admission.post_enrolment_status == ChoixStatutDoctorat.ADMISSION_IN_PROGRESS.name:
        current_tab_tree.pop(MESSAGE_TAB, None)

    tab_context['tab_tree'] = current_tab_tree
    return tab_context


@register.simple_tag(takes_context=True)
def current_subtabs(context):
    tab_context = default_tab_context(context)
    permission_obj = context['view'].get_permission_object()
    tab_context['subtabs'] = [
        tab
        for tab in TAB_TREES['doctorate'][tab_context['active_parent']]
        if can_read_tab(context, tab.name, permission_obj)
    ]
    return tab_context


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


@register.inclusion_tag('admission/includes/field_data.html')
def field_data(name, data=None, css_class=None, hide_empty=False, translate_data=False, inline=False, html_tag=''):
    if isinstance(data, list):
        if data:
            template_string = "{% load osis_document %}{% document_visualizer files %}"
            template_context = {'files': data}
            data = template.Template(template_string).render(template.Context(template_context))
        else:
            data = ''
    elif translate_data is True:
        data = _(data)

    if inline is True:
        name = _("%(label)s:") % {'label': name}
        css_class = (css_class + ' inline-field-data') if css_class else 'inline-field-data'

    return {
        'name': name,
        'data': data,
        'css_class': css_class,
        'hide_empty': hide_empty,
        'html_tag': html_tag,
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
def bootstrap_field_with_tooltip(field, classes='', show_help=False):
    return {
        'field': field,
        'classes': classes,
        'show_help': show_help,
    }


@register.simple_tag(takes_context=True)
def has_perm(context, perm, obj=None):
    if not obj:
        obj = context['view'].get_permission_object()
    return rules.has_perm(perm, context['request'].user, obj)


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
        _("Participation"): [0, 0],
        _("Scientific communication"): [0, 0],
        _("Publication"): [0, 0],
        _("Courses and training"): [0, 0],
        _("Services"): [0, 0],
        _("VAE"): [0, 0],
        _("Scientific residencies"): [0, 0],
        _("Confirmation paper"): [0, 0],
        _("Thesis defences"): [0, 0],
    }
    for activity in activities:
        index = int(activity.status == StatutActivite.ACCEPTEE.name)
        if activity.status != StatutActivite.REFUSEE.name:
            added += activity.ects
        if activity.status not in [StatutActivite.SOUMISE.name, StatutActivite.ACCEPTEE.name]:
            continue
        if activity.status == StatutActivite.ACCEPTEE.name:
            validated += activity.ects
        elif (
            activity.category == CategorieActivite.CONFERENCE.name
            or activity.category == CategorieActivite.SEMINAR.name
        ):
            categories[_("Participation")][index] += activity.ects
        elif activity.category == CategorieActivite.COMMUNICATION.name and (
            activity.parent_id is None or activity.parent.category == CategorieActivite.CONFERENCE.name
        ):
            categories[_("Scientific communication")][index] += activity.ects
        elif activity.category == CategorieActivite.PUBLICATION.name and (
            activity.parent_id is None or activity.parent.category == CategorieActivite.CONFERENCE.name
        ):
            categories[_("Publication")][index] += activity.ects
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
        elif activity.category == CategorieActivite.COURSE.name:
            categories[_("Courses and training")][index] += activity.ects
        elif (
            activity.category == CategorieActivite.PAPER.name
            and activity.type == ChoixTypeEpreuve.CONFIRMATION_PAPER.name
        ):
            categories[_("Confirmation paper")][index] += activity.ects
        elif activity.category == CategorieActivite.PAPER.name:
            categories[_("Thesis defences")][index] += activity.ects
    if not any(cat_added + cat_validated for cat_added, cat_validated in categories.values()):
        return {}
    return {
        'categories': categories,
        'added': added,
        'validated': validated,
    }
