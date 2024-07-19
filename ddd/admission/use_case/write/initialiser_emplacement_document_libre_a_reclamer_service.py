# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Union, Type

from admission.ddd.admission.commands import InitialiserEmplacementDocumentLibreAReclamerCommand
from admission.ddd.admission.doctorat.preparation.domain.model.enums import OngletsChecklist as OngletsChecklistDoctorat
from admission.ddd.admission.domain.builder.emplacement_document_builder import EmplacementDocumentBuilder
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity
from admission.ddd.admission.formation_continue.domain.model.enums import OngletsChecklist as OngletsChecklistContinue
from admission.ddd.admission.formation_generale.domain.model.enums import OngletsChecklist as OngletsChecklistGenerale
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository


def initialiser_emplacement_document_libre_a_reclamer(
    cmd: 'InitialiserEmplacementDocumentLibreAReclamerCommand',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
    classe_enumeration_onglets_checklist: Union[
        Type[OngletsChecklistContinue],
        Type[OngletsChecklistGenerale],
        Type[OngletsChecklistDoctorat],
    ],
) -> EmplacementDocumentIdentity:
    emplacement_document = EmplacementDocumentBuilder().initialiser_emplacement_document_libre(
        uuid_proposition=cmd.uuid_proposition,
        auteur=cmd.auteur,
        type_emplacement=cmd.type_emplacement,
        libelle=cmd.libelle_fr,
        libelle_fr=cmd.libelle_fr,
        libelle_en=cmd.libelle_en,
        raison=cmd.raison,
        statut_reclamation=cmd.statut_reclamation,
        onglet_checklist_associe=getattr(classe_enumeration_onglets_checklist, cmd.onglet_checklist_associe)
        if cmd.onglet_checklist_associe
        else None,
    )

    emplacement_document.remplir_par_gestionnaire(uuid_document=cmd.uuid_document, auteur=cmd.auteur)

    emplacement_document_repository.save(entity=emplacement_document, auteur=cmd.auteur)

    return emplacement_document.entity_id
