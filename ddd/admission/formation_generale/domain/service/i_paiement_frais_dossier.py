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
import datetime
from datetime import timedelta
from typing import Dict, List

from admission.ddd.admission.domain.model.periode import Periode
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
    STATUTS_PROPOSITION_GENERALE_GESTIONNAIRE_PEUT_DEMANDER_PAIEMENT,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition as PropositionGenerale
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionPourPaiementInvalideException,
    PropositionDoitEtreEnAttenteDePaiementException,
    StatutPropositionInvalidePourPaiementInscriptionException,
    PaiementNonRealiseException,
    PaiementDejaRealiseException, DateLimitePaiementDepasseeException,
)
from admission.ddd.admission.formation_generale.dtos.paiement import PaiementDTO
from osis_common.ddd import interface


class IPaiementFraisDossier(interface.DomainService):
    @classmethod
    def paiement_realise(cls, proposition_uuid: str) -> bool:
        raise NotImplementedError

    @classmethod
    def recuperer_paiements_proposition(cls, proposition_uuid: str) -> List[PaiementDTO]:
        raise NotImplementedError

    @classmethod
    def doit_payer(cls, elements_confirmation: Dict[str, str]) -> bool:
        return 'frais_dossier' in elements_confirmation

    @classmethod
    def ouvrir_paiement(cls, proposition_uuid: str) -> PaiementDTO:
        raise NotImplementedError

    @classmethod
    def verifier_paiement_frais_dossier(cls, proposition: PropositionGenerale) -> None:
        if not proposition.statut == ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE:
            raise PropositionPourPaiementInvalideException

        if not cls.paiement_realise(proposition_uuid=proposition.entity_id.uuid):
            raise PaiementNonRealiseException

    @classmethod
    def verifier_paiement_frais_dossier_necessaire(
        cls,
        proposition: PropositionGenerale,
        periode_hue_plus_5_resident_etranger: Periode,
    ) -> None:
        if not proposition.statut == ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE:
            raise PropositionPourPaiementInvalideException

        if cls.paiement_realise(proposition_uuid=proposition.entity_id.uuid):
            raise PaiementDejaRealiseException
        aujourdhui = datetime.date.today()
        date_limite = periode_hue_plus_5_resident_etranger.date_fin + timedelta(days=14)
        if aujourdhui >= date_limite:
            raise DateLimitePaiementDepasseeException(date_limite=date_limite)

    @classmethod
    def verifier_paiement_necessaire_par_gestionnaire(cls, proposition: PropositionGenerale) -> None:
        if (
            proposition.statut.name not in STATUTS_PROPOSITION_GENERALE_GESTIONNAIRE_PEUT_DEMANDER_PAIEMENT
            or proposition.checklist_initiale.frais_dossier.statut == ChoixStatutChecklist.SYST_REUSSITE
            or proposition.checklist_actuelle.frais_dossier.statut == ChoixStatutChecklist.SYST_REUSSITE
        ):
            raise StatutPropositionInvalidePourPaiementInscriptionException(proposition.statut.value)

        if cls.paiement_realise(proposition_uuid=proposition.entity_id.uuid):
            raise PaiementDejaRealiseException

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

        if cls.paiement_realise(proposition_uuid=proposition.entity_id.uuid):
            raise PaiementDejaRealiseException
