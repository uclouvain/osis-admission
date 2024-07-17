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
from typing import List

from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import SignataireIdentity
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import INotification
from admission.ddd.admission.doctorat.preparation.dtos import AvisDTO, PropositionDTO
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO


class NotificationInMemory(INotification):
    @classmethod
    def envoyer_signatures(cls, *args, **kwargs) -> None:
        pass

    @classmethod
    def notifier_avis(cls, proposition: Proposition, signataire_id: 'SignataireIdentity', avis: AvisDTO) -> None:
        pass

    @classmethod
    def notifier_soumission(cls, proposition: Proposition) -> None:
        pass

    @classmethod
    def notifier_suppression_membre(cls, proposition: Proposition, signataire_id: 'SignataireIdentity') -> None:
        pass

    @classmethod
    def renvoyer_invitation(cls, proposition: Proposition, membre: 'SignataireIdentity'):
        pass

    @classmethod
    def envoyer_message_libre_au_candidat(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        pass

    @classmethod
    def confirmer_reception_documents_envoyes_par_candidat(
        cls,
        proposition: PropositionDTO,
        liste_documents_reclames: List[EmplacementDocument],
        liste_documents_dto: List[EmplacementDocumentDTO],
    ):
        pass
