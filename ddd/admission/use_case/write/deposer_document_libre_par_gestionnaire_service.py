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

from admission.ddd.admission.commands import DeposerDocumentLibreParGestionnaireCommand
from admission.ddd.admission.domain.builder.document_builder import DocumentBuilder
from admission.ddd.admission.enums.document import StatutDocument
from admission.ddd.admission.repository.i_document import IDocumentRepository


def deposer_document_libre_par_gestionnaire(
    cmd: 'DeposerDocumentLibreParGestionnaireCommand',
    document_repository: 'IDocumentRepository',
) -> str:
    document = DocumentBuilder().initier_document(
        statut_document=StatutDocument.VALIDE.name,
        uuid_proposition=cmd.uuid_proposition,
        auteur=cmd.auteur,
        token_document=cmd.token_document,
        type_document=cmd.type_document,
        nom_document=cmd.nom_document,
    )

    document_repository.save_document_gestionnaire(document)

    return document.entity_id.identifiant
