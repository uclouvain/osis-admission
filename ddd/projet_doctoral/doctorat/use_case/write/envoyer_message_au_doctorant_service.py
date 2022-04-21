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

from admission.ddd.projet_doctoral.doctorat.builder.doctorat_identity import DoctoratIdentityBuilder
from admission.ddd.projet_doctoral.doctorat.commands import EnvoyerMessageDoctorantCommand
from admission.ddd.projet_doctoral.doctorat.domain.model.doctorat import DoctoratIdentity
from admission.ddd.projet_doctoral.doctorat.domain.service.i_historique import IHistorique
from admission.ddd.projet_doctoral.doctorat.domain.service.i_notification import INotification
from admission.ddd.projet_doctoral.doctorat.repository.i_doctorat import IDoctoratRepository


def envoyer_message_au_doctorant(
    cmd: 'EnvoyerMessageDoctorantCommand',
    doctorat_repository: 'IDoctoratRepository',
    notification: 'INotification',
    historique: 'IHistorique',
) -> 'DoctoratIdentity':
    # GIVEN
    doctorat_identity = DoctoratIdentityBuilder.build_from_uuid(cmd.doctorat_uuid)
    doctorat = doctorat_repository.get(entity_id=doctorat_identity)

    # THEN
    message = notification.envoyer_message(
        doctorat,
        cmd.matricule_emetteur,
        doctorat.matricule_doctorant,
        cmd.sujet,
        cmd.message,
        cmd.cc_promoteurs,
        cmd.cc_membres_ca,
    )
    historique.historiser_message_au_doctorant(doctorat, cmd.matricule_emetteur, message)

    return doctorat_identity
