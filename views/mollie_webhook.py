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

from django.http import HttpResponse
from rest_framework.parsers import FormParser
from rest_framework.views import APIView

from admission.contrib.models import GeneralEducationAdmission

from admission.auth.predicates import (
    is_invited_to_pay_after_submission,
    is_invited_to_pay_after_request,
    payment_needed_after_submission,
    payment_needed_after_manager_request,
)
from admission.contrib.models.online_payment import PaymentStatus
from admission.ddd.admission.formation_generale.commands import (
    PayerFraisDossierPropositionSuiteDemandeCommand,
    PayerFraisDossierPropositionSuiteSoumissionCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionPourPaiementInvalideException,
)
from admission.services.paiement_en_ligne import PaiementEnLigneService

__all__ = [
    'MollieWebHook',
]

from infrastructure.messages_bus import message_bus_instance


class MollieWebHook(APIView):
    """
    Mollie appelle le webhook quand un paiement atteint l'un des statuts suivants :
        PaymentStatus.PAID
        PaymentStatus.EXPIRED
        PaymentStatus.FAILED
        PaymentStatus.CANCELED
    DEV étant inaccessible depuis l'extérieur, il faut simuler l'appel au webhook
    """

    parser_classes = [FormParser]
    permission_classes = []

    def post(self, request, *args, **kwargs):
        paiement_id = request.POST.get('id')
        self.update_from_payment(paiement_id)
        return HttpResponse()

    @staticmethod
    def update_from_payment(paiement_id):
        # Update the payment
        updated_payment = PaiementEnLigneService.update_payment(paiement_id=paiement_id)

        if updated_payment.status == PaymentStatus.PAID.name:
            # Update the admission and inform the candidate that the payment is successful
            admission = GeneralEducationAdmission.objects.get(pk=updated_payment.admission_id)

            if payment_needed_after_submission(admission=admission):
                # After the submission
                return message_bus_instance.invoke(
                    PayerFraisDossierPropositionSuiteSoumissionCommand(uuid_proposition=admission.uuid)
                )
            elif payment_needed_after_manager_request(admission=admission):
                # After a manager request
                return message_bus_instance.invoke(
                    PayerFraisDossierPropositionSuiteDemandeCommand(uuid_proposition=admission.uuid)
                )

            raise PropositionPourPaiementInvalideException
