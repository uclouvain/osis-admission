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

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from admission.api.serializers.payment_method import PaymentMethodSerializer
from admission.models.online_payment import PaymentStatus
from admission.tests.factories.payment import OnlinePaymentFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.user import UserFactory


class PaymentMethodAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.candidate = PersonFactory()
        cls.student = StudentFactory(person=cls.candidate)
        cls.payment = OnlinePaymentFactory(admission__candidate=cls.candidate, status=PaymentStatus.PAID.name)
        cls.url_kwargs = {'noma': cls.student.registration_id}
        cls.url = reverse('admission_api_v1:payment-method-application-fees', kwargs=cls.url_kwargs)

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_valid_payment_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = PaymentMethodSerializer(self.payment)
        self.assertEqual(response.data, serializer.data)

    def test_not_get_unpaid_payment_method(self):
        candidate = PersonFactory()
        student = StudentFactory(person=candidate)
        OnlinePaymentFactory(admission__candidate=candidate, status=PaymentStatus.OPEN.name)
        url = reverse(
            'admission_api_v1:payment-method-application-fees',
            kwargs={'noma': student.registration_id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('OnlinePayment matching query does not exist', response.data['detail'])

    def test_get_invalid_student_case_not_found(self):
        invalid_url = reverse(
            'admission_api_v1:payment-method-application-fees',
            kwargs={
                'noma': '0000000000',
            }
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('OnlinePayment matching query does not exist', response.data['detail'])
