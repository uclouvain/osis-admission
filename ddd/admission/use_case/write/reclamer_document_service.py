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

from admission.ddd.admission.commands import ReclamerDocumentCommand
from admission.ddd.admission.domain.builder.document_builder import DocumentBuilder
from admission.ddd.admission.enums.emplacement_document import StatutDocument
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository


def reclamer_document(
    cmd: 'ReclamerDocumentCommand',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
) -> str:
    document = DocumentBuilder().initier_document(
        statut_document=StatutDocument.A_RECLAMER.name,
        uuid_demande=cmd.uuid_demande,
        auteur=cmd.auteur,
        nom_document='',
        identifiant_document=cmd.identifiant_document,
        type_document=cmd.type_document,
    )

    document.definir_a_reclamer(raison=cmd.raison)

    emplacement_document_repository.save_emplacement_document_candidat(entity=document)

    return document.entity_id.identifiant
