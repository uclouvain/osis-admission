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
from admission.ddd.admission.domain.builder.emplacement_document_identity_builder import (
    EmplacementDocumentIdentityBuilder,
)
from admission.ddd.admission.domain.service.i_historique import IHistorique
from admission.ddd.admission.domain.validator.validator_by_business_action import (
    DocumentsDemandesCompletesValidatorList,
)
from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument
from admission.ddd.admission.formation_generale.commands import CompleterEmplacementsDocumentsParCandidatCommand
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository


def completer_emplacements_documents_par_candidat(
    cmd: 'CompleterEmplacementsDocumentsParCandidatCommand',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    identifiants_documents_demandes = EmplacementDocumentIdentityBuilder.build_list(
        list(proposition.documents_demandes.keys()),
        cmd.uuid_proposition,
    )

    documents_reclames = emplacement_document_repository.search(
        entity_ids=identifiants_documents_demandes,
        statut=StatutEmplacementDocument.RECLAME,
    )

    # WHEN
    DocumentsDemandesCompletesValidatorList(
        documents_reclames=documents_reclames,
        reponses_documents_a_completer=cmd.reponses_documents_a_completer,
    ).validate()

    emplacement_document_repository.completer_documents_par_candidat(
        documents_completes=documents_reclames,
        reponses_documents_a_completer=cmd.reponses_documents_a_completer,
        auteur=proposition.matricule_candidat,
    )
    proposition.completer_documents_par_candidat()

    # THEN
    proposition_repository.save(proposition)
    emplacement_document_repository.save_multiple(entities=documents_reclames, auteur=proposition.matricule_candidat)
    historique.historiser_completion_documents_par_candidat(proposition=proposition)

    return proposition.entity_id
