# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid
from datetime import datetime, date
from typing import List, Optional

import attr

from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
)
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True, eq=False)
class EmplacementDocumentIdentity(interface.EntityIdentity):
    identifiant: str
    proposition_id: PropositionIdentity

    def __eq__(self, other):
        return self.identifiant == other.identifiant and self.proposition_id == other.proposition_id


@attr.dataclass(slots=True)
class EmplacementDocument(interface.Entity):
    entity_id: EmplacementDocumentIdentity
    uuids_documents: List[uuid.UUID]
    type: TypeEmplacementDocument
    statut: StatutEmplacementDocument
    justification_gestionnaire: str
    statut_reclamation: Optional[StatutReclamationEmplacementDocument] = None
    requis_automatiquement: bool = False
    libelle: str = ''
    reclame_le: Optional[datetime] = None
    a_echeance_le: Optional[date] = None
    derniere_action_le: Optional[datetime] = None
    dernier_acteur: str = ''
    document_soumis_par: str = ''

    def specifier_reclamation(self, raison: str, acteur: str, statut: str):
        self.justification_gestionnaire = raison
        self.derniere_action_le = datetime.now()
        self.statut = StatutEmplacementDocument.A_RECLAMER
        self.statut_reclamation = getattr(StatutReclamationEmplacementDocument, statut, None)
        self.dernier_acteur = acteur

    def reclamer_au_candidat(self, auteur: str, reclame_le: datetime, a_echeance_le: date):
        self.dernier_acteur = auteur
        self.a_echeance_le = a_echeance_le
        self.derniere_action_le = reclame_le
        self.reclame_le = reclame_le
        self.statut = StatutEmplacementDocument.RECLAME

    def annuler_reclamation_au_candidat(self, auteur: str, annule_le: datetime):
        self.dernier_acteur = auteur
        self.a_echeance_le = None
        self.derniere_action_le = annule_le
        self.reclame_le = None
        self.statut = StatutEmplacementDocument.RECLAMATION_ANNULEE

    def remplir_par_gestionnaire(self, uuid_document: str, auteur: str):
        if not uuid_document:
            return
        self.uuids_documents = [uuid_document]
        self.statut = StatutEmplacementDocument.VALIDE
        self.statut_reclamation = None
        self.document_soumis_par = auteur

    def remplir_par_candidat(self, uuid_documents, auteur: str, complete_le: datetime):
        self.dernier_acteur = auteur
        self.derniere_action_le = complete_le

        if uuid_documents:
            self.uuids_documents = uuid_documents
            self.statut = StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION
            self.statut_reclamation = None
            self.document_soumis_par = auteur
        else:
            self.statut = StatutEmplacementDocument.A_RECLAMER
