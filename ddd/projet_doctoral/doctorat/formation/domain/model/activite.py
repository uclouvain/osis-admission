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
from typing import Optional

import attr

from admission.ddd.projet_doctoral.doctorat.domain.model.doctorat import DoctoratIdentity
from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import CategorieActivite, StatutActivite
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class ActiviteIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class Activite(interface.RootEntity):
    entity_id: 'ActiviteIdentity'
    doctorat_id: 'DoctoratIdentity'
    categorie: 'CategorieActivite'
    statut: 'StatutActivite' = StatutActivite.NON_SOUMISE
    ects: Optional[float] = None
    parent_id: Optional['ActiviteIdentity'] = None
    categorie_parente: Optional['CategorieActivite'] = None

    def soumettre(self):
        self.statut = StatutActivite.SOUMISE

    def accepter(self):
        self.statut = StatutActivite.ACCEPTEE

    def refuser(self):
        self.statut = StatutActivite.REFUSEE
