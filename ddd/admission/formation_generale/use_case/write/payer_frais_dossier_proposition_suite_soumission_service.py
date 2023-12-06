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
from admission.ddd import MONTANT_FRAIS_DOSSIER
from admission.ddd.admission.formation_generale.commands import PayerFraisDossierPropositionSuiteSoumissionCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.domain.service.i_notification import INotification
from admission.ddd.admission.formation_generale.domain.service.i_paiement_frais_dossier import IPaiementFraisDossier
from admission.ddd.admission.formation_generale.events import FraisDossierPayeEvent
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.repository.i_proposition import formater_reference


def payer_frais_dossier_proposition_suite_soumission(
    message_bus: 'MessageBus',
    cmd: 'PayerFraisDossierPropositionSuiteSoumissionCommand',
    proposition_repository: 'IPropositionRepository',
    notification: 'INotification',
    paiement_frais_dossier_service: 'IPaiementFraisDossier',
    historique: 'IHistorique',
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
    proposition_repository.save(proposition)
    notification.confirmer_soumission(proposition)
    historique.historiser_paiement_frais_dossier_suite_soumission(proposition)

    message_bus.publish(
        FraisDossierPayeEvent(
            entity_id=proposition_id,
            numero_dossier=formater_reference(
                reference=proposition.reference,
                nom_campus_inscription='TEST',  # formation.campus_inscription   # TODO: Add translator to get formation
                sigle_entite_gestion='TEST',  # formation.sigle_entite_gestion # TODO: Add translator to get formation
                annee=proposition.formation_id.annee,
            ),
            montant=MONTANT_FRAIS_DOSSIER,
            matricule=proposition.matricule_candidat,
        )
    )
    return proposition_id
