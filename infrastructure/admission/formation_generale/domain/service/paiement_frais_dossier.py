##############################################################################
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
##############################################################################
from typing import List

from django.conf import settings

from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.online_payment import PaymentStatus, OnlinePayment
from admission.ddd import MONTANT_FRAIS_DOSSIER
from admission.ddd.admission.formation_generale.domain.service.i_paiement_frais_dossier import IPaiementFraisDossier
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_generale.dtos.paiement import PaiementDTO
from admission.services.paiement_en_ligne import PaiementEnLigneService


class PaiementFraisDossier(IPaiementFraisDossier):
    @classmethod
    def paiement_realise(cls, proposition_uuid: str) -> bool:
        try:
            admission = BaseAdmission.objects.get(uuid=proposition_uuid)
        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException
        payments = PaiementEnLigneService.get_all_payments(
            admission=admission,
        )
        return any(payment.status == PaymentStatus.PAID.name for payment in payments)

    @classmethod
    def ouvrir_paiement(cls, proposition_uuid: str) -> PaiementDTO:
        try:
            admission = BaseAdmission.objects.get(uuid=proposition_uuid)
        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException
        payment = PaiementEnLigneService.get_or_create_payment(
            url_redirection=settings.ADMISSION_FRONTEND_LINK.format(context='general-education', uuid=proposition_uuid)
            + 'payment?from_mollie=1',
            admission=admission,
            montant=MONTANT_FRAIS_DOSSIER,
        )
        return cls._to_dto(payment)

    @staticmethod
    def _to_dto(payment: OnlinePayment) -> PaiementDTO:
        return PaiementDTO(
            identifiant_paiement=payment.payment_id,
            statut=payment.status,
            methode=payment.method,
            montant=payment.amount,
            date_creation=payment.creation_date,
            date_mise_a_jour=payment.updated_date,
            date_expiration=payment.expiration_date,
            url_checkout=payment.checkout_url,
        )

    @classmethod
    def recuperer_paiements_proposition(cls, proposition_uuid) -> List[PaiementDTO]:
        try:
            admission = BaseAdmission.objects.get(uuid=proposition_uuid)
        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

        payments = PaiementEnLigneService.get_all_payments(admission=admission)

        return [cls._to_dto(payment) for payment in payments]
