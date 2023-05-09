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
from admission.ddd.admission.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.commands import ReclamerDocumentsAuCandidatParSICCommand
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_notification import INotification
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository


def reclamer_documents_au_candidat_par_sic(
    cmd: 'ReclamerDocumentsAuCandidatParSICCommand',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
    proposition_repository: 'IPropositionRepository',
    notification: 'INotification',
    historique: 'IHistorique',
) -> PropositionIdentity:
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_demande))

    documents_reclamables = emplacement_document_repository.get_documents_reclamables_proposition(
        proposition=proposition,
    )

    emplacement_document_repository.reclamer_documents_au_candidat(
        identifiants_documents_reclames=cmd.identifiants_documents,
        documents_reclamables=documents_reclamables,
        auteur=cmd.auteur,
        a_echeance_le=cmd.a_echeance_le,
    )

    proposition.reclamer_documents_par_sic(documents_demandes=documents_reclamables)

    proposition_repository.save(proposition)
    notification.demande_complements(
        proposition=proposition,
        objet_message=cmd.objet_message,
        corps_message=cmd.corps_message,
    )
    historique.historiser_demande_complements_sic(proposition=proposition, acteur=cmd.auteur)

    return proposition.entity_id
