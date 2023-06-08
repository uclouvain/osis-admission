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

from typing import Dict

from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition as PropositionGenerale
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionPourPaiementInvalideException,
    PropositionDoitEtreEnAttenteDePaiementException,
    StatutPropositionInvalidePourPaiementInscriptionException,
    PaiementNonRealiseException,
)
from osis_common.ddd import interface


class IPaiementFraisDossier(interface.DomainService):
    @classmethod
    def paiement_realise(cls, proposition_uuid: str) -> bool:
        raise NotImplementedError

    @classmethod
    def doit_payer(cls, elements_confirmation: Dict[str, str]) -> bool:
        return 'frais_dossier' in elements_confirmation

    @classmethod
    def verifier_paiement_frais_dossier(cls, proposition: PropositionGenerale) -> None:
        if not proposition.statut == ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE:
            raise PropositionPourPaiementInvalideException

        if not cls.paiement_realise(proposition_uuid=proposition.entity_id.uuid):
            raise PaiementNonRealiseException

    @classmethod
    def verifier_paiement_necessaire_par_gestionnaire(cls, proposition: PropositionGenerale) -> None:
        if (
            not proposition.statut == ChoixStatutPropositionGenerale.CONFIRMEE
            or proposition.checklist_initiale.frais_dossier.statut == ChoixStatutChecklist.SYST_REUSSITE
            or proposition.checklist_actuelle.frais_dossier.statut == ChoixStatutChecklist.SYST_REUSSITE
        ):
            raise StatutPropositionInvalidePourPaiementInscriptionException(proposition.statut.value)

    @classmethod
    def verifier_proposition_en_attente_paiement_suite_demande_gestionnaire(
        cls,
        proposition: PropositionGenerale,
    ) -> None:
        if (
            not proposition.statut == ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE
            or proposition.checklist_initiale.frais_dossier.statut == ChoixStatutChecklist.SYST_REUSSITE
            or proposition.checklist_actuelle.frais_dossier.statut != ChoixStatutChecklist.GEST_BLOCAGE
        ):
            raise PropositionDoitEtreEnAttenteDePaiementException

    @classmethod
    def verifier_paiement_non_realise(cls, proposition: PropositionGenerale) -> None:
        if (
            proposition.checklist_initiale.frais_dossier.statut == ChoixStatutChecklist.SYST_REUSSITE
            or proposition.checklist_actuelle.frais_dossier.statut == ChoixStatutChecklist.SYST_REUSSITE
        ):
            raise PropositionPourPaiementInvalideException
