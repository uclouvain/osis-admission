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
import datetime
import logging
from decimal import Decimal
from typing import Dict

import attr
import requests
from django.conf import settings
from django.urls import reverse
from django.utils.translation import get_language

from admission.contrib.models.online_payment import PaymentStatus, PaymentMethod

logger = logging.getLogger(settings.DEFAULT_LOGGER)


@attr.dataclass
class PaiementMollie:
    checkout_url: str
    paiement_url: str
    dashboard_url: str
    paiement_id: str
    statut: str
    methode: str
    description: str
    montant: Decimal
    date_d_expiration: datetime.datetime
    date_de_creation: datetime.datetime
    date_de_mise_a_jour: datetime.datetime


class MollieService:
    """
        Mollie status transition:
              ┌───────────┬─────►PAID
              │           │
              ├───────────┼─────►CANCELED
        OPEN──┤           │
              ├───►PENDING├─────►EXPIRED
              │           │
              └───────────┴─────►FAILED
              PENDING --> FAILED only for banktransfer
        Expiry times per payment method:
            Bancontact : 1 hour
            Bank transfer : 12 (+2) days
            Credit card : 30 minutes
    """
    MOLLIE_BASE_URL: str = settings.MOLLIE_API_BASE_URL

    @classmethod
    def recuperer_paiement(cls, paiement_id: str) -> PaiementMollie:
        logger.info(f"[MOLLIE] Recuperation du paiement avec mollie_id {paiement_id}")
        try:
            response = requests.get(
                url=f"{cls.MOLLIE_BASE_URL}/{paiement_id}",
                headers={'Authorization': f'Bearer {settings.MOLLIE_API_TOKEN}'}
            )
            result = response.json()
        except Exception as e:
            logger.error(
                f"[MOLLIE] Une erreur est survenue durant la requete a Mollie "
                f"pour la recuperation du paiement avec mollie_id : {paiement_id}"
            )
            raise FetchMolliePaymentException(mollie_id=paiement_id) from e

        logger.info(f"[MOLLIE] JSON recu : {result}")
        if response.status_code != 200:
            logger.error(
                f"[MOLLIE] La recuperation du paiement avec mollie_id = {paiement_id} "
                f"a echouee avec un status code = {response.status_code}"
            )
        return cls._convert_to_dto(result)

    @classmethod
    def creer_paiement(cls, reference: str, montant: Decimal, url_redirection: str) -> PaiementMollie:
        data = {
            "amount[value]": '{0:.2f}'.format(montant),
            "amount[currency]": "EUR",
            'description': f"Frais de dossier {reference}",
            'redirectUrl': url_redirection,
            'webhookUrl': f"{settings.ADMISSION_BACKEND_LINK_PREFIX}{reverse('admission:mollie-webhook')}",
            'locale': 'fr_BE' if get_language() == settings.LANGUAGE_CODE else 'en_US'
        }
        logger.info(f"[MOLLIE] Creation d'un paiement pour l'admission avec reference {reference} - data : {data}")

        try:
            response = requests.post(
                url=cls.MOLLIE_BASE_URL,
                data=data,
                headers={'Authorization': f'Bearer {settings.MOLLIE_API_TOKEN}'}
            )
            result = response.json()
        except Exception as e:
            logger.error(
                f"[MOLLIE] Une erreur est survenue durant la requete à Mollie "
                f"pour la creation d'un paiement pour l'admission avec reference {reference}"
            )
            raise CreateMolliePaymentException(reference=reference) from e

        logger.info(f"[MOLLIE] JSON reçu : {result}")
        if response.status_code != 201:
            logger.error(
                f"[MOLLIE] La creation du paiement a echouee avec un status code = {response.status_code}"
            )
            raise CreateMolliePaymentException(reference=reference)
        return cls._convert_to_dto(result)

    @classmethod
    def _convert_to_dto(cls, result: Dict) -> PaiementMollie:
        date_d_expiration = result.get('expiresAt', result.get('expiredAt'))
        date_format = '%Y-%m-%dT%H:%M:%S+00:00'
        return PaiementMollie(
            checkout_url=result['_links'].get('checkout', {}).get('href', ''),
            paiement_url=result['_links']['self']['href'],
            dashboard_url=result['_links']['dashboard']['href'],
            paiement_id=result['id'],
            statut=PaymentStatus(result['status']).name,
            methode=PaymentMethod(result['method']).name if result['method'] else None,
            date_d_expiration=datetime.datetime.strptime(date_d_expiration, date_format),
            date_de_creation=datetime.datetime.strptime(result.get('createdAt'), date_format),
            date_de_mise_a_jour=datetime.datetime.now(),
            description=result['description'],
            montant=Decimal(result['amount']['value'])
        )


class MollieException(Exception):
    pass


class FetchMolliePaymentException(MollieException):
    def __init__(self, mollie_id: str, **kwargs):
        self.message = f"[MOLLIE] Impossible de recuperer le paiement avec mollie_id: {mollie_id}"
        super().__init__(**kwargs)


class CreateMolliePaymentException(MollieException):
    def __init__(self, reference: str, **kwargs):
        self.message = f"[MOLLIE] Impossible de creer le paiement pour l'admission avec reference: {reference}"
        super().__init__(**kwargs)
