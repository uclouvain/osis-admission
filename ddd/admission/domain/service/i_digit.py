# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import logging
from abc import abstractmethod
from types import SimpleNamespace
from typing import Optional

from django.conf import settings

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.domain.validator.exceptions import FusionDigitDesactiveeException, \
    ADejaTicketCreationEnAttenteException, NeCorrespondPasACompteTemporaireException, \
    NotInAccountCreationPeriodException, \
    AdmissionDansUnStatutPasAutoriseASInscrireException, PropositionFusionEnCoursDeTraitementException
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.repository.i_digit import IDigitRepository
from base.models.person_merge_proposal import PersonMergeStatus
from osis_common.ddd import interface
from osis_common.ddd.interface import BusinessException


class IDigitService(interface.DomainService):

    @classmethod
    @abstractmethod
    def fusion_digit_est_active(cls) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def correspond_a_compte_temporaire(cls, matricule_candidat: str) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def recuperer_proposition_fusion(cls, matricule_candidat: str) -> Optional[SimpleNamespace]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def rechercher_compte_existant(
            cls,
            matricule: str,
            nom: str,
            prenom: str,
            autres_prenoms: str,
            genre: str,
            date_naissance: str,
            niss: str
    ) -> str:
        raise NotImplementedError

    @classmethod
    def verifier_peut_soumettre_ticket_creation(
            cls,
            proposition: Proposition,
            digit_repository: 'IDigitRepository',
    ):
        logger = logging.getLogger(settings.DEFAULT_LOGGER)

        try:
            if not cls.fusion_digit_est_active():
                raise FusionDigitDesactiveeException()

            if digit_repository.has_pending_digit_creation_ticket(global_id=proposition.matricule_candidat):
                raise ADejaTicketCreationEnAttenteException(matricule_candidat=proposition.matricule_candidat)

            if not cls.correspond_a_compte_temporaire(proposition.matricule_candidat):
                raise NeCorrespondPasACompteTemporaireException(matricule_candidat=proposition.matricule_candidat)

            # replace with date from academic calendar
            open_year = 2024
            if not proposition.annee_calculee == open_year:
                raise NotInAccountCreationPeriodException(matricule_candidat=proposition.matricule_candidat)

            if proposition.type_demande == TypeDemande.ADMISSION and proposition.statut not in {
                ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE,
                ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE,
                ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE,
            }:
                raise AdmissionDansUnStatutPasAutoriseASInscrireException(
                    matricule_candidat=proposition.matricule_candidat
                )

            proposition_fusion = cls.recuperer_proposition_fusion(proposition.matricule_candidat)
            if proposition_fusion:
                if proposition_fusion.statut not in [
                    PersonMergeStatus.MERGED.name, PersonMergeStatus.REFUSED.name, PersonMergeStatus.NO_MATCH.name
                ]:
                    raise PropositionFusionEnCoursDeTraitementException(
                        merge_status=proposition_fusion.statut,
                        matricule_candidat=proposition.matricule_candidat
                    )
        except BusinessException as e:
            logger.info(f"DIGIT submit ticket canceled: {e.message}")
            raise e
