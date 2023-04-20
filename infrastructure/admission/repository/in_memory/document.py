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

from admission.ddd.admission.domain.model.document import Document, DocumentIdentity
from admission.ddd.admission.repository.i_document import IDocumentRepository
from osis_common.ddd.interface import EntityIdentity, ApplicationService


class DocumentInMemoryRepository(IDocumentRepository):
    entities: List[Document] = []

    @classmethod
    def reset(cls):
        cls.entities = []

    @classmethod
    def search(cls, entity_ids: Optional[List[DocumentIdentity]] = None, **kwargs) -> List[Document]:
        return [entity for entity in cls.entities if entity.entity_id in entity_ids]

    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        for entity in cls.entities:
            if entity.entity_id == entity_id:
                cls.entities.remove(entity)
                break

    @classmethod
    def save_document_gestionnaire(cls, document: Document) -> None:
        cls.entities.append(document)

    @classmethod
    def get(cls, entity_id: DocumentIdentity) -> Document:
        return next(entity for entity in cls.entities if entity.entity_id == entity_id)
