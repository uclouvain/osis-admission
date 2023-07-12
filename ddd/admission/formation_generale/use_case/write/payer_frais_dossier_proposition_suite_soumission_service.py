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

from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.formation_generale.commands import PayerFraisDossierPropositionSuiteSoumissionCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.domain.service.i_notification import INotification
from admission.ddd.admission.formation_generale.domain.service.i_paiement_frais_dossier import IPaiementFraisDossier
from admission.ddd.admission.formation_generale.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def payer_frais_dossier_proposition_suite_soumission(
    cmd: 'PayerFraisDossierPropositionSuiteSoumissionCommand',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    notification: 'INotification',
    paiement_frais_dossier_service: 'IPaiementFraisDossier',
    historique: 'IHistorique',
    questions_specifiques_translator: 'IQuestionSpecifiqueTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    # WHEN
    paiement_frais_dossier_service.verifier_paiement_frais_dossier(
        proposition=proposition,
    )

    # THEN
    proposition.payer_frais_dossier()
    Checklist.initialiser(
        proposition=proposition,
        profil_candidat_translator=profil_candidat_translator,
        questions_specifiques_translator=questions_specifiques_translator,
        a_paye_frais_dossier=True,
    )
    proposition_repository.save(proposition)
    notification.confirmer_soumission(proposition)
    historique.historiser_paiement_frais_dossier_suite_soumission(proposition)

    return proposition_id
