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
from datetime import date
from typing import List, Optional

import attr

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixTypeFinancement
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class Financement(interface.ValueObject):
    type: Optional[ChoixTypeFinancement]
    type_contrat_travail: Optional[str] = ''
    eft: Optional[int] = None
    bourse_recherche: Optional[str] = ''
    bourse_date_debut: Optional[date] = None
    bourse_date_fin: Optional[date] = None
    bourse_preuve: List[str] = attr.Factory(list)
    duree_prevue: Optional[int] = None
    temps_consacre: Optional[int] = None


financement_non_rempli = Financement(type=None)
