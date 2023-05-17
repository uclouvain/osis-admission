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
from admission.ddd.admission.commands import InitialiserEmplacementDocumentAReclamerCommand
from admission.ddd.admission.domain.builder.emplacement_document_builder import EmplacementDocumentBuilder
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository


def initialiser_emplacement_document_a_reclamer(
    cmd: 'InitialiserEmplacementDocumentAReclamerCommand',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
) -> EmplacementDocumentIdentity:
    emplacement_document = EmplacementDocumentBuilder().initialiser_emplacement_document_a_reclamer(
        uuid_proposition=cmd.uuid_proposition,
        auteur=cmd.auteur,
        identifiant_emplacement=cmd.identifiant_emplacement,
        raison=cmd.raison,
    )

    emplacement_document_repository.save(entity=emplacement_document, auteur=cmd.auteur)

    return emplacement_document.entity_id
