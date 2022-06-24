# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
)

from osis_common.ddd import interface


class INotification(interface.DomainService):
    @classmethod
    @abstractmethod
    def notifier_soumission(cls, epreuve_confirmation: EpreuveConfirmation) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def notifier_nouvelle_echeance(cls, epreuve_confirmation: EpreuveConfirmation) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def notifier_echec_epreuve(
        cls,
        epreuve_confirmation: EpreuveConfirmation,
        sujet_notification_candidat,
        message_notification_candidat,
    ) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def notifier_repassage_epreuve(
        cls,
        epreuve_confirmation: EpreuveConfirmation,
        sujet_notification_candidat,
        message_notification_candidat,
    ) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def notifier_reussite_epreuve(cls, epreuve_confirmation: EpreuveConfirmation) -> None:
        raise NotImplementedError
