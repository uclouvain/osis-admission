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
from dataclasses import dataclass

from django import template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

register = template.Library()


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


TAB_TREES = {
    'doctorate': {
        'cdd': {
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
            ],
        },
    },
}


def get_active_parent(tab_tree, tab_name):
    return next(
        (parent for parent, children in tab_tree.items() if any(child.name == tab_name for child in children)),
        None,
    )


@register.inclusion_tag('admission/includes/tabs_bar.html', takes_context=True)
def doctorate_tabs(context):
    match = context['request'].resolver_match

    namespaces = match.namespaces

    current_tab_tree = TAB_TREES[namespaces[1]][namespaces[2]]
    parent = get_active_parent(current_tab_tree, match.url_name)

    return {
        'tab_tree': current_tab_tree,
        'active_parent': parent,
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'namespace': match.namespace,
        'request': context['request'],
        'view': context['view'],
    }


@register.inclusion_tag('admission/includes/subtabs_bar.html', takes_context=True)
def doctorate_subtabs(context):
    match = context['request'].resolver_match

    namespaces = match.namespaces

    current_tab_tree = TAB_TREES[namespaces[1]][namespaces[2]]

    return {
        'subtabs': current_tab_tree.get(get_active_parent(current_tab_tree, match.url_name), []),
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'namespace': match.namespace,
        'request': context['request'],
        'view': context['view'],
    }


@register.simple_tag(takes_context=True)
def update_tab_path_from_detail(context, admission_uuid):
    """From a detail page, get the path of the update page."""
    match = context['request'].resolver_match
    return reverse(
        '{}:update:{}'.format(match.namespace, match.url_name),
        args=[admission_uuid],
    )


@register.simple_tag(takes_context=True)
def detail_tab_path_from_update(context, admission_uuid):
    """From an update page, get the path of the detail page."""
    match = context['request'].resolver_match
    return reverse(
        '{}:{}'.format(':'.join(match.namespaces[:-1]), match.url_name),
        args=[admission_uuid],
    )
