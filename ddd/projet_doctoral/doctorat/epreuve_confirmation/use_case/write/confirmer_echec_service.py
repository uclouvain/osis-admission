# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.projet_doctoral.doctorat.domain.model.doctorat import DoctoratIdentity
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.builder.epreuve_confirmation_identity import (
    EpreuveConfirmationIdentityBuilder,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import (
    ConfirmerEchecCommand,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.domain.service.i_notification import INotification
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.repository.i_epreuve_confirmation import (
    IEpreuveConfirmationRepository,
)
from admission.ddd.projet_doctoral.doctorat.repository.i_doctorat import IDoctoratRepository


def confirmer_echec(
    cmd: 'ConfirmerEchecCommand',
    epreuve_confirmation_repository: 'IEpreuveConfirmationRepository',
    doctorat_repository: 'IDoctoratRepository',
    notification: 'INotification',
) -> DoctoratIdentity:
    # GIVEN
    epreuve_confirmation_id = EpreuveConfirmationIdentityBuilder.build_from_uuid(cmd.uuid)
    epreuve_confirmation = epreuve_confirmation_repository.get(epreuve_confirmation_id)

    doctorat = doctorat_repository.get(epreuve_confirmation.doctorat_id)

    # WHEN
    epreuve_confirmation.verifier_pour_encodage_decision()
    doctorat.encoder_decision_echec_epreuve_confirmation()

    # THEN
    notification.notifier_echec_epreuve(epreuve_confirmation, cmd.sujet_message, cmd.corps_message)
    doctorat_repository.save(doctorat)

    return doctorat.entity_id
