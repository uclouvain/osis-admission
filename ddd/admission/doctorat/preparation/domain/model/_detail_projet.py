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
from typing import List, Optional

import attr

from admission.ddd.admission.doctorat.preparation.domain.model._institut import InstitutIdentity
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixLangueRedactionThese
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class DetailProjet(interface.ValueObject):
    titre: str = ''
    resume: str = ''
    langue_redaction_these: ChoixLangueRedactionThese = ChoixLangueRedactionThese.UNDECIDED
    institut_these: Optional[InstitutIdentity] = None
    lieu_these: str = ''
    documents: List[str] = attr.Factory(list)
    graphe_gantt: List[str] = attr.Factory(list)
    proposition_programme_doctoral: List[str] = attr.Factory(list)
    projet_formation_complementaire: List[str] = attr.Factory(list)
    lettres_recommandation: List[str] = attr.Factory(list)


projet_non_rempli = DetailProjet()
