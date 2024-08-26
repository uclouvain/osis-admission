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
from abc import abstractmethod
from email.message import EmailMessage
from typing import List, Optional

from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument
from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from admission.ddd.admission.repository.i_digit import IDigitRepository
from admission.ddd.admission.shared_kernel.email_destinataire.repository.i_email_destinataire import (
    IEmailDestinataireRepository,
)
from osis_common.ddd import interface


class INotification(interface.DomainService):
    @classmethod
    @abstractmethod
    def confirmer_soumission(cls, proposition: Proposition) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def demande_complements(cls, proposition: Proposition, objet_message: str, corps_message: str) -> EmailMessage:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def demande_paiement_frais_dossier(cls, proposition: Proposition) -> EmailMessage:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def confirmer_envoi_a_fac_lors_de_la_decision_facultaire(
        cls,
        proposition: Proposition,
        email_destinataire_repository: IEmailDestinataireRepository,
    ) -> Optional[EmailMessage]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def confirmer_reception_documents_envoyes_par_candidat(
        cls,
        proposition: PropositionDTO,
        liste_documents_reclames: List[EmplacementDocument],
        liste_documents_dto: List[EmplacementDocumentDTO],
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def refuser_proposition_par_sic(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def accepter_proposition_par_sic(
        cls,
        proposition_uuid: str,
        objet_message: str,
        corps_message: str,
        digit_repository: 'IDigitRepository',
    ) -> EmailMessage:
        raise NotImplementedError

    @classmethod
    def modifier_authentification_experience_parcours(
        cls,
        proposition: Proposition,
        etat_authentification: str,
    ) -> Optional[EmailMessage]:
        methode_notification = {
            EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name: cls.demande_verification_titre_acces,
            EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name: (
                cls.informer_candidat_verification_parcours_en_cours
            ),
        }.get(etat_authentification)

        if methode_notification:
            return methode_notification(proposition)

    @classmethod
    @abstractmethod
    def demande_verification_titre_acces(cls, proposition: Proposition) -> EmailMessage:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def informer_candidat_verification_parcours_en_cours(cls, proposition: Proposition) -> EmailMessage:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def notifier_candidat_derogation_financabilite(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        raise NotImplementedError
