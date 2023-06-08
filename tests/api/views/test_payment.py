# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import copy
from unittest import mock

import mock
from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.translation import gettext
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PaiementNonRealiseException,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import CandidateFactory
from base.tests.factories.education_group_year import Master120TrainingFactory


class PayApplicationFeesAfterSubmissionViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
            ),
            training=Master120TrainingFactory(),
            status=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
            checklist={},
        )

        self.url = resolve_url('admission_api_v1:pay_after_submission', uuid=self.admission.uuid)

    def test_pay_application_fees_with_candidate(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        response = self.client.post(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(response_data, {'uuid': str(self.admission.uuid)})

        # Check the update of the admission
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertIn('initial', self.admission.checklist)
        self.assertEqual(
            self.admission.checklist['initial']['frais_dossier']['statut'],
            ChoixStatutChecklist.SYST_REUSSITE.name,
        )
        self.assertEqual(self.admission.checklist['initial']['frais_dossier']['libelle'], 'Payed')
        self.assertIn('current', self.admission.checklist)
        self.assertEqual(
            self.admission.checklist['current']['frais_dossier']['statut'],
            ChoixStatutChecklist.SYST_REUSSITE.name,
        )
        self.assertEqual(self.admission.checklist['current']['frais_dossier']['libelle'], 'Payed')

    def test_pay_application_fees_with_candidate_is_forbidden_if_the_fees_have_not_been_paid(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        with mock.patch(
            'admission.infrastructure.admission.formation_generale.domain.service.paiement_frais_dossier.'
            'PaiementFraisDossier.paiement_realise',
            return_value=False,
        ):
            response = self.client.post(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()

        triggered_exception = PaiementNonRealiseException()
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

        # Check that the admission hasn't changed
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name)
        self.assertEqual(self.admission.checklist, {})

    def test_pay_application_fees_with_candidate_is_forbidden_if_he_has_not_been_invited_to_do_it(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        self.admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.admission.save()

        response = self.client.post(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response_data = response.json()

        self.assertEqual(
            response_data,
            {'detail': gettext('You must be invited to pay the application fees by the system.')},
        )

    def test_pay_application_fees_other_candidate_is_forbidden(self):
        self.client.force_authenticate(user=CandidateFactory().person.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PayApplicationFeesAfterRequestViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
            ),
            training=Master120TrainingFactory(),
            status=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        )
        self.admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        self.admission.checklist['current']['frais_dossier']['libelle'] = 'Must pay'
        self.admission.save()

        self.default_checklist = copy.deepcopy(self.admission.checklist)

        self.url = resolve_url('admission_api_v1:pay_after_request', uuid=self.admission.uuid)

    def test_pay_application_fees_with_candidate(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        response = self.client.post(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(response_data, {'uuid': str(self.admission.uuid)})

        # Check the update of the admission
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertIn('current', self.admission.checklist)
        self.assertEqual(
            self.admission.checklist['current']['frais_dossier']['statut'],
            ChoixStatutChecklist.SYST_REUSSITE.name,
        )
        self.assertEqual(self.admission.checklist['current']['frais_dossier']['libelle'], 'Payed')

    def test_pay_application_fees_with_candidate_is_forbidden_if_the_fees_have_not_been_paid(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        with mock.patch(
            'admission.infrastructure.admission.formation_generale.domain.service.paiement_frais_dossier.'
            'PaiementFraisDossier.paiement_realise',
            return_value=False,
        ):
            response = self.client.post(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()

        triggered_exception = PaiementNonRealiseException()
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

        # Check that the admission hasn't changed
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name)
        self.assertEqual(self.admission.checklist, self.default_checklist)

    def test_pay_application_fees_with_candidate_is_forbidden_if_he_has_not_been_invited_to_do_it(self):
        self.client.force_authenticate(user=self.admission.candidate.user)

        self.admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.admission.save()

        response = self.client.post(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response_data = response.json()

        self.assertEqual(
            response_data,
            {'detail': gettext('You must be invited to pay the application fees by a manager.')},
        )

        self.admission.status = ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name
        self.admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.SYST_REUSSITE.name
        self.admission.save()

        response = self.client.post(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pay_application_fees_other_candidate_is_forbidden(self):
        self.client.force_authenticate(user=CandidateFactory().person.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
