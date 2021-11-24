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
from typing import List

import attr
import uuid

from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum
from osis_common.ddd import interface


class ChoixLangueRedactionThese(ChoiceEnum):
    FRENCH = _('French')
    ENGLISH = _('English')
    OTHER = _('Other')
    UNDECIDED = _('Undecided')


@attr.s(frozen=True, slots=True)
class DetailProjet(interface.ValueObject):
    titre = attr.ib(type=str, default='')
    resume = attr.ib(type=str, default='')
    langue_redaction_these = attr.ib(type=ChoixLangueRedactionThese, default=ChoixLangueRedactionThese.UNDECIDED)
    institut_these = attr.ib(type=str, default='')
    lieu_these = attr.ib(type=str, default='')
    documents = attr.ib(type=List[uuid.UUID], factory=list)
    graphe_gantt = attr.ib(type=List[uuid.UUID], factory=list)
    proposition_programme_doctoral = attr.ib(type=List[uuid.UUID], factory=list)
    projet_formation_complementaire = attr.ib(type=List[uuid.UUID], factory=list)
    lettres_recommandation = attr.ib(type=List[uuid.UUID], factory=list)


projet_non_rempli = DetailProjet()
