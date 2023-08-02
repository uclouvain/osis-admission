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
from _decimal import Decimal

from django.conf import settings

from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.online_payment import OnlinePayment, StatutPaiement
from admission.services.mollie import MollieService, PaiementMollie

logger = logging.getLogger(settings.DEFAULT_LOGGER)


class PaiementEnLigneService:
    MONTANT_FRAIS_DE_DOSSIER: Decimal = Decimal(200)
    paiement_service = MollieService

    @classmethod
    def get_and_update_payment(cls, paiement_id: str, admission: BaseAdmission = None) -> OnlinePayment:
        online_payment = OnlinePayment.objects.get_or_create(
            payment_id=paiement_id,
            admission_id=admission.pk if admission else None
        )
        paiement_mollie = cls.paiement_service.recuperer_paiement(paiement_id=paiement_id)
        cls._update_payment(online_payment, paiement_mollie)
        return online_payment

    @classmethod
    def _update_payment(cls, online_payment: OnlinePayment, paiement_mollie: PaiementMollie):
        online_payment.methode = paiement_mollie.methode
        online_payment.status = paiement_mollie.statut
        online_payment.updated_date = paiement_mollie.date_de_mise_a_jour
        online_payment.checkout_url = paiement_mollie.checkout_url
        online_payment.save()

    @classmethod
    def get_or_create_payment(cls, url_redirection: str, admission: BaseAdmission) -> OnlinePayment:
        paiements_ouverts = OnlinePayment.objects.filter(
            admission_id=admission.id,
            status__in=StatutPaiement.paiements_ouverts,
        )
        if paiements_ouverts:
            return paiements_ouverts.first()
        paiement_mollie = cls.paiement_service.creer_paiement(
            reference=str(admission.reference),
            montant=cls.MONTANT_FRAIS_DE_DOSSIER,
            url_redirection=url_redirection
        )
        paiement_en_ligne = cls._convert_to_db_object(paiement_mollie, admission)
        paiement_en_ligne.save()
        return paiement_en_ligne

    @classmethod
    def _convert_to_db_object(cls, paiement_mollie: PaiementMollie, admission: BaseAdmission) -> OnlinePayment:
        return OnlinePayment(
            payment_id=paiement_mollie.paiement_id,
            admission_id=admission.id,
            status=paiement_mollie.statut,
            expiration_date=paiement_mollie.date_d_expiration,
            method=paiement_mollie.methode,
            creation_date=paiement_mollie.date_de_creation,
            updated_date=datetime.datetime.now(),
            checkout_url=paiement_mollie.checkout_url,
            payment_url=paiement_mollie.paiement_url,
            dashboard_url=paiement_mollie.dashboard_url,
            montant=paiement_mollie.montant
        )
