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
from typing import Optional, List

from admission.ddd.admission.domain.model.demande import DemandeIdentity
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument, EmplacementDocumentIdentity
from admission.ddd.admission.enums.emplacement_document import TypeDocument
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository
from osis_common.ddd.interface import EntityIdentity, ApplicationService


class EmplacementDocumentInMemoryRepository(IEmplacementDocumentRepository):
    entities: List[EmplacementDocument] = []

    @classmethod
    def reset(cls):
        cls.entities = []

    @classmethod
    def search(
        cls, entity_ids: Optional[List[EmplacementDocumentIdentity]] = None, **kwargs
    ) -> List[EmplacementDocument]:
        return [entity for entity in cls.entities if entity.entity_id in entity_ids]

    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        for entity in cls.entities:
            if entity.entity_id == entity_id:
                cls.entities.remove(entity)
                break

    @classmethod
    def save_emplacement_document_gestionnaire(cls, document: EmplacementDocument) -> None:
        cls.save(document)

    @classmethod
    def save_emplacement_document_candidat(cls, document: EmplacementDocument) -> None:
        cls.save(document)

    @classmethod
    def save(cls, document: EmplacementDocument) -> None:
        cls.entities.append(document)

    @classmethod
    def save_multiple_emplacements_documents_candidat(cls, entities: List[EmplacementDocument]) -> None:
        for entity in entities:
            cls.save(entity)

    @classmethod
    def reinitialiser_emplacements_documents_candidat(
        cls,
        demande_identity: DemandeIdentity,
        entities: List[EmplacementDocument],
    ) -> None:
        cls.entities = [
            entity
            for entity in cls.entities
            if entity.demande != demande_identity
            or entity.type
            in {
                TypeDocument.CANDIDAT_SIC,
                TypeDocument.CANDIDAT_FAC,
            }
        ]
        cls.save_multiple_emplacements_documents_candidat(entities)
