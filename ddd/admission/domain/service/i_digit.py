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

from django.conf import settings

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.domain.service.i_periode_soumission_ticket_digit import \
    IPeriodeSoumissionTicketDigitTranslator
from admission.ddd.admission.domain.validator.exceptions import (
    NotInAccountCreationPeriodException,
    AdmissionDansUnStatutPasAutoriseASInscrireException, PropositionFusionATraiterException,
    PropositionDeFusionAvecValidationSyntaxiqueInvalideException,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from base.models.person_merge_proposal import PersonMergeStatus
from osis_common.ddd import interface
from osis_common.ddd.interface import BusinessException


class IDigitService(interface.DomainService):

    @classmethod
    @abstractmethod
    def correspond_a_compte_temporaire(cls, matricule_candidat: str) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def recuperer_proposition_fusion(cls, matricule_candidat: str) -> SimpleNamespace:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def rechercher_compte_existant(
        cls,
        matricule: str,
    ) -> str:
        raise NotImplementedError

    @classmethod
    def verifier_peut_soumettre_ticket_creation(
        cls,
        proposition: Proposition,
        periode_soumission_ticket_digit_translator: 'IPeriodeSoumissionTicketDigitTranslator'
    ):
        logger = logging.getLogger(settings.DEFAULT_LOGGER)

        try:
            if cls.correspond_a_compte_temporaire(proposition.matricule_candidat):
                cls.peut_soumettre_compte_temporaire(
                    logger,
                    periode_soumission_ticket_digit_translator,
                    proposition
                )
            else:
                cls.peut_soumettre_compte_interne(
                    logger,
                    periode_soumission_ticket_digit_translator,
                    proposition
                )
        except BusinessException as e:
            logger.exception(f"DIGIT submit ticket canceled: {e.message}")
            raise e

    @classmethod
    def peut_soumettre_compte_interne(cls, logger, periode_soumission_ticket_digit_translator, proposition):
        proposition_fusion = cls.recuperer_proposition_fusion(proposition.matricule_candidat)
        cls._verifier_periode_creation_compte(logger, periode_soumission_ticket_digit_translator, proposition)
        cls._verifier_pas_de_fusion_a_traiter(logger, proposition, proposition_fusion)
        cls._verifier_syntaxe_valide(logger, proposition, proposition_fusion)

    @classmethod
    def peut_soumettre_compte_temporaire(cls, logger, periode_soumission_ticket_digit_translator, proposition):
        proposition_fusion = cls.recuperer_proposition_fusion(proposition.matricule_candidat)
        cls._verifier_periode_creation_compte(logger, periode_soumission_ticket_digit_translator, proposition)
        cls._verifier_statut_autorise(logger, proposition, proposition_fusion)
        cls._verifier_pas_de_fusion_a_traiter(logger, proposition, proposition_fusion)
        cls._verifier_syntaxe_valide(logger, proposition, proposition_fusion)

    @classmethod
    def _verifier_syntaxe_valide(cls, logger, proposition, proposition_fusion):
        if not proposition_fusion.a_une_syntaxe_valide:
            logger.error(
                f"SOUMETTRE TICKET CREATION PERSONNE - PropositionDeFusionAvecValidationSyntaxiqueInvalideException"
            )
            raise PropositionDeFusionAvecValidationSyntaxiqueInvalideException(
                matricule_candidat=proposition.matricule_candidat,
            )

    @classmethod
    def _verifier_pas_de_fusion_a_traiter(cls, logger, proposition, proposition_fusion):
        if proposition_fusion.statut not in [
            PersonMergeStatus.IN_PROGRESS.name,
            PersonMergeStatus.MERGED.name,
            PersonMergeStatus.REFUSED.name,
            PersonMergeStatus.NO_MATCH.name,
        ]:
            logger.error(f"SOUMETTRE TICKET CREATION PERSONNE - PropositionFusionATraiterException")
            raise PropositionFusionATraiterException(
                merge_status=proposition_fusion.statut,
                matricule_candidat=proposition.matricule_candidat
            )

    @classmethod
    def _verifier_statut_autorise(cls, logger, proposition, proposition_fusion):
        if (proposition.type_demande == TypeDemande.ADMISSION and proposition.statut not in {
            ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE,
            ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE,
            ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE,
        } and proposition_fusion.statut not in [PersonMergeStatus.IN_PROGRESS.name, PersonMergeStatus.REFUSED.name]
                and not cls.correspond_a_compte_temporaire(proposition.matricule_candidat)):
            logger.error(
                f"SOUMETTRE TICKET CREATION PERSONNE - AdmissionDansUnStatutPasAutoriseASInscrireException"
            )
            raise AdmissionDansUnStatutPasAutoriseASInscrireException(
                matricule_candidat=proposition.matricule_candidat
            )

    @classmethod
    def _verifier_periode_creation_compte(cls, logger, periode_soumission_ticket_digit_translator, proposition):
        periodes_soumission_ticket_digit = periode_soumission_ticket_digit_translator.get_periodes_actives()
        if proposition.annee_calculee not in [p.annee for p in periodes_soumission_ticket_digit]:
            logger.error(f"SOUMETTRE TICKET CREATION PERSONNE - NotInAccountCreationPeriodException")
            raise NotInAccountCreationPeriodException(matricule_candidat=proposition.matricule_candidat)
