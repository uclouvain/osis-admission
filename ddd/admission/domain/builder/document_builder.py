# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime

from admission.ddd.admission.domain.builder.document_identity_builder import DocumentIdentityBuilder
from admission.ddd.admission.domain.model.document import Document, DocumentIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.dtos.document import DocumentDTO
from admission.ddd.admission.enums.document import TypeDocument, StatutDocument, OngletsDemande
from osis_common.ddd import interface
from osis_common.ddd.interface import CommandRequest


class DocumentBuilder(interface.RootEntityBuilder):
    @classmethod
    def build_from_command(cls, cmd: 'CommandRequest') -> 'Document':
        pass

    @classmethod
    def build_from_repository_dto(cls, dto_object: 'DocumentDTO') -> 'Document':
        return Document(
            entity_id=DocumentIdentity(identifiant=dto_object.identifiant),
            proposition=PropositionIdentity(uuid=dto_object.uuid_proposition),
            libelle=dto_object.libelle,
            onglet=OngletsDemande[dto_object.onglet],
            uuids=dto_object.uuids,
            auteur=dto_object.auteur,
            type=TypeDocument[dto_object.type],
            statut=StatutDocument[dto_object.statut],
            justification_gestionnaire=dto_object.justification_gestionnaire,
            soumis_le=dto_object.soumis_le,
            reclame_le=dto_object.reclame_le,
            a_echeance_le=dto_object.a_echeance_le,
            derniere_action_le=dto_object.derniere_action_le,
        )

    @classmethod
    def initier_document(
        cls,
        uuid_proposition: str,
        auteur: str,
        token_document: str,
        type_document: str,
        nom_document: str,
        statut_document: str,
        identifiant_document: str = '',
        identifiant_question_specifique: str = '',
    ) -> 'Document':
        heure_initiation = datetime.datetime.now()
        return Document(
            entity_id=DocumentIdentityBuilder.build(
                type_document=TypeDocument[type_document],
                identifiant_document=identifiant_document,
                token_document=token_document,
                identifiant_question_specifique=identifiant_question_specifique,
            ),
            proposition=PropositionIdentity(uuid=uuid_proposition),
            libelle=nom_document,
            uuids=[token_document],
            auteur=auteur,
            type=TypeDocument[type_document],
            statut=StatutDocument[statut_document],
            justification_gestionnaire='',
            soumis_le=heure_initiation if token_document else None,
            reclame_le=None,
            a_echeance_le=None,
            onglet=OngletsDemande.DOCUMENTS_ADDITIONNELS,
            derniere_action_le=heure_initiation,
        )
