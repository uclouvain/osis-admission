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
import datetime
import logging
from decimal import Decimal

from django.conf import settings
from django.db.models import QuerySet

from admission.models.base import BaseAdmission
from admission.models.online_payment import OnlinePayment, PaymentStatus
from admission.services.mollie import MollieService, PaiementMollie, FetchMolliePaymentException

logger = logging.getLogger(settings.DEFAULT_LOGGER)


class PaiementEnLigneService:
    paiement_service = MollieService

    @classmethod
    def update_payment(cls, paiement_id: str) -> OnlinePayment:
        paiement_mollie = cls.paiement_service.recuperer_paiement(paiement_id)
        online_payment = OnlinePayment.objects.get(payment_id=paiement_id)
        cls._update_payment(online_payment, paiement_mollie)
        return online_payment

    @classmethod
    def get_and_update_payment(cls, paiement_id: str, admission: BaseAdmission) -> OnlinePayment:
        online_payment = OnlinePayment.objects.get(payment_id=paiement_id, admission_id=admission.pk)
        try:
            paiement_mollie = cls.paiement_service.recuperer_paiement(paiement_id=paiement_id)
            cls._update_payment(online_payment, paiement_mollie)
        except FetchMolliePaymentException:
            pass
        return online_payment

    @classmethod
    def _update_payment(cls, online_payment: OnlinePayment, paiement_mollie: PaiementMollie):
        online_payment.method = paiement_mollie.methode or ''
        online_payment.status = paiement_mollie.statut
        online_payment.updated_date = paiement_mollie.date_de_mise_a_jour
        online_payment.checkout_url = paiement_mollie.checkout_url
        try:
            online_payment.save()
        except Exception as e:
            logger.exception(
                f"[PAIEMENT EN LIGNE] Impossible de mettre a jour le paiement en ligne {paiement_mollie}"
            )
            raise UpdateOnlinePaymentException(reference=str(online_payment.admission)) from e

    @classmethod
    def get_or_create_payment(cls, url_redirection: str, admission: BaseAdmission, montant: Decimal) -> OnlinePayment:
        paiements_ouverts = OnlinePayment.objects.filter(
            admission_id=admission.id,
            status__in=PaymentStatus.open_payments(),
        )
        if paiements_ouverts.exists():
            paiement_ouvert = paiements_ouverts.first()
            paiement_ouvert = cls.update_payment(paiement_id=paiement_ouvert.payment_id)
            if paiement_ouvert.status in PaymentStatus.open_payments():
                return paiement_ouvert

        paiement_mollie = cls.paiement_service.creer_paiement(
            reference=str(admission),
            montant=montant,
            url_redirection=url_redirection,
        )
        paiement_en_ligne = cls._convert_to_db_object(paiement_mollie, admission)
        try:
            paiement_en_ligne.save()
        except Exception as e:
            raise SaveOnlinePaymentException(reference=str(admission)) from e
        return paiement_en_ligne

    @classmethod
    def _convert_to_db_object(cls, paiement_mollie: PaiementMollie, admission: BaseAdmission) -> OnlinePayment:
        return OnlinePayment(
            payment_id=paiement_mollie.paiement_id,
            admission_id=admission.id,
            status=paiement_mollie.statut,
            expiration_date=paiement_mollie.date_d_expiration,
            method=paiement_mollie.methode or '',
            creation_date=paiement_mollie.date_de_creation,
            updated_date=datetime.datetime.now(),
            checkout_url=paiement_mollie.checkout_url,
            payment_url=paiement_mollie.paiement_url,
            dashboard_url=paiement_mollie.dashboard_url,
            amount=paiement_mollie.montant,
        )

    @classmethod
    def get_all_payments(cls, admission: BaseAdmission) -> QuerySet[OnlinePayment]:
        payments = OnlinePayment.objects.filter(admission_id=admission.pk).order_by('creation_date')
        open_payments = payments.filter(status__in=PaymentStatus.open_payments())
        if open_payments.exists():
            last_open_payment = open_payments.last()
            cls.get_and_update_payment(paiement_id=last_open_payment.payment_id, admission=admission)
        return payments


class PaiementEnLigneException(Exception):
    pass


class SaveOnlinePaymentException(PaiementEnLigneException):
    def __init__(self, reference: str, **kwargs):
        self.message = (
            f"[PAIEMENT EN LIGNE] Une erreur est survenue durant la creation du paiement en ligne "
            f"du dossier {reference} en DB"
        )
        super().__init__(**kwargs)


class UpdateOnlinePaymentException(PaiementEnLigneException):
    def __init__(self, reference: str, **kwargs):
        self.message = (
            f"[PAIEMENT EN LIGNE] Une erreur est survenue durant la mise a jour du paiement en ligne "
            f"du dossier {reference} en DB"
        )
        super().__init__(**kwargs)
