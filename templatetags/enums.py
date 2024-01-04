##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from django import template
from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum, ChoiceEnumWithAcronym

register = template.Library()


@register.filter
def enum_display(value, enum_name):
    if isinstance(value, str):
        for enum in ChoiceEnum.__subclasses__():
            if enum.__name__ == enum_name:
                return enum.get_value(value)
    return value or ''


@register.filter
def enum_with_acronym_display(value, enum_name):
    if isinstance(value, str):
        for enum in ChoiceEnumWithAcronym.__subclasses__():
            if enum.__name__ == enum_name:
                if hasattr(enum, value):
                    return getattr(enum, value, value).label
                break
    return value or ''


@register.filter
def format_is_online(value):
    return _("Online") if value else _("In person")
