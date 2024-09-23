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
    RefuserPropositionParFaculteCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import INotification
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator


def refuser_proposition_par_faculte(
    cmd: RefuserPropositionParFaculteCommand,
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
    personne_connue_ucl_translator: 'IPersonneConnueUclTranslator',
    notification: 'INotification',
) -> PropositionIdentity:
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    proposition.refuser_par_fac(auteur_modification=cmd.gestionnaire)

    # THEN
    gestionnaire_dto = personne_connue_ucl_translator.get(cmd.gestionnaire)

    proposition_repository.save(entity=proposition)

    message = notification.envoyer_message_libre_au_candidat(
        proposition=proposition,
        objet_message=cmd.objet_message,
        corps_message=cmd.corps_message,
        matricule_emetteur=cmd.gestionnaire,
        cc_promoteurs=True,
        cc_membres_ca=True,
    )

    historique.historiser_refus_fac(
        proposition=proposition,
        gestionnaire=gestionnaire_dto,
        message=message,
    )

    return proposition.entity_id
