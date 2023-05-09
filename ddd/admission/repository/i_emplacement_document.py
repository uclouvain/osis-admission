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
import datetime
from abc import ABCMeta
from typing import List

from admission.ddd.admission.domain.model.demande import DemandeIdentity
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument, EmplacementDocumentIdentity
from admission.ddd.admission.enums.emplacement_document import TypeDocument
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from osis_common.ddd import interface


class IEmplacementDocumentRepository(interface.AbstractRepository, metaclass=ABCMeta):
    @classmethod
    def get_documents_reclamables_proposition(
        cls,
        proposition: Proposition,
    ) -> List[EmplacementDocument]:
        raise NotImplementedError

    @classmethod
    def reclamer_documents_au_candidat(
        cls,
        identifiants_documents_reclames: List[str],
        documents_reclamables: List[EmplacementDocument],
        auteur: str,
        a_echeance_le: datetime.date,
    ):
        heure = datetime.datetime.now()
        for document in documents_reclamables:
            if document.entity_id.identifiant in identifiants_documents_reclames:
                document.reclamer_au_candidat(
                    auteur=auteur,
                    a_echeance_le=a_echeance_le,
                    reclame_le=heure,
                )

    @classmethod
    def save_emplacement_document_gestionnaire(cls, entity: EmplacementDocument) -> None:
        raise NotImplementedError

    @classmethod
    def save_emplacement_document_candidat(cls, entity: EmplacementDocument) -> None:
        raise NotImplementedError

    @classmethod
    def save(cls, entity: EmplacementDocument) -> None:
        raise NotImplementedError

    @classmethod
    def delete_emplacement_candidat(
        cls,
        entity_id: EmplacementDocumentIdentity,
        demande_entity_id: DemandeIdentity,
        type_document: TypeDocument,
    ) -> None:
        raise NotImplementedError

    @classmethod
    def save_multiple_emplacements_documents_candidat(cls, entities: List[EmplacementDocument]) -> None:
        raise NotImplementedError

    @classmethod
    def reinitialiser_emplacements_documents_candidat(
        cls,
        demande_identity: DemandeIdentity,
        entities: List[EmplacementDocument],
    ) -> None:
        raise NotImplementedError
