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
from admission.ddd.admission.commands import AnnulerReclamationDocumentCommand
from admission.ddd.admission.domain.model.demande import DemandeIdentity
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity
from admission.ddd.admission.enums.emplacement_document import TypeDocument
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository


def annuler_reclamation_document(
    cmd: 'AnnulerReclamationDocumentCommand',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
) -> EmplacementDocumentIdentity:
    emplacement_document_entity_id = EmplacementDocumentIdentity(identifiant=cmd.identifiant_document)
    demande_entity_id = DemandeIdentity(uuid=cmd.uuid_demande)

    emplacement_document_repository.delete_emplacement_candidat(
        entity_id=emplacement_document_entity_id,
        demande_entity_id=demande_entity_id,
        type_document=TypeDocument[cmd.type_document],
    )

    return emplacement_document_entity_id
