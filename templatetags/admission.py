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

from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import StatutActivite
from admission.utils import get_cached_admission_perm_obj

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
        elif nextarg == "-":
            ret.append(reduce_list_separated(ret.pop(), next(iterargs, None), separator=" - "))
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

    def __hash__(self):
        # Only hash the name, as lazy strings have different memory addresses
        return hash(self.name)


MESSAGE_TAB = Tab('messages', _('Send a mail'), 'envelope')
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
    },
}


def get_active_parent(tab_tree, tab_name):
    return next(
        (parent for parent, children in tab_tree.items() if any(child.name == tab_name for child in children)),
        None,
    )


@register.inclusion_tag('admission/includes/doctorate_tabs_bar.html', takes_context=True)
def doctorate_tabs_bar(context):
    match = context['request'].resolver_match

    current_tab_name = match.url_name
    if len(match.namespaces) > 2:
        current_tab_name = match.namespaces[2]

    current_tab_tree = TAB_TREES[match.namespaces[1]].copy()
    admission = get_cached_admission_perm_obj(context['view'].kwargs.get('pk', ''))

    # Prevent showing message tab when candidate is not enrolled
    # TODO switch to a perm-based selection of the tabs
    if admission.post_enrolment_status == ChoixStatutDoctorat.ADMISSION_IN_PROGRESS.name:
        del current_tab_tree[MESSAGE_TAB]

    parent = get_active_parent(current_tab_tree, current_tab_name)

    return {
        'tab_tree': current_tab_tree,
        'active_parent': parent,
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'namespace': match.namespace,
        'request': context['request'],
        'view': context['view'],
    }


@register.simple_tag(takes_context=True)
def current_subtabs(context):
    # TODO switch to a perm-based selection of the subtabs, and hide parent tab if no tabs
    match = context['request'].resolver_match
    current_tab_name = match.url_name
    if len(match.namespaces) > 2 and match.namespaces[2] != 'update':
        current_tab_name = match.namespaces[2]
    current_tab_tree = TAB_TREES[match.namespaces[1]]
    return current_tab_tree.get(get_active_parent(current_tab_tree, current_tab_name), [])


@register.inclusion_tag('admission/includes/doctorate_subtabs_bar.html', takes_context=True)
def doctorate_subtabs_bar(context, tabs=None):
    match = context['request'].resolver_match
    current_tab_name = match.url_name
    if len(match.namespaces) > 2 and match.namespaces[2] != 'update':
        current_tab_name = match.namespaces[2]

    return {
        'subtabs': tabs if tabs is not None else current_subtabs(context),
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'namespace': ':'.join(match.namespaces[:2]),
        'request': context['request'],
        'view': context['view'],
        'active_tab': current_tab_name,
    }


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
def field_data(name, data=None, css_class=None, hide_empty=False, translate_data=False, inline=False):
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
def status_as_class(activity):
    return {
        StatutActivite.SOUMISE.name: "warning",
        StatutActivite.ACCEPTEE.name: "success",
        StatutActivite.REFUSEE.name: "danger",
    }.get(activity.status, 'default')
