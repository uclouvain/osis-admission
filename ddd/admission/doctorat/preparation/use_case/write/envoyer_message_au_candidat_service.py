# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.doctorat.preparation.commands import EnvoyerMessageCandidatCommand
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import INotification
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.domain.model.proposition import PropositionIdentity


def envoyer_message_au_candidat(
    cmd: 'EnvoyerMessageCandidatCommand',
    proposition_repository: 'IPropositionRepository',
    notification: 'INotification',
    historique: 'IHistorique',
) -> 'PropositionIdentity':
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.proposition_uuid))

    # THEN
    message = notification.envoyer_message_libre_au_candidat(
        proposition=proposition,
        objet_message=cmd.sujet,
        corps_message=cmd.message,
        matricule_emetteur=cmd.matricule_emetteur,
        cc_promoteurs=cmd.cc_promoteurs,
        cc_membres_ca=cmd.cc_membres_ca,
    )

    historique.historiser_message_au_candidat(proposition, cmd.matricule_emetteur, message)

    return proposition.entity_id
