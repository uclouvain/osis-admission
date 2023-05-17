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

from admission.ddd.admission.domain.builder.emplacement_document_identity_builder import (
    EmplacementDocumentIdentityBuilder,
)
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import TypeEmplacementDocument, StatutEmplacementDocument
from osis_common.ddd import interface
from osis_common.ddd.interface import CommandRequest


class EmplacementDocumentBuilder(interface.RootEntityBuilder):
    @classmethod
    def build_from_command(cls, cmd: 'CommandRequest') -> 'EmplacementDocument':
        raise NotImplementedError

    @classmethod
    def build_from_repository_dto(cls, dto_object: 'EmplacementDocumentDTO') -> 'EmplacementDocument':
        raise NotImplementedError

    @classmethod
    def initialiser_emplacement_document_libre(
        cls,
        uuid_proposition: str,
        auteur: str,
        type_emplacement: str,
        libelle: str,
        raison: str = '',
    ) -> 'EmplacementDocument':
        heure_initialisation = datetime.datetime.now()
        return EmplacementDocument(
            entity_id=EmplacementDocumentIdentityBuilder.build_libre(
                type_emplacement=type_emplacement,
                uuid_proposition=uuid_proposition,
            ),
            libelle=libelle,
            uuids_documents=[],
            dernier_acteur=auteur,
            type=TypeEmplacementDocument[type_emplacement],
            statut=StatutEmplacementDocument.A_RECLAMER,
            justification_gestionnaire=raison,
            derniere_action_le=heure_initialisation,
        )

    @classmethod
    def initialiser_emplacement_document_a_reclamer(
        cls,
        identifiant_emplacement: str,
        uuid_proposition: str,
        auteur: str,
        raison: str,
    ) -> 'EmplacementDocument':
        heure_initialisation = datetime.datetime.now()
        return EmplacementDocument(
            entity_id=EmplacementDocumentIdentityBuilder.build_non_libre(
                identifiant_emplacement=identifiant_emplacement,
                uuid_proposition=uuid_proposition,
            ),
            uuids_documents=[],
            dernier_acteur=auteur,
            type=TypeEmplacementDocument.NON_LIBRE,
            statut=StatutEmplacementDocument.A_RECLAMER,
            justification_gestionnaire=raison,
            derniere_action_le=heure_initialisation,
            requis_automatiquement=True,
        )
