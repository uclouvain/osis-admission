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
from email.message import EmailMessage

from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique


class HistoriqueInMemory(IHistorique):
    @classmethod
    def historiser_paiement_frais_dossier_suite_soumission(cls, proposition: Proposition):
        pass

    @classmethod
    def historiser_paiement_frais_dossier_suite_demande_gestionnaire(cls, proposition: Proposition):
        pass

    @classmethod
    def historiser_demande_paiement_par_gestionnaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
        rappel: bool = False,
    ):
        pass

    @classmethod
    def historiser_annulation_demande_paiement_par_gestionnaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_initial: ChoixStatutPropositionGenerale,
    ):
        pass
