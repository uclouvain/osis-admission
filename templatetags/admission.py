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
from django import template

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
