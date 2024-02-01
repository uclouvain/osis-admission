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
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.commands import (
    RefuserAdmissionParSicCommand,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.domain.service.i_pdf_generation import IPDFGeneration
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def refuser_admission_par_sic(
    cmd: RefuserAdmissionParSicCommand,
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
    notification: 'INotification',
    pdf_generation: 'IPDFGeneration',
) -> PropositionIdentity:
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    proposition.refuser_par_sic(auteur_modification=cmd.auteur)

    # THEN
    pdf_generation.generer_attestation_refus_sic(
        proposition_repository=proposition_repository,
        proposition=proposition,
        gestionnaire=cmd.auteur,
    )

    proposition_repository.save(entity=proposition)

    message = notification.refuser_proposition_par_sic(
        proposition=proposition,
        objet_message=cmd.objet_message,
        corps_message=cmd.corps_message,
    )
    historique.historiser_refus_sic(
        proposition=proposition,
        message=message,
        gestionnaire=cmd.auteur,
    )

    return proposition.entity_id
