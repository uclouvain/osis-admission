##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from typing import List

from osis_common.ddd import interface


class IContingente(interface.DomainService):
    @classmethod
    def generer_numero_de_dossier_ares_si_necessaire(cls, proposition: 'Proposition', annee: int) -> str:
        raise NotImplementedError

    @classmethod
    def verifier_proposition_contingente_unique(cls, proposition_candidat: 'PropositionFormationGenerale'):
        raise NotImplementedError

    @classmethod
    def recuperer_admissions_a_notifier(
        cls, formation_id: 'FormationIdentity'
    ) -> List['AdmissionContingenteNonResidenteNotificationDTO']:
        raise NotImplementedError

    @classmethod
    def notifier_admissions_en_lot(
        cls,
        formation_id: 'FormationIdentity',
        gestionnaire: str,
        proposition_repository: 'IPropositionRepository',
        profil_candidat_translator: 'IProfilCandidatTranslator',
        pdf_generation: 'IPDFGeneration',
        notification: 'INotification',
        historique: 'IHistorique',
    ) -> List['PropositionDTO']:
        raise NotImplementedError

    @classmethod
    def notifier_admission(
        cls,
        proposition_id: 'PropositionIdentity',
        gestionnaire: str,
        proposition_repository: 'IPropositionRepository',
        profil_candidat_translator: 'IProfilCandidatTranslator',
        pdf_generation: 'IPDFGeneration',
        notification: 'INotification',
        historique: 'IHistorique',
    ) -> None:
        raise NotImplementedError
