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
from typing import List, Optional

from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.service.i_notification import INotification
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from admission.ddd.admission.shared_kernel.domain.service.i_matricule_etudiant import IMatriculeEtudiantService
from admission.ddd.admission.shared_kernel.email_destinataire.repository.i_email_destinataire import (
    IEmailDestinataireRepository,
)


class NotificationInMemory(INotification):
    @classmethod
    def confirmer_soumission(cls, proposition: Proposition) -> None:
        pass

    @classmethod
    def demande_complements(cls, proposition: Proposition, objet_message: str, corps_message: str) -> EmailMessage:
        pass

    @classmethod
    def demande_paiement_frais_dossier(cls, proposition: Proposition):
        pass

    @classmethod
    def confirmer_envoi_a_fac_lors_de_la_decision_facultaire(
        cls,
        proposition: Proposition,
        email_destinataire_repository: IEmailDestinataireRepository,
    ) -> Optional[EmailMessage]:
        pass

    @classmethod
    def confirmer_reception_documents_envoyes_par_candidat(
        cls,
        proposition: PropositionDTO,
        liste_documents_reclames: List[EmplacementDocument],
        liste_documents_dto: List[EmplacementDocumentDTO],
    ):
        pass

    @classmethod
    def refuser_proposition_par_sic(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        pass

    @classmethod
    def accepter_proposition_par_sic(
        cls,
        message_bus,
        proposition_uuid: str,
        objet_message: str,
        corps_message: str,
        matricule_etudiant_service: 'IMatriculeEtudiantService',
    ) -> EmailMessage:
        pass

    @classmethod
    def demande_verification_titre_acces(cls, proposition: Proposition) -> EmailMessage:
        pass

    @classmethod
    def informer_candidat_verification_parcours_en_cours(cls, proposition: Proposition) -> EmailMessage:
        pass

    @classmethod
    def notifier_candidat_derogation_financabilite(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        pass
