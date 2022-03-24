##############################################################################
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
##############################################################################
from typing import Optional

from django import template

from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixStatutProposition
from admission.ddd.projet_doctoral.preparation.domain.model._financement import ChoixTypeFinancement
from admission.ddd.projet_doctoral.validation.domain.model._enums import ChoixStatutCDD, ChoixStatutSIC
from base.models.utils.utils import ChoiceEnum

register = template.Library()


@register.filter
def get_enum_value(enum: ChoiceEnum, key: Optional[str]):
    return enum.get_value(key) if key else ''


# Enums
TEMPLATE_ENUMS = {
    val.__name__: val for val in [
        ChoixStatutProposition,
        ChoixStatutCDD,
        ChoixStatutSIC,
        ChoixTypeFinancement,
    ]
}


@register.filter
def enum_display(value: Optional[str], enum_name: str):
    if isinstance(value, str):
        enum = TEMPLATE_ENUMS.get(enum_name)
        if enum:
            return enum.get_value(value)
    return value or ''
