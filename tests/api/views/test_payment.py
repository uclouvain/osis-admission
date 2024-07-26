# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime
import uuid
from decimal import Decimal
from email import message_from_string
from unittest import mock

import freezegun
import mock
from django.conf import settings
from django.shortcuts import resolve_url
from osis_notification.models import EmailNotification
from rest_framework import status
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from admission.models import GeneralEducationAdmission
from admission.models.online_payment import OnlinePayment, PaymentStatus, PaymentMethod
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PaiementDejaRealiseException,
    PropositionPourPaiementInvalideException,
)
from admission.services.mollie import PaiementMollie
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.payment import OnlinePaymentFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import CandidateFactory
from base.tests.factories.education_group_year import Master120TrainingFactory
from base.tests.factories.user import UserFactory


class ApplicationFeesListViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
                private_email='candidate@test.be',
            ),
            training=Master120TrainingFactory(),
            status=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        )
        self.admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        self.admission.checklist['current']['frais_dossier']['extra'] = {'initial': '1'}
        self.original_checklist = self.admission.checklist
        self.admission.save()
        self.user = self.admission.candidate.user

        self.url = resolve_url('admission_api_v1:view_application_fees', uuid=self.admission.uuid)

        OnlinePaymentFactory(admission=self.admission, creation_date=datetime.datetime(2020, 1, 1)),
        OnlinePaymentFactory(admission=self.admission, creation_date=datetime.datetime(2020, 1, 2)),
        OnlinePaymentFactory(admission=GeneralEducationAdmissionFactory(), creation_date=datetime.datetime(2020, 1, 3)),

        self.payments = OnlinePayment.objects.filter(admission=self.admission).order_by('creation_date')
        self.mollie_payments = [
            PaiementMollie(
                checkout_url=payment.checkout_url,
                paiement_url=payment.payment_url,
                dashboard_url=payment.dashboard_url,
                paiement_id=payment.payment_id,
                statut=payment.status,
                methode=payment.method,
                date_d_expiration=payment.expiration_date,
                date_de_creation=payment.creation_date,
                date_de_mise_a_jour=payment.updated_date,
                description='',
                montant=payment.amount,
            )
            for payment in self.payments
        ]

        patcher = mock.patch('admission.services.paiement_en_ligne.PaiementEnLigneService.paiement_service')
        patched = patcher.start()
        patched.recuperer_paiement.side_effect = lambda paiement_id: next(
            (payment for payment in self.mollie_payments if payment.paiement_id == paiement_id),
            None,
        )
        self.addCleanup(patcher.stop)

    def test_forbidden_access_if_the_user_is_not_the_related_candidate_and_status_not_allowed(self):
        self.client.force_authenticate(user=UserFactory())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=CandidateFactory().person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user)
        self.admission.status = ChoixStatutPropositionGenerale.EN_BROUILLON.name
        self.admission.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_return_list_of_payments(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payments = response.json()
        self.assertEqual(len(payments), 2)

        for index, payment in enumerate(self.payments):
            self.assertEqual(payments[index]['identifiant_paiement'], payment.payment_id)
            self.assertEqual(payments[index]['statut'], payment.status)
            self.assertEqual(payments[index]['methode'], payment.method)
            self.assertEqual(payments[index]['montant'], f'{payment.amount:.2f}')
            self.assertEqual(payments[index]['url_checkout'], payment.checkout_url)
            self.assertEqual(payments[index]['date_creation'], payment.creation_date.isoformat())
            self.assertEqual(payments[index]['date_mise_a_jour'], payment.updated_date.isoformat())
            self.assertEqual(payments[index]['date_expiration'], payment.expiration_date.isoformat())


@freezegun.freeze_time('2020-01-04')
class OpenApplicationFeesPaymentViewTestCase(APITestCase):
    @classmethod
    def to_mollie(cls, payment: OnlinePayment) -> PaiementMollie:
        return PaiementMollie(
            checkout_url=payment.checkout_url,
            paiement_url=payment.payment_url,
            dashboard_url=payment.dashboard_url,
            paiement_id=payment.payment_id,
            statut=payment.status,
            methode=payment.method,
            date_d_expiration=payment.expiration_date,
            date_de_creation=payment.creation_date,
            date_de_mise_a_jour=payment.updated_date,
            description='',
            montant=payment.amount,
        )

    def setUp(self) -> None:
        self.admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
                private_email='candidate@test.be',
            ),
            training=Master120TrainingFactory(),
            status=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        )
        self.admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        self.admission.checklist['current']['frais_dossier']['extra'] = {'initial': '1'}
        self.original_checklist = self.admission.checklist
        self.admission.save()

        self.user = self.admission.candidate.user

        self.url = resolve_url('admission_api_v1:open_application_fees_payment', uuid=self.admission.uuid)

        OnlinePaymentFactory(
            admission=self.admission,
            status=PaymentStatus.EXPIRED.name,
        ),
        OnlinePaymentFactory(
            admission=self.admission,
            status=PaymentStatus.CANCELED.name,
        ),
        OnlinePaymentFactory(admission=GeneralEducationAdmissionFactory()),

        self.payments = OnlinePayment.objects.filter(admission=self.admission)

        # Mock mollie service
        patcher = mock.patch('admission.services.paiement_en_ligne.PaiementEnLigneService.paiement_service')
        patched = patcher.start()
        patched.recuperer_paiement.side_effect = lambda paiement_id: next(
            (self.to_mollie(payment) for payment in self.payments if payment.payment_id == paiement_id),
            None,
        )
        patched.creer_paiement.side_effect = lambda reference, montant, url_redirection: PaiementMollie(
            checkout_url='https://example.com/checkout',
            paiement_url='https://example.com/payment',
            dashboard_url='https://example.com/dashboard',
            paiement_id=str(uuid.uuid4())[:14],
            statut=PaymentStatus.OPEN.name,
            methode=PaymentMethod.BANCONTACT.name,
            date_d_expiration=datetime.datetime(2020, 2, 2),
            date_de_creation=datetime.datetime(2020, 1, 1),
            date_de_mise_a_jour=datetime.datetime(2020, 1, 1),
            description='',
            montant=Decimal(200),
        )
        self.addCleanup(patcher.stop)

    def test_forbidden_access_after_submission_if_the_user_is_not_the_related_candidate_and_statuses_not_allowed(self):
        self.admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        self.admission.checklist['current']['frais_dossier']['extra'] = {"initial": '1'}

        # No candidate user
        self.client.force_authenticate(user=UserFactory())
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Candidate user but not of the current admission
        self.client.force_authenticate(user=CandidateFactory().person.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Invalid admission status
        self.client.force_authenticate(user=self.user)
        self.admission.status = ChoixStatutPropositionGenerale.EN_BROUILLON.name
        self.admission.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Invalid admission checklist status
        self.admission.status = ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name
        self.admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        self.admission.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Invalid admission checklist extra (after manager request)
        self.admission.status = ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name
        self.admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        self.admission.checklist['current']['frais_dossier']['extra'] = {}
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_forbidden_access_after_a_manager_request_if_the_user_is_not_the_related_candidate_and_statuses_not_allowed(
        self,
    ):
        self.admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        self.admission.checklist['current']['frais_dossier']['extra'] = {}
        self.admission.save()

        # No candidate user
        self.client.force_authenticate(user=UserFactory())
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Candidate user but not of the current admission
        self.client.force_authenticate(user=CandidateFactory().person.user)
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Invalid admission status
        self.client.force_authenticate(user=self.user)
        self.admission.status = ChoixStatutPropositionGenerale.EN_BROUILLON.name
        self.admission.save()
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Invalid admission checklist status
        self.admission.status = ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name
        self.admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        self.admission.save()
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Invalid admission checklist extra (after manager request)
        self.admission.status = ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name
        self.admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        self.admission.checklist['current']['frais_dossier']['extra'] = {'initial': '1'}
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creation_of_a_new_payment_if_there_is_no_opened_one(self):
        self.client.force_authenticate(user=self.user)

        payment = OnlinePayment.objects.filter(admission=self.admission, status=PaymentStatus.OPEN.name).first()
        self.assertIsNone(payment)

        response = self.client.post(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        created_payment = response.json()

        payments = OnlinePayment.objects.filter(admission=self.admission, status=PaymentStatus.OPEN.name)
        self.assertEqual(len(payments), 1)
        self.assertEqual(created_payment['identifiant_paiement'], payments[0].payment_id)
        self.assertEqual(created_payment['statut'], payments[0].status)
        self.assertEqual(created_payment['methode'], payments[0].method)
        self.assertEqual(created_payment['montant'], f'{payments[0].amount:.2f}')
        self.assertEqual(created_payment['url_checkout'], payments[0].checkout_url)
        self.assertEqual(created_payment['date_creation'], payments[0].creation_date.isoformat())
        self.assertEqual(created_payment['date_mise_a_jour'], payments[0].updated_date.isoformat())
        self.assertEqual(created_payment['date_expiration'], payments[0].expiration_date.isoformat())

    def test_returns_an_existing_payment_if_there_is_already_one(self):
        self.client.force_authenticate(user=self.user)

        existing_payment = OnlinePaymentFactory(
            admission=self.admission,
            status=PaymentStatus.OPEN.name,
        )

        response = self.client.post(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        created_payment = response.json()

        payments = OnlinePayment.objects.filter(admission=self.admission, status=PaymentStatus.OPEN.name)
        self.assertEqual(len(payments), 1)
        self.assertEqual(created_payment['identifiant_paiement'], existing_payment.payment_id)
        self.assertEqual(created_payment['statut'], existing_payment.status)
        self.assertEqual(created_payment['methode'], existing_payment.method)
        self.assertEqual(created_payment['montant'], f'{existing_payment.amount:.2f}')
        self.assertEqual(created_payment['url_checkout'], existing_payment.checkout_url)
        self.assertEqual(created_payment['date_creation'], existing_payment.creation_date.isoformat())
        self.assertEqual(created_payment['date_mise_a_jour'], existing_payment.updated_date.isoformat())
        self.assertEqual(created_payment['date_expiration'], existing_payment.expiration_date.isoformat())

    def test_returns_an_exception_if_the_candidate_already_paid(self):
        self.client.force_authenticate(user=self.user)

        existing_payment = OnlinePaymentFactory(
            admission=self.admission,
            status=PaymentStatus.PAID.name,
        )

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()

        triggered_exception = PaiementDejaRealiseException()
        self.assertEqual(
            response_data,
            {
                'non_field_errors': [
                    {
                        'status_code': triggered_exception.status_code,
                        'detail': triggered_exception.message,
                    }
                ]
            },
        )


@freezegun.freeze_time('2020-01-04')
class MollieWebHookTestCase(APITestCase):
    @classmethod
    def to_mollie(cls, payment: OnlinePayment) -> PaiementMollie:
        return PaiementMollie(
            checkout_url=payment.checkout_url,
            paiement_url=payment.payment_url,
            dashboard_url=payment.dashboard_url,
            paiement_id=payment.payment_id,
            statut=payment.status,
            methode=payment.method,
            date_d_expiration=payment.expiration_date,
            date_de_creation=payment.creation_date,
            date_de_mise_a_jour=payment.updated_date,
            description='',
            montant=payment.amount,
        )

    def setUp(self) -> None:
        self.admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
                private_email='candidate@test.be',
            ),
            training=Master120TrainingFactory(),
            status=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        )
        self.admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        self.admission.checklist['current']['frais_dossier']['extra'] = {'initial': '1'}
        self.original_checklist = self.admission.checklist
        self.admission.save()

        self.user = self.admission.candidate.user

        self.url = resolve_url('admission:mollie-webhook')

        OnlinePaymentFactory(
            admission=self.admission,
            status=PaymentStatus.EXPIRED.name,
        ),
        OnlinePaymentFactory(
            admission=self.admission,
            status=PaymentStatus.CANCELED.name,
        ),
        OnlinePaymentFactory(admission=GeneralEducationAdmissionFactory(), creation_date=datetime.datetime(2020, 1, 3)),

        self.payments = list(OnlinePayment.objects.filter(admission=self.admission))

        # Mock mollie service
        patcher = mock.patch('admission.services.paiement_en_ligne.PaiementEnLigneService.paiement_service')
        patched = patcher.start()
        patched.recuperer_paiement.side_effect = lambda paiement_id: next(
            (self.to_mollie(payment) for payment in self.payments if payment.payment_id == paiement_id),
            None,
        )
        self.addCleanup(patcher.stop)

    def test_update_payment(self):
        original_payment = self.payments[0]
        online_payment = OnlinePayment.objects.get(pk=original_payment.pk)
        online_payment.status = PaymentStatus.FAILED.name
        online_payment.save()

        response = self.client.post(
            self.url,
            data=f'id={original_payment.payment_id}',
            content_type='application/x-www-form-urlencoded',
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        online_payment.refresh_from_db()
        self.assertEqual(online_payment.status, original_payment.status)

    def test_pay_application_fees_after_submission(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        payment = OnlinePaymentFactory(
            admission=self.admission,
            status=PaymentStatus.PAID.name,
        )

        self.payments.append(payment)

        response = self.client.post(
            self.url,
            data=f'id={payment.payment_id}',
            content_type='application/x-www-form-urlencoded',
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the update of the admission
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertIn('current', self.admission.checklist)
        self.assertEqual(
            self.admission.checklist['current']['frais_dossier']['statut'],
            ChoixStatutChecklist.SYST_REUSSITE.name,
        )
        self.assertEqual(self.admission.checklist['current']['frais_dossier']['libelle'], 'Payed')

        # Check the notification
        notifications = EmailNotification.objects.filter(person=self.admission.candidate)
        self.assertEqual(len(notifications), 1)

        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], 'candidate@test.be')
        self.assertNotIn('inscription tardive', notifications[0].payload)
        self.assertIn('payement des frais de dossier', notifications[0].payload)

    def test_pay_application_fees_after_manager_request(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        self.admission.checklist['current']['frais_dossier']['extra'] = {}
        self.admission.save()

        payment = OnlinePaymentFactory(
            admission=self.admission,
            status=PaymentStatus.PAID.name,
        )

        self.payments.append(payment)

        response = self.client.post(
            self.url,
            data=f'id={payment.payment_id}',
            content_type='application/x-www-form-urlencoded',
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the update of the admission
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertIn('current', self.admission.checklist)
        self.assertEqual(
            self.admission.checklist['current']['frais_dossier']['statut'],
            ChoixStatutChecklist.SYST_REUSSITE.name,
        )
        self.assertEqual(self.admission.checklist['current']['frais_dossier']['libelle'], 'Payed')

    def test_pay_application_fees_is_not_allowed_if_the_admission_status_is_not_valid(self):
        self.admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.admission.save()

        payment = OnlinePaymentFactory(
            admission=self.admission,
            status=PaymentStatus.PAID.name,
        )

        self.payments.append(payment)

        response = self.client.post(
            self.url,
            data=f'id={payment.payment_id}',
            content_type='application/x-www-form-urlencoded',
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        triggered_exception = PropositionPourPaiementInvalideException()

        self.assertEqual(
            response.json(),
            {
                'non_field_errors': [
                    {
                        'status_code': triggered_exception.status_code,
                        'detail': triggered_exception.message,
                    },
                ],
            },
        )
