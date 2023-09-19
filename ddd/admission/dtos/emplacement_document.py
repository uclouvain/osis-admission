##############################################################################
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
##############################################################################
import datetime
from typing import Optional, List, Dict

import attr

from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    DocumentsSystemeFAC,
    EMPLACEMENTS_DOCUMENTS_RECLAMABLES,
)
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class EmplacementDocumentDTO(interface.Entity):
    identifiant: str
    libelle: str
    libelle_langue_candidat: str
    document_uuids: List[str]
    type: str
    statut: str
    justification_gestionnaire: str
    document_soumis_par: Optional[PersonneConnueUclDTO]
    document_soumis_le: Optional[datetime.datetime]
    reclame_le: Optional[datetime.datetime]
    dernier_acteur: Optional[PersonneConnueUclDTO]
    derniere_action_le: Optional[datetime.datetime]
    a_echeance_le: Optional[datetime.datetime]
    onglet: str
    nom_onglet: str
    nom_onglet_langue_candidat: str
    uuid_proposition: str
    requis_automatiquement: bool
    types_documents: Dict[str, str]
    noms_documents_televerses: Dict[str, str]

    def est_emplacement_systeme_fac(self):
        return (
            self.type == TypeEmplacementDocument.SYSTEME.name and self.identifiant.split('.')[-1] in DocumentsSystemeFAC
        )

    @property
    def est_reclamable(self):
        return self.type in EMPLACEMENTS_DOCUMENTS_RECLAMABLES
