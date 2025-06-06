# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.exceptions import NotFound

from admission.api.serializers.payment_method import PaymentMethodSerializer
from admission.models.online_payment import OnlinePayment, PaymentStatus


@extend_schema_view(
    get=extend_schema(operation_id="retrievePaymentMethod"),
)
class PaymentMethodAPIView(generics.RetrieveAPIView):
    """
    Get the payment method of the application fees
    """

    name = 'payment-method-application-fees'
    filter_backends = []
    serializer_class = PaymentMethodSerializer

    def get_object(self) -> 'OnlinePayment':
        try:
            return (
                OnlinePayment.objects.filter(
                    admission__candidate__student__registration_id=self.kwargs['noma'],
                    status=PaymentStatus.PAID.name,
                )
                .values('method')
                .get()
            )
        except OnlinePayment.DoesNotExist as e:
            raise NotFound(detail=str(e))
