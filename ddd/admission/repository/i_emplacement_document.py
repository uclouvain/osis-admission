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
from abc import ABCMeta
from typing import List

from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument, EmplacementDocumentIdentity
from admission.ddd.admission.domain.model.demande import DemandeIdentity
from admission.ddd.admission.enums.emplacement_document import TypeDocument
from osis_common.ddd import interface


class IEmplacementDocumentRepository(interface.AbstractRepository, metaclass=ABCMeta):
    @classmethod
    def get_document_admission(
        cls,
        proposition_identity: DemandeIdentity,
        entity_id: EmplacementDocumentIdentity,
    ) -> EmplacementDocument:
        raise NotImplementedError

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
