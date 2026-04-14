##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

import attr

from admission.ddd.admission.shared_kernel.enums.comptabilite import (
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    LienParente,
    TypeSituationAssimilation,
)
from base.models.utils.utils import ChoiceEnum
from osis_common.ddd import interface


@attr.dataclass(slots=True)
class Assimilation(interface.ValueObject):
    class Source(ChoiceEnum):
        OSIS = 'OSIS'
        EPC = 'EPC'

    source: Source

    type_situation_assimilation: TypeSituationAssimilation

    sous_type_situation_assimilation_1: Optional[ChoixAssimilation1] = None
    sous_type_situation_assimilation_2: Optional[ChoixAssimilation2] = None
    sous_type_situation_assimilation_3: Optional[ChoixAssimilation3] = None
    relation_parente: Optional[LienParente] = None
    sous_type_situation_assimilation_5: Optional[ChoixAssimilation5] = None
    sous_type_situation_assimilation_6: Optional[ChoixAssimilation6] = None
