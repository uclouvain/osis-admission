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
from unittest import mock

from django.test import TestCase

from admission.auth.predicates import continuing
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory


class PredicatesTestCase(TestCase):
    def setUp(self):
        self.predicate_context_patcher = mock.patch(
            "rules.Predicate.context",
            new_callable=mock.PropertyMock,
            return_value={'perm_name': 'dummy-perm'},
        )
        self.predicate_context_patcher.start()
        self.admission.status = ChoixStatutPropositionContinue.EN_BROUILLON.name
        self.admission.submitted_at = None
        self.admission.save(update_fields=['status', 'submitted_at'])
        self.addCleanup(self.predicate_context_patcher.stop)

    @classmethod
    def setUpTestData(cls):
        cls.admission = ContinuingEducationAdmissionFactory()
        cls.general_admission = GeneralEducationAdmissionFactory()
        cls.doctorate_admission = DoctorateAdmissionFactory()

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
        self.admission.submitted_at = None
        self.admission.save(update_fields=['submitted_at'])

        self.assertFalse(continuing.is_submitted(self.admission.candidate.user, self.admission))

        self.admission.submitted_at = datetime.datetime.now()
        self.admission.save(update_fields=['submitted_at'])

        self.assertTrue(continuing.is_submitted(self.admission.candidate.user, self.admission))

        self.general_admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.general_admission.save(update_fields=['status'])

        self.assertFalse(continuing.is_submitted(self.general_admission.candidate.user, self.general_admission))

        self.doctorate_admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.doctorate_admission.save(update_fields=['status'])

        self.assertFalse(continuing.is_submitted(self.doctorate_admission.candidate.user, self.doctorate_admission))

    def test_not_cancelled(self):
        self._test_admission_statuses(
            predicate=continuing.not_cancelled,
            admission=self.admission,
            valid_statuses=set(ChoixStatutPropositionContinue.get_names())
            - {ChoixStatutPropositionContinue.ANNULEE.name},
        )

        self.general_admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.general_admission.save(update_fields=['status'])

        self.assertFalse(continuing.not_cancelled(self.general_admission.candidate.user, self.general_admission))

        self.doctorate_admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.doctorate_admission.save(update_fields=['status'])

        self.assertFalse(continuing.not_cancelled(self.doctorate_admission.candidate.user, self.doctorate_admission))

    def test_is_submitted_or_not_cancelled(self):
        # Not submitted
        self.admission.submitted_at = None
        self.admission.save(update_fields=['submitted_at'])

        self._test_admission_statuses(
            predicate=continuing.is_submitted_or_not_cancelled,
            admission=self.admission,
            valid_statuses=set(ChoixStatutPropositionContinue.get_names())
            - {ChoixStatutPropositionContinue.ANNULEE.name},
        )

        # Submitted
        self.admission.submitted_at = datetime.datetime.now()
        self.admission.save(update_fields=['submitted_at'])

        self._test_admission_statuses(
            predicate=continuing.is_submitted_or_not_cancelled,
            admission=self.admission,
            valid_statuses=set(ChoixStatutPropositionContinue.get_names()),
        )

        doctorate_admission = DoctorateAdmissionFactory(
            submitted_at=None,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        self.assertFalse(
            continuing.is_submitted_or_not_cancelled(
                doctorate_admission.candidate.user,
                doctorate_admission,
            )
        )

        general_admission = GeneralEducationAdmissionFactory(
            submitted_at=None,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        self.assertFalse(
            continuing.is_submitted_or_not_cancelled(
                general_admission.candidate.user,
                general_admission,
            )
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

        self.general_admission.status = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name
        self.general_admission.save(update_fields=['status'])

        self.assertFalse(continuing.not_cancelled(self.general_admission.candidate.user, self.general_admission))

        self.doctorate_admission.status = ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name
        self.doctorate_admission.save(update_fields=['status'])

        self.assertFalse(continuing.not_cancelled(self.doctorate_admission.candidate.user, self.doctorate_admission))

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
            },
        )

        self.general_admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.general_admission.save(update_fields=['status'])

        self.assertFalse(continuing.in_manager_status(self.general_admission.candidate, self.general_admission))

        self.doctorate_admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.doctorate_admission.save(update_fields=['status'])

        self.assertFalse(continuing.in_manager_status(self.doctorate_admission.candidate, self.doctorate_admission))

    def test_can_request_documents(self):
        self._test_admission_statuses(
            predicate=continuing.can_request_documents,
            admission=self.admission,
            valid_statuses={
                ChoixStatutPropositionContinue.CONFIRMEE.name,
                ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name,
            },
        )

        self.general_admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.general_admission.save(update_fields=['status'])

        self.assertFalse(continuing.in_manager_status(self.general_admission.candidate, self.general_admission))

        self.doctorate_admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.doctorate_admission.save(update_fields=['status'])

        self.assertFalse(continuing.in_manager_status(self.doctorate_admission.candidate, self.doctorate_admission))

    def test_is_invited_to_complete(self):
        self._test_admission_statuses(
            predicate=continuing.is_invited_to_complete,
            admission=self.admission,
            valid_statuses={ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name},
        )
