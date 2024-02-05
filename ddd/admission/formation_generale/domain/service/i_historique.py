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
from abc import abstractmethod
from email.message import EmailMessage
from typing import Optional

from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from osis_common.ddd import interface


class IHistorique(interface.DomainService):
    @classmethod
    @abstractmethod
    def historiser_paiement_frais_dossier_suite_soumission(cls, proposition: Proposition):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_paiement_frais_dossier_suite_demande_gestionnaire(cls, proposition: Proposition):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_demande_paiement_par_gestionnaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
        rappel: bool = False,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_annulation_demande_paiement_par_gestionnaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_initial: ChoixStatutPropositionGenerale,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_envoi_fac_par_sic_lors_de_la_decision_facultaire(
        cls,
        proposition: Proposition,
        message: EmailMessage,
        gestionnaire: str,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_envoi_sic_par_fac_lors_de_la_decision_facultaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        envoi_par_fac: bool,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_refus_fac(cls, proposition: Proposition, gestionnaire: PersonneConnueUclDTO):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_acceptation_fac(cls, proposition: Proposition, gestionnaire: PersonneConnueUclDTO):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_refus_sic(cls, proposition: Proposition, message: EmailMessage, gestionnaire: str):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_acceptation_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: Optional[EmailMessage] = None,
    ):
        raise NotImplementedError

    @classmethod
    def historiser_modification_authentification_experience_parcours(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        etat_authentification: str,
        message: Optional[EmailMessage],
        uuid_experience: str,
    ):
        historize_method = {
            EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name: (
                cls.historiser_demande_verification_titre_acces
            ),
            EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name: (
                cls.historiser_information_candidat_verification_parcours_en_cours
            ),
        }.get(etat_authentification)

        if historize_method:
            historize_method(
                proposition=proposition,
                gestionnaire=gestionnaire,
                message=message,
                uuid_experience=uuid_experience,
            )

    @classmethod
    @abstractmethod
    def historiser_demande_verification_titre_acces(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
        uuid_experience: str,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_information_candidat_verification_parcours_en_cours(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
        uuid_experience: str,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_specification_motifs_refus_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_original: ChoixStatutPropositionGenerale,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_specification_informations_acceptation_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_original: ChoixStatutPropositionGenerale,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_specification_motifs_refus_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_original: ChoixStatutPropositionGenerale,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def historiser_specification_informations_acceptation_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_original: ChoixStatutPropositionGenerale,
    ):
        raise NotImplementedError
