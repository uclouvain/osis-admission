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
from pprint import pprint

import attr
import requests
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, get_language
from django.views import View
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED

from admission.contrib.models.online_payment import StatutPaiement


@attr.dataclass
class PaiementEnLigne:
    checkout_url: str
    paiement_url: str
    paiement_id: str
    statut: str
    methode: str
    date_d_expiration: datetime.date


class PaiementEnLigneService:
    MONTANT_FRAIS_DE_DOSSIER: str = "200.00"
    MOLLIE_BASE_URL: str = settings.MOLLIE_API_BASE_URL

    @classmethod
    def recuperer_paiement(cls, id: str):
        response = requests.get(
            url=f"{cls.MOLLIE_BASE_URL}/{id}",
            headers={
                'Authorization': f'Bearer {settings.MOLLIE_API_TOKEN}'
            }
        )
        result = response.json()
        pprint(result)
        if response.status_code == HTTP_200_OK:
            return cls._convert_to_dto(result)
        print(response.status_code)

    @classmethod
    def creer_paiement(cls, base_url: str) -> PaiementEnLigne:
        response = requests.post(
            url=cls.MOLLIE_BASE_URL,
            data={
                "amount[value]": cls.MONTANT_FRAIS_DE_DOSSIER,
                "amount[currency]": "EUR",
                'description': str(_('Payment of application fees')),  # TODO: add reference/number
                'redirectUrl': 'http://www.google.be',
                'cancelUrl': '',
                'webhookUrl': f"{base_url}{reverse('mollie_webhook')}",
                'locale': 'fr_BE' if get_language() == settings.LANGUAGE_CODE else 'en_US'
            },
            headers={
                'Authorization': f'Bearer {settings.MOLLIE_API_TOKEN}'
            }
        )
        print(reverse('mollie_webhook'))
        result = response.json()
        pprint(result)
        if response.status_code == HTTP_201_CREATED:
            return cls._convert_to_dto(result)
        print(response.status_code)

    @classmethod
    def _convert_to_dto(cls, result) -> PaiementEnLigne:
        return PaiementEnLigne(
            checkout_url=result['_links'].get('checkout', {}).get('href', ''),
            paiement_url=result['_links']['self']['href'],
            paiement_id=result['id'],
            statut=StatutPaiement(result['status']).name,
            methode=result['method'],
            date_d_expiration=datetime.datetime.strptime(
                result.get('expiresAt', result.get('expiredAt')),
                '%Y-%m-%dT%H:%M:%S+00:00'
            ),
        )


class MollieWebHook(View):
    name = 'mollie_webhook'

    def post(self, request, *args, **kwargs):
        print("YOLO")
        body = request.data
        print(request)
        print(body)
        return HttpResponse()

