# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from typing import Iterable

from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from base.models.utils.utils import ChoiceEnum


def not_in_statuses_predicate_message(statuses: Iterable[str], status_enum_class: type(ChoiceEnum)):
    """
    From a set of statuses, join the lazy translation representation of each status
    :param statuses: The set of statuses
    :param status_enum_class: The class of an enumeration (inheriting from ChoiceEnum)
    :return: The lazy translation representation of the statuses
    """
    strings = [
        _('The global status of the application must be one of the following in order to realize this action: '),
    ]

    for index, status in enumerate(statuses):
        if index > 0:
            strings.append(', ')

        strings.append(status_enum_class[status].value)

    strings.append('.')

    return format_lazy('{}' * len(strings), *strings)


def not_in_general_statuses_predicate_message(statuses: Iterable[str]):
    return not_in_statuses_predicate_message(statuses, ChoixStatutPropositionGenerale)


def not_in_continuing_statuses_predicate_message(statuses: Iterable[str]):
    return not_in_statuses_predicate_message(statuses, ChoixStatutPropositionContinue)


def not_in_doctorate_statuses_predicate_message(statuses: Iterable[str]):
    return not_in_statuses_predicate_message(statuses, ChoixStatutPropositionDoctorale)
