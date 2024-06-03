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

from unittest import mock

from django.test import TestCase

from admission.auth.predicates import continuing
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.tests.factories.user import UserFactory


class PredicatesTestCase(TestCase):
    def setUp(self):
        self.predicate_context_patcher = mock.patch(
            "rules.Predicate.context",
            new_callable=mock.PropertyMock,
            return_value={'perm_name': 'dummy-perm'},
        )
        self.predicate_context_patcher.start()
        self.addCleanup(self.predicate_context_patcher.stop)

    @classmethod
    def setUpTestData(cls):
        cls.admission = ContinuingEducationAdmissionFactory()

    def _test_admission_statuses(self, predicate, admission, valid_statuses):
        for status in ChoixStatutPropositionContinue.get_names():
            self.admission.status = status
            self.assertEqual(
                predicate(admission.candidate.user, admission),
                status in valid_statuses,
                f'The status "{status}" is not valid for the predicate "{predicate.__name__}"',
            )

    def test_in_progress(self):
        self._test_admission_statuses(
            predicate=continuing.in_progress,
            admission=self.admission,
            valid_statuses={
                ChoixStatutPropositionContinue.EN_BROUILLON.name,
            },
        )

    def test_is_submitted(self):
        self._test_admission_statuses(
            predicate=continuing.is_submitted,
            admission=self.admission,
            valid_statuses={
                ChoixStatutPropositionContinue.CONFIRMEE.name,
                ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name,
                ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name,
                ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE.name,
                ChoixStatutPropositionContinue.EN_ATTENTE.name,
                ChoixStatutPropositionContinue.INSCRIPTION_REFUSEE.name,
                ChoixStatutPropositionContinue.ANNULEE_PAR_GESTIONNAIRE.name,
                ChoixStatutPropositionContinue.CLOTUREE.name,
            },
        )

    def test_not_cancelled(self):
        self._test_admission_statuses(
            predicate=continuing.not_cancelled,
            admission=self.admission,
            valid_statuses=set(ChoixStatutPropositionContinue.get_names())
            - {ChoixStatutPropositionContinue.ANNULEE.name},
        )

    def test_is_continuing(self):
        doctorate_admission = DoctorateAdmissionFactory()

        self.assertFalse(
            continuing.is_continuing(
                doctorate_admission.candidate.user,
                doctorate_admission,
            )
        )

        general_admission = GeneralEducationAdmissionFactory()

        self.assertFalse(
            continuing.is_continuing(
                general_admission.candidate.user,
                general_admission,
            )
        )

        self.assertTrue(
            continuing.is_continuing(
                self.admission.candidate.user,
                self.admission,
            )
        )

    def test_in_document_request_status(self):
        self._test_admission_statuses(
            predicate=continuing.in_document_request_status,
            admission=self.admission,
            valid_statuses={ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name},
        )

    def test_in_manager_status(self):
        self._test_admission_statuses(
            predicate=continuing.in_manager_status,
            admission=self.admission,
            valid_statuses={
                ChoixStatutPropositionContinue.CONFIRMEE.name,
                ChoixStatutPropositionContinue.EN_ATTENTE.name,
                ChoixStatutPropositionContinue.INSCRIPTION_REFUSEE.name,
                ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name,
                ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE.name,
                ChoixStatutPropositionContinue.CLOTUREE.name,
                ChoixStatutPropositionContinue.ANNULEE_PAR_GESTIONNAIRE.name,
            },
        )

        user = UserFactory()
        general_admission = GeneralEducationAdmissionFactory(status=ChoixStatutPropositionGenerale.CONFIRMEE.name)
        doctorate_admission = DoctorateAdmissionFactory(status=ChoixStatutPropositionDoctorale.CONFIRMEE.name)
        continuing_admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)

        self.assertFalse(continuing.in_manager_status(user, general_admission))
        self.assertFalse(continuing.in_manager_status(user, doctorate_admission))
        self.assertTrue(continuing.in_manager_status(user, continuing_admission))

    def test_can_request_documents(self):
        self._test_admission_statuses(
            predicate=continuing.can_request_documents,
            admission=self.admission,
            valid_statuses={
                ChoixStatutPropositionContinue.CONFIRMEE.name,
                ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name,
            },
        )

    def test_is_invited_to_complete(self):
        self._test_admission_statuses(
            predicate=continuing.is_invited_to_complete,
            admission=self.admission,
            valid_statuses={ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name},
        )
