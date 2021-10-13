##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from typing import Optional

import attr
from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum
from osis_common.ddd import interface


class ChoixDoctoratDejaRealise(ChoiceEnum):
    YES = _('YES')
    NO = _('NO')
    PARTIAL = _('PARTIAL')


@attr.s(frozen=True, slots=True)
class ExperiencePrecedenteRecherche(interface.ValueObject):
    doctorat_deja_realise = attr.ib(type=ChoixDoctoratDejaRealise, default=ChoixDoctoratDejaRealise.NO)
    institution = attr.ib(type=Optional[str], default='')
    date_soutenance = attr.ib(type=Optional[datetime.date], default=None)
    raison_non_soutenue = attr.ib(type=Optional[str], default='')


aucune_experience_precedente_recherche = ExperiencePrecedenteRecherche(
    doctorat_deja_realise=ChoixDoctoratDejaRealise.NO,
)
