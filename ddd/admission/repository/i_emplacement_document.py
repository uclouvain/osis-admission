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
from typing import List, Optional, Dict

from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument, EmplacementDocumentIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument
from osis_common.ddd import interface


class IEmplacementDocumentRepository(interface.AbstractRepository, metaclass=ABCMeta):
    @classmethod
    def reclamer_documents_au_candidat(
        cls,
        documents_reclames: List[EmplacementDocument],
        auteur: str,
        a_echeance_le: datetime.date,
    ):
        heure = datetime.datetime.now()
        for document in documents_reclames:
            document.reclamer_au_candidat(
                auteur=auteur,
                a_echeance_le=a_echeance_le,
                reclame_le=heure,
            )

    @classmethod
    def annuler_reclamation_documents_au_candidat(
        cls,
        documents_reclames: List[EmplacementDocument],
        auteur: str,
    ):
        heure = datetime.datetime.now()
        for document in documents_reclames:
            document.annuler_reclamation_au_candidat(
                auteur=auteur,
                annule_le=heure,
            )

    @classmethod
    def completer_documents_par_candidat(
        cls,
        documents_completes: List[EmplacementDocument],
        reponses_documents_a_completer: Dict[str, List[str]],
        auteur: str,
    ):
        heure = datetime.datetime.now()
        for document in documents_completes:
            document.remplir_par_candidat(
                uuid_documents=reponses_documents_a_completer.get(document.entity_id.identifiant),
                auteur=auteur,
                complete_le=heure,
            )

    @classmethod
    def get(cls, entity_id: EmplacementDocumentIdentity) -> EmplacementDocument:
        raise NotImplementedError

    @classmethod
    def search(
        cls,
        entity_ids: Optional[List[EmplacementDocumentIdentity]] = None,
        statut: Optional[StatutEmplacementDocument] = None,
        **kwargs,
    ) -> List[EmplacementDocument]:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: EmplacementDocumentIdentity, auteur='', supprimer_donnees=False, **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    def save(cls, entity: EmplacementDocument, auteur='') -> None:
        raise NotImplementedError

    @classmethod
    def save_multiple(cls, entities: List[EmplacementDocument], auteur='') -> None:
        raise NotImplementedError

    @classmethod
    def reinitialiser_emplacements_documents_non_libres(
        cls,
        proposition_identity: PropositionIdentity,
        entities: List[EmplacementDocument],
    ) -> None:
        raise NotImplementedError
