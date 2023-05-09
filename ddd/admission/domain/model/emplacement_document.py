# ##############################################################################
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
# ##############################################################################
from datetime import datetime, date
from typing import List, Optional

import attr

from admission.ddd.admission.domain.model.demande import DemandeIdentity
from admission.ddd.admission.enums.emplacement_document import TypeDocument, StatutDocument, OngletsDemande
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class EmplacementDocumentIdentity(interface.EntityIdentity):
    identifiant: str


@attr.dataclass(slots=True)
class EmplacementDocument(interface.Entity):
    entity_id: EmplacementDocumentIdentity
    demande: DemandeIdentity
    libelle: str
    libelle_langue_candidat: str
    onglet: OngletsDemande
    uuids: List[str]
    auteur: str
    type: TypeDocument
    statut: StatutDocument
    justification_gestionnaire: str
    soumis_le: Optional[datetime] = None
    reclame_le: Optional[datetime] = None
    a_echeance_le: Optional[date] = None
    derniere_action_le: Optional[datetime] = None

    def definir_a_reclamer(self, raison: str, auteur: str):
        self.justification_gestionnaire = raison
        self.derniere_action_le = datetime.now()
        self.statut = StatutDocument.A_RECLAMER
        self.auteur = auteur

    def reclamer_au_candidat(
        self,
        auteur: str,
        a_echeance_le: date,
        reclame_le: datetime,
    ):
        self.auteur = auteur
        self.a_echeance_le = a_echeance_le
        self.derniere_action_le = reclame_le
        self.reclame_le = reclame_le
        self.statut = StatutDocument.RECLAME

    def get_infos_a_sauvegarder(self):
        return {
            'author': self.auteur,
            'reason': self.justification_gestionnaire,
            'type': self.type.name,
            'last_action_at': self.derniere_action_le,
            'status': self.statut.name,
            'requested_at': self.reclame_le,
            'deadline_at': self.a_echeance_le,
        }
