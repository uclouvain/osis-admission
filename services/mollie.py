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
import contextlib
import datetime
import logging
from time import sleep
from typing import Dict, List

import attr
import requests
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, get_language

from admission.contrib.models.online_payment import StatutPaiement, MethodePaiement

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
    date_d_expiration: datetime.datetime
    date_de_creation: datetime.datetime
    date_de_mise_a_jour: datetime.datetime


class MollieService:
    MOLLIE_BASE_URL: str = settings.MOLLIE_API_BASE_URL

    @classmethod
    def recuperer_paiement(cls, paiement_id: str) -> PaiementMollie:
        logger.info(f"[MOLLIE] Récupération paiement avec mollie_id {paiement_id}")
        try:
            response = request_retry(
                url=f"{cls.MOLLIE_BASE_URL}/{paiement_id}",
                headers={'Authorization': f'Bearer {settings.MOLLIE_API_TOKEN}'}
            )
            result = response.json()
        except Exception as e:
            logger.error(
                f"[MOLLIE] Une erreur est survenue durant la requête à Mollie "
                f"pour la récupération du paiement avec mollie_id : {paiement_id}"
            )
            raise FetchMolliePaymentException(mollie_id=paiement_id) from e

        logger.info(f"[MOLLIE] JSON reçu : {result}")
        return cls._convert_to_dto(result)

    @classmethod
    def creer_paiement(cls, reference: int, montant: str, url_redirection: str) -> PaiementMollie:
        base_url = (
            settings.ADMISSION_BACKEND_LINK_PREFIX if settings.ENVIRONMENT != 'LOCAL'
            else 'https://ac26-2001-6a8-3081-a001-00-8268-f0de.ngrok-free.app'
        )
        data = {
            "amount[value]": montant,
            "amount[currency]": "EUR",
            'description': f"{str(_('Payment of application fees'))} - {reference}",
            'redirectUrl': url_redirection,
            'webhookUrl': f"{base_url}{reverse('admission:mollie-webhook')}",
            'locale': 'fr_BE' if get_language() == settings.LANGUAGE_CODE else 'en_US'
        }
        logger.info(f"[MOLLIE] Création d'un paiement pour l'admission avec référence {reference} - data : {data}")

        try:
            response = request_retry(
                url=cls.MOLLIE_BASE_URL,
                method='post',
                success_list=[201],
                data=data,
                headers={'Authorization': f'Bearer {settings.MOLLIE_API_TOKEN}'}
            )
            result = response.json()
        except Exception as e:
            logger.error(
                f"[MOLLIE] Une erreur est survenue durant la requête à Mollie "
                f"pour la création d'un paiement pour l'admission avec référence {reference}"
            )
            raise CreateMolliePaymentException(reference=reference) from e

        logger.info(f"[MOLLIE] JSON reçu : {result}")
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
            statut=StatutPaiement(result['status']).name,
            methode=MethodePaiement(result['method']).name if result['method'] else None,
            date_d_expiration=datetime.datetime.strptime(date_d_expiration, date_format),
            date_de_creation=datetime.datetime.strptime(result.get('createdAt'), date_format),
            date_de_mise_a_jour=datetime.datetime.now(),
            description=result['description']
        )


class FetchMolliePaymentException(Exception):
    def __init__(self, mollie_id: str, **kwargs):
        self.message = f"[MOLLIE] Impossible de récupérer le paiement avec mollie_id: {mollie_id}"
        super().__init__(**kwargs)


class CreateMolliePaymentException(Exception):
    def __init__(self, reference: int, **kwargs):
        self.message = f"[MOLLIE] Impossible de créer le paiement pour l'admission avec reference: {reference}"
        super().__init__(**kwargs)


def request_retry(
    url: str,
    num_retries: int = 1,
    success_list: List[int] = None,
    method: str = 'get',
    backoff_factor: int = 1,
    **kwargs
):
    if not success_list:
        success_list = [200]
    for try_number in range(num_retries):
        logger.info(f"Request to {url} : try #{try_number + 1}/{num_retries}")
        with contextlib.suppress(requests.exceptions.ConnectionError):
            request_method = getattr(requests, method)
            response = request_method(url, **kwargs)
            if response.status_code in success_list:
                return response
        sleep_time = backoff_factor * (2 ** (num_retries - 1))
        logger.warning(
            f"Try #{try_number + 1}/{num_retries} failed (status_code : {response.status_code}) - "
            f"Pause of {sleep_time} seconds before next try"
        )
        sleep(sleep_time)
