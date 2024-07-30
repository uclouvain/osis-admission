##############################################################################
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
##############################################################################
from django.test import TestCase, RequestFactory
from django.urls import reverse

from admission.api.serializers.payment_method import PaymentMethodSerializer
from admission.tests.factories.payment import OnlinePaymentFactory
from base.tests.factories.student import StudentFactory


class PaymentMethodSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = StudentFactory()
        cls.payment = OnlinePaymentFactory(admission__candidate__student=cls.student)
        url = reverse(
            'admission_api_v1:payment-method-application-fees',
            kwargs={'noma': cls.student.registration_id}
        )
        cls.serializer = PaymentMethodSerializer(cls.payment, context={'request': RequestFactory().get(url), })

    def test_contains_expected_fields(self):
        expected_fields = [
            'method',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)
