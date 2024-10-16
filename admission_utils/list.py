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


def list_to_dict_with_prev_and_next_elements(list_to_process, id_attribute: str = ''):
    """
    From a list of elements, return a dictionary containing for each element, the previous and the next elements.
    :param list_to_process: The input list.
    :param id_attribute: The attribute identifying the objects. If specified, the related values will be stored.
    :return: The output dictionary as {current_value: {previous: previous_value, next: next_value}}
    """
    get_id_method = (lambda elt: getattr(elt, id_attribute)) if id_attribute else (lambda elt: elt)
    dict_result = {}
    prev_elt = None

    for current in list_to_process:
        id_value = get_id_method(current)
        dict_result[id_value] = {
            'previous': prev_elt,
            'next': None,
        }

        if prev_elt:
            dict_result[prev_elt]['next'] = id_value
        prev_elt = id_value

    return dict_result
