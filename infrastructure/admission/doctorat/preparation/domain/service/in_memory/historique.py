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
from typing import Optional

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    SignataireIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.dtos import AvisDTO
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO


class HistoriqueInMemory(IHistorique):
    @classmethod
    def historiser_initiation(cls, proposition_identity: PropositionIdentity, matricule_auteur: str):
        pass

    @classmethod
    def historiser_completion(cls, proposition: Proposition, matricule_auteur: str):
        pass

    @classmethod
    def historiser_completion_cotutelle(cls, proposition: Proposition, matricule_auteur: str):
        pass

    @classmethod
    def historiser_avis(
        cls,
        proposition: Proposition,
        signataire_id: 'SignataireIdentity',
        avis: AvisDTO,
        statut_original_proposition: 'ChoixStatutPropositionDoctorale',
        matricule_auteur: Optional[str] = '',
    ):
        pass

    @classmethod
    def historiser_ajout_membre(
        cls,
        proposition: Proposition,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_suppression_membre(
        cls,
        proposition: Proposition,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_modification_membre(
        cls,
        proposition: Proposition,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_designation_promoteur_reference(
        cls,
        proposition: Proposition,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_send_back_to_candidate(
        cls,
        proposition: Proposition,
        matricule_gestionnaire: str,
    ):
        pass

    @classmethod
    def historiser_demande_signatures(cls, proposition: Proposition, matricule_auteur: str):
        pass

    @classmethod
    def historiser_soumission(cls, proposition: Proposition):
        pass

    @classmethod
    def historiser_suppression(cls, proposition: Proposition):
        pass

    @classmethod
    def historiser_message_au_candidat(cls, proposition: Proposition, matricule_emetteur: str, message: EmailMessage):
        pass

    @classmethod
    def historiser_envoi_cdd_par_sic_lors_de_la_decision_cdd(
        cls,
        proposition: Proposition,
        gestionnaire: str,
    ):
        pass

    @classmethod
    def historiser_envoi_sic_par_cdd_lors_de_la_decision_cdd(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        envoi_par_cdd: bool,
    ):
        pass

    @classmethod
    def historiser_refus_cdd(cls, proposition: Proposition, gestionnaire: str, message: EmailMessage):
        pass

    @classmethod
    def historiser_acceptation_cdd(
        cls,
        proposition: Proposition,
        gestionnaire: PersonneConnueUclDTO,
        message: EmailMessage,
    ):
        pass

    @classmethod
    def historiser_specification_informations_acceptation_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_original: ChoixStatutPropositionDoctorale,
    ):
        pass

    @classmethod
    def historiser_refus_sic(cls, proposition: Proposition, message: EmailMessage, gestionnaire: str):
        pass

    @classmethod
    def historiser_acceptation_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: Optional[EmailMessage] = None,
    ):
        pass

    @classmethod
    def historiser_mail_acceptation_inscription_sic(
        cls,
        proposition_uuid: str,
        gestionnaire: str,
        message: EmailMessage,
    ):
        pass

    @classmethod
    def historiser_demande_verification_titre_acces(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
        uuid_experience: str,
    ):
        pass

    @classmethod
    def historiser_information_candidat_verification_parcours_en_cours(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
        uuid_experience: str,
    ):
        pass

    @classmethod
    def historiser_derogation_financabilite(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: Optional[EmailMessage] = None,
    ):
        pass
