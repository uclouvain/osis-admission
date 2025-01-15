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

from django.conf import settings
from django.test import TestCase
from django.utils import translation

from admission.auth.predicates import general, not_in_general_statuses_predicate_message
from admission.auth.predicates.general import is_invited_to_pay_after_request
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
    STATUTS_PROPOSITION_GENERALE_SOUMISE,
    STATUTS_PROPOSITION_GENERALE_ENVOYABLE_EN_FAC_POUR_DECISION,
)
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
        self.addCleanup(self.predicate_context_patcher.stop)

    def test_is_invited_to_complete(self):
        admission = GeneralEducationAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
        }

        for status in ChoixStatutPropositionGenerale.get_names():
            admission.status = status
            self.assertEqual(
                general.is_invited_to_complete(admission.candidate.user, admission),
                status in valid_statuses,
            )

    def test_is_invited_to_pay_after_submission(self):
        admission_without_checklist = GeneralEducationAdmissionFactory(checklist={})
        admission_with_checklist = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        )
        admission_with_checklist.checklist['current']['frais_dossier'] = {
            'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
            'extra': {'initial': '1'},
        }
        admission_with_checklist.save()

        # The checklist must be initialized and the status must be one of the following
        valid_statuses = {
            ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        }

        for status in ChoixStatutPropositionGenerale.get_names():
            admission_with_checklist.status = status
            status_is_valid = status in valid_statuses
            self.assertEqual(
                general.is_invited_to_pay_after_submission(
                    admission_with_checklist.candidate.user,
                    admission_with_checklist,
                ),
                status_is_valid,
                f'With checklist, the status "{status}" must{"" if status_is_valid else " not "} be accepted',
            )

            admission_without_checklist.status = status
            self.assertFalse(
                general.is_invited_to_pay_after_submission(
                    admission_without_checklist.candidate.user,
                    admission_without_checklist,
                ),
                f'With checklist, the status "{status}" must not be accepted',
            )

    def test_is_invited_to_pay_after_request(self):
        admission_without_checklist = GeneralEducationAdmissionFactory(checklist={})
        admission_just_submitted = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        )
        admission_just_submitted.checklist['current']['frais_dossier'] = {
            'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
            'extra': {'initial': '1'},
        }
        admission_with_checklist = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        )
        admission_with_checklist.checklist['current']['frais_dossier'] = {
            'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
        }

        # The checklist must be initialized and the status must be one of the following
        valid_statuses = {
            ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        }

        for status in ChoixStatutPropositionGenerale.get_names():
            admission_with_checklist.status = status
            status_is_valid = status in valid_statuses
            self.assertEqual(
                general.is_invited_to_pay_after_request(
                    admission_with_checklist.candidate.user,
                    admission_with_checklist,
                ),
                status in valid_statuses,
                f'With checklist, the status "{status}" must{"" if status_is_valid else " not"} be accepted',
            )

            admission_without_checklist.status = status
            self.assertFalse(
                general.is_invited_to_pay_after_request(
                    admission_without_checklist.candidate.user,
                    admission_without_checklist,
                ),
                'Without checklist, this status must not be accepted: {}'.format(status),
            )
            admission_just_submitted.status = status
            self.assertFalse(
                is_invited_to_pay_after_request(
                    admission_just_submitted.candidate.user,
                    admission_just_submitted,
                ),
                'Just after submission, this status must not be accepted: {}'.format(status),
            )

    def test_in_fac_status(self):
        admission = GeneralEducationAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC.name,
            ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name,
        }

        for status in ChoixStatutPropositionGenerale.get_names():
            admission.status = status
            self.assertEqual(
                general.in_fac_status(admission.candidate.user, admission),
                status in valid_statuses,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(
            status=ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name
        )
        self.assertFalse(general.in_fac_status(continuing_admission.candidate.user, continuing_admission))

        doctorate_admission = DoctorateAdmissionFactory(status=ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC.name)
        self.assertFalse(general.in_fac_status(doctorate_admission.candidate.user, doctorate_admission))

    def test_in_fac_document_request_status(self):
        admission = GeneralEducationAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
        }

        for status in ChoixStatutPropositionGenerale.get_names():
            admission.status = status
            self.assertEqual(
                general.in_fac_document_request_status(admission.candidate.user, admission),
                status in valid_statuses,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(
            status=ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name,
        )
        self.assertFalse(
            general.in_fac_document_request_status(
                continuing_admission.candidate.user,
                continuing_admission,
            )
        )

        doctorate_admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name,
        )
        self.assertFalse(
            general.in_fac_document_request_status(
                doctorate_admission.candidate.user,
                doctorate_admission,
            )
        )

    def test_in_sic_document_request_status(self):
        admission = GeneralEducationAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
        }

        for status in ChoixStatutPropositionGenerale.get_names():
            admission.status = status
            self.assertEqual(
                general.in_sic_document_request_status(admission.candidate.user, admission),
                status in valid_statuses,
            )

        doctorate_admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC.name,
        )
        self.assertFalse(
            general.in_sic_document_request_status(
                doctorate_admission.candidate.user,
                doctorate_admission,
            )
        )

    def test_in_fac_status_extended(self):
        admission = GeneralEducationAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC.name,
            ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name,
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
        }

        for status in ChoixStatutPropositionGenerale.get_names():
            admission.status = status
            self.assertEqual(
                general.in_fac_status_extended(admission.candidate.user, admission),
                status in valid_statuses,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(
            status=ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name,
        )
        self.assertFalse(general.in_fac_status_extended(continuing_admission.candidate.user, continuing_admission))

        doctorate_admission = DoctorateAdmissionFactory(status=ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC.name)
        self.assertFalse(general.in_fac_status_extended(doctorate_admission.candidate.user, doctorate_admission))

    def test_in_sic_status(self):
        admission = GeneralEducationAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionGenerale.CONFIRMEE.name,
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name,
            ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name,
            ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name,
            ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
            ChoixStatutPropositionGenerale.INSCRIPTION_REFUSEE.name,
            ChoixStatutPropositionGenerale.CLOTUREE.name,
        }

        for status in ChoixStatutPropositionGenerale.get_names():
            admission.status = status
            self.assertEqual(
                general.in_sic_status(admission.candidate.user, admission),
                status in valid_statuses,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertFalse(general.in_sic_status(continuing_admission.candidate.user, continuing_admission))

        doctorate_admission = DoctorateAdmissionFactory(status=ChoixStatutPropositionDoctorale.CONFIRMEE.name)
        self.assertFalse(general.in_sic_status(doctorate_admission.candidate.user, doctorate_admission))

    def test_not_cancelled(self):
        admission = GeneralEducationAdmissionFactory()

        for status in ChoixStatutPropositionGenerale.get_names():
            admission.status = status
            self.assertEqual(
                general.not_cancelled(admission.candidate.user, admission),
                status != ChoixStatutPropositionGenerale.ANNULEE.name,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertFalse(general.not_cancelled(continuing_admission.candidate.user, continuing_admission))

        doctorate_admission = DoctorateAdmissionFactory(status=ChoixStatutPropositionDoctorale.CONFIRMEE.name)
        self.assertFalse(general.not_cancelled(doctorate_admission.candidate.user, doctorate_admission))

    def test_in_sic_status_extended(self):
        admission = GeneralEducationAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionGenerale.CONFIRMEE.name,
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name,
            ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name,
            ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name,
            ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
            ChoixStatutPropositionGenerale.INSCRIPTION_REFUSEE.name,
            ChoixStatutPropositionGenerale.CLOTUREE.name,
            ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
        }

        for status in ChoixStatutPropositionGenerale.get_names():
            admission.status = status
            self.assertEqual(
                general.in_sic_status_extended(admission.candidate.user, admission),
                status in valid_statuses,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertFalse(general.in_sic_status_extended(continuing_admission.candidate.user, continuing_admission))

        doctorate_admission = DoctorateAdmissionFactory(status=ChoixStatutPropositionDoctorale.CONFIRMEE.name)
        self.assertFalse(general.in_sic_status_extended(doctorate_admission.candidate.user, doctorate_admission))

    def test_is_submitted(self):
        admission = GeneralEducationAdmissionFactory()

        for status in ChoixStatutPropositionGenerale.get_names():
            admission.status = status
            self.assertEqual(
                general.is_submitted(admission.candidate.user, admission),
                status in STATUTS_PROPOSITION_GENERALE_SOUMISE,
                status,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertFalse(general.is_submitted(continuing_admission.candidate.user, continuing_admission))

        doctorate_admission = DoctorateAdmissionFactory(status=ChoixStatutPropositionDoctorale.CONFIRMEE.name)
        self.assertFalse(general.is_submitted(doctorate_admission.candidate.user, doctorate_admission))

    def test_not_in_general_statuses_predicate_message_in_english(self):
        with translation.override(settings.LANGUAGE_CODE_EN):
            result = not_in_general_statuses_predicate_message(
                statuses=[
                    ChoixStatutPropositionGenerale.CONFIRMEE.name,
                    ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
                ]
            )
            self.assertEqual(
                result,
                'The global status of the application must be one of the following in order to realize this action: '
                'Application confirmed, To be completed for the Enrolment Office (SIC).',
            )

    def test_not_in_general_statuses_predicate_message_in_french(self):
        with translation.override(settings.LANGUAGE_CODE_FR):
            result = not_in_general_statuses_predicate_message(
                statuses=[
                    ChoixStatutPropositionGenerale.CONFIRMEE.name,
                    ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
                ]
            )
            self.assertEqual(
                result,
                'Le statut global de la demande doit être l\'un des suivants pour pouvoir réaliser cette action : '
                'Demande confirmée, A compléter pour SIC.',
            )

    def test_is_general(self):
        doctorate_admission = DoctorateAdmissionFactory()
        self.assertFalse(general.is_general(doctorate_admission.candidate.user, doctorate_admission))

        continuing_admission = ContinuingEducationAdmissionFactory()
        self.assertFalse(general.is_general(continuing_admission.candidate.user, continuing_admission))

        general_admission = GeneralEducationAdmissionFactory()
        self.assertTrue(general.is_general(general_admission.candidate.user, general_admission))

    def test_can_send_to_fac_faculty_decision(self):
        admission = GeneralEducationAdmissionFactory()

        for status in ChoixStatutPropositionGenerale.get_names():
            admission.status = status
            self.assertEqual(
                general.can_send_to_fac_faculty_decision(admission.candidate.user, admission),
                status in STATUTS_PROPOSITION_GENERALE_ENVOYABLE_EN_FAC_POUR_DECISION,
                status,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertFalse(
            general.can_send_to_fac_faculty_decision(
                continuing_admission.candidate.user,
                continuing_admission,
            )
        )

        doctorate_admission = DoctorateAdmissionFactory(status=ChoixStatutPropositionDoctorale.CONFIRMEE.name)
        self.assertFalse(
            general.can_send_to_fac_faculty_decision(
                doctorate_admission.candidate.user,
                doctorate_admission,
            )
        )
