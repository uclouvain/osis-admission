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

from admission.ddd.admission.commands import InitialiserEmplacementDocumentLibreAReclamerCommand
from admission.ddd.admission.domain.builder.emplacement_document_builder import EmplacementDocumentBuilder
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository


def initialiser_emplacement_document_libre_a_reclamer(
    cmd: 'InitialiserEmplacementDocumentLibreAReclamerCommand',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
) -> EmplacementDocumentIdentity:
    emplacement_document = EmplacementDocumentBuilder().initialiser_emplacement_document_libre(
        uuid_proposition=cmd.uuid_proposition,
        auteur=cmd.auteur,
        type_emplacement=cmd.type_emplacement,
        libelle=cmd.libelle,
        raison=cmd.raison,
    )

    emplacement_document.remplir_par_gestionnaire(uuid_document=cmd.uuid_document, auteur=cmd.auteur)

    emplacement_document_repository.save(entity=emplacement_document, auteur=cmd.auteur)

    return emplacement_document.entity_id
