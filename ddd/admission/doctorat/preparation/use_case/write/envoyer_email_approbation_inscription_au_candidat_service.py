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

from admission.ddd.admission.doctorat.preparation.commands import (
    EnvoyerEmailApprobationInscriptionAuCandidatCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import INotification
from admission.ddd.admission.repository.i_digit import IDigitRepository


def envoyer_email_approbation_inscription_au_candidat(
    cmd: EnvoyerEmailApprobationInscriptionAuCandidatCommand,
    historique: 'IHistorique',
    notification: 'INotification',
    digit_repository: 'IDigitRepository',
):
    message = notification.accepter_proposition_par_sic(
        proposition_uuid=cmd.uuid_proposition,
        objet_message=cmd.objet_message,
        corps_message=cmd.corps_message,
        digit_repository=digit_repository,
    )
    historique.historiser_mail_acceptation_inscription_sic(
        proposition_uuid=cmd.uuid_proposition,
        message=message,
        gestionnaire=cmd.auteur,
    )
