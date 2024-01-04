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

from email.message import EmailMessage

from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from osis_common.ddd import interface


class IHistorique(interface.DomainService):
    @classmethod
    def historiser_paiement_frais_dossier_suite_soumission(cls, proposition: Proposition):
        raise NotImplementedError

    @classmethod
    def historiser_paiement_frais_dossier_suite_demande_gestionnaire(cls, proposition: Proposition):
        raise NotImplementedError

    @classmethod
    def historiser_demande_paiement_par_gestionnaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
        rappel: bool = False,
    ):
        raise NotImplementedError

    @classmethod
    def historiser_annulation_demande_paiement_par_gestionnaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_initial: ChoixStatutPropositionGenerale,
    ):
        raise NotImplementedError

    @classmethod
    def historiser_paiement(cls, proposition: Proposition):
        raise NotImplementedError

    @classmethod
    def historiser_envoi_fac_par_sic_lors_de_la_decision_facultaire(
        cls,
        proposition: Proposition,
        message: EmailMessage,
        gestionnaire: str,
    ):
        raise NotImplementedError

    @classmethod
    def historiser_envoi_sic_par_fac_lors_de_la_decision_facultaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        envoi_par_fac: bool,
    ):
        raise NotImplementedError

    @classmethod
    def historiser_refus_fac(cls, proposition: Proposition, gestionnaire: str):
        raise NotImplementedError

    @classmethod
    def historiser_acceptation_fac(cls, proposition: Proposition, gestionnaire: str):
        raise NotImplementedError
