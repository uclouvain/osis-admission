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
from osis_signature.enums import SignatureState

from admission.auth.predicates import doctorate
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE,
    STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_CDD_POUR_DECISION,
)
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, PromoterRoleFactory
from admission.tests.factories.supervision import PromoterFactory as PromoterActorFactory, _ProcessFactory
from base.tests.factories.entity import EntityFactory


class PredicatesTestCase(TestCase):
    def setUp(self):
        self.predicate_context_patcher = mock.patch(
            "rules.Predicate.context",
            new_callable=mock.PropertyMock,
            return_value={'perm_name': 'dummy-perm'},
        )
        self.predicate_context_patcher.start()
        self.addCleanup(self.predicate_context_patcher.stop)

    def test_is_main_promoter(self):
        author = CandidateFactory().person
        promoter1 = PromoterRoleFactory()
        promoter2 = PromoterRoleFactory()
        process = _ProcessFactory()
        PromoterActorFactory(actor_ptr__person_id=promoter2.person_id, actor_ptr__process=process)
        request = DoctorateAdmissionFactory(supervision_group=process)
        self.assertFalse(doctorate.is_admission_request_promoter(author.user, request))
        self.assertFalse(doctorate.is_admission_request_promoter(promoter1.person.user, request))
        self.assertTrue(doctorate.is_admission_request_promoter(promoter2.person.user, request))

    def test_is_part_of_committee_and_invited(self):
        # Create process
        process = _ProcessFactory()

        # Create promoters
        invited_promoter = PromoterActorFactory(process=process)
        invited_promoter.actor_ptr.switch_state(SignatureState.INVITED)
        approved_promoter = PromoterActorFactory(process=process)
        approved_promoter.actor_ptr.switch_state(SignatureState.APPROVED)
        unknown_promoter = PromoterActorFactory()

        # Create admission
        request = DoctorateAdmissionFactory(supervision_group=process)

        # Check predicate
        self.assertTrue(doctorate.is_part_of_committee_and_invited(invited_promoter.person.user, request))
        self.assertFalse(doctorate.is_part_of_committee_and_invited(approved_promoter.person.user, request))
        self.assertFalse(doctorate.is_part_of_committee_and_invited(unknown_promoter.person.user, request))

    def test_is_part_of_committee(self):
        # Promoter is part of the supervision group
        promoter = PromoterActorFactory()
        request = DoctorateAdmissionFactory(supervision_group=promoter.process)
        self.assertTrue(doctorate.is_part_of_committee(promoter.person.user, request))

    def test_unconfirmed_proposition(self):
        admission = DoctorateAdmissionFactory()

        valid_status = [
            ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
        ]
        invalid_status = [
            ChoixStatutPropositionDoctorale.ANNULEE.name,
            ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
        ]

        for status in valid_status:
            admission.status = status
            self.assertTrue(
                doctorate.unconfirmed_proposition(admission.candidate.user, admission),
                'This status must be accepted: {}'.format(status),
            )

        for status in invalid_status:
            admission.status = status
            self.assertFalse(
                doctorate.unconfirmed_proposition(admission.candidate.user, admission),
                'This status must not be accepted: {}'.format(status),
            )

    def test_is_enrolled(self):
        admission = DoctorateAdmissionFactory()

        valid_status = [
            ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
        ]
        invalid_status = [
            ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
            ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            ChoixStatutPropositionDoctorale.ANNULEE.name,
        ]

        for status in valid_status:
            admission.status = status
            self.assertTrue(
                doctorate.is_enrolled(admission.candidate.user, admission),
                'This status must be accepted: {}'.format(status),
            )

        for status in invalid_status:
            admission.status = status
            self.assertFalse(
                doctorate.is_enrolled(admission.candidate.user, admission),
                'This status must not be accepted: {}'.format(status),
            )

    def test_is_being_enrolled(self):
        admission = DoctorateAdmissionFactory()

        valid_status = [
            ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
            ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        ]
        invalid_status = [
            ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
            ChoixStatutPropositionDoctorale.ANNULEE.name,
        ]

        for status in valid_status:
            admission.status = status
            self.assertTrue(
                doctorate.is_being_enrolled(admission.candidate.user, admission),
                'This status must be accepted: {}'.format(status),
            )

        for status in invalid_status:
            admission.status = status
            self.assertFalse(
                doctorate.is_being_enrolled(admission.candidate.user, admission),
                'This status must not be accepted: {}'.format(status),
            )

    def test_is_submitted(self):
        admission = DoctorateAdmissionFactory()

        for status in ChoixStatutPropositionDoctorale.get_names():
            admission.status = status
            self.assertEqual(
                doctorate.is_submitted(admission.candidate.user, admission),
                status in STATUTS_PROPOSITION_DOCTORALE_SOUMISE,
                status,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertFalse(doctorate.is_submitted(continuing_admission.candidate.user, continuing_admission))

        general_admission = GeneralEducationAdmissionFactory(status=ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertFalse(doctorate.is_submitted(general_admission.candidate.user, general_admission))

    def test_not_cancelled(self):
        admission = DoctorateAdmissionFactory()

        for status in ChoixStatutPropositionDoctorale.get_names():
            admission.status = status
            self.assertEqual(
                doctorate.not_cancelled(admission.candidate.user, admission),
                status != ChoixStatutPropositionDoctorale.ANNULEE.name,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertFalse(doctorate.not_cancelled(continuing_admission.candidate.user, continuing_admission))

        general_admission = GeneralEducationAdmissionFactory(status=ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertFalse(doctorate.not_cancelled(general_admission.candidate.user, general_admission))

    def test_in_fac_status(self):
        admission = DoctorateAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC.name,
            ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        }

        for status in ChoixStatutPropositionDoctorale.get_names():
            admission.status = status
            self.assertEqual(
                doctorate.in_fac_status(admission.candidate.user, admission),
                status in valid_statuses,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(
            status=ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name
        )
        self.assertFalse(doctorate.in_fac_status(continuing_admission.candidate.user, continuing_admission))

        general_admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC.name
        )
        self.assertFalse(doctorate.in_fac_status(general_admission.candidate.user, general_admission))

    def test_in_fac_status_extended(self):
        admission = DoctorateAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC.name,
            ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
            ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name,
        }

        for status in ChoixStatutPropositionDoctorale.get_names():
            admission.status = status
            self.assertEqual(
                doctorate.in_fac_status_extended(admission.candidate.user, admission),
                status in valid_statuses,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(
            status=ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name,
        )
        self.assertFalse(doctorate.in_fac_status_extended(continuing_admission.candidate.user, continuing_admission))

        general_admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC.name
        )
        self.assertFalse(doctorate.in_fac_status_extended(general_admission.candidate.user, general_admission))

    def test_in_sic_status(self):
        admission = DoctorateAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name,
            ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name,
            ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION.name,
            ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
            ChoixStatutPropositionDoctorale.INSCRIPTION_REFUSEE.name,
            ChoixStatutPropositionDoctorale.CLOTUREE.name,
        }

        for status in ChoixStatutPropositionDoctorale.get_names():
            admission.status = status
            self.assertEqual(
                doctorate.in_sic_status(admission.candidate.user, admission),
                status in valid_statuses,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertFalse(doctorate.in_sic_status(continuing_admission.candidate.user, continuing_admission))

        general_admission = GeneralEducationAdmissionFactory(status=ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertFalse(doctorate.in_sic_status(general_admission.candidate.user, general_admission))

    def test_in_sic_document_request_status(self):
        admission = DoctorateAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC.name,
        }

        for status in ChoixStatutPropositionDoctorale.get_names():
            admission.status = status
            self.assertEqual(
                doctorate.in_sic_document_request_status(admission.candidate.user, admission),
                status in valid_statuses,
            )

        general_admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
        )
        self.assertFalse(
            doctorate.in_sic_document_request_status(
                general_admission.candidate.user,
                general_admission,
            )
        )

    def test_in_fac_document_request_status(self):
        admission = DoctorateAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name,
        }

        for status in ChoixStatutPropositionDoctorale.get_names():
            admission.status = status
            self.assertEqual(
                doctorate.in_fac_document_request_status(admission.candidate.user, admission),
                status in valid_statuses,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(
            status=ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name,
        )
        self.assertFalse(
            doctorate.in_fac_document_request_status(
                continuing_admission.candidate.user,
                continuing_admission,
            )
        )

        general_admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
        )
        self.assertFalse(
            doctorate.in_fac_document_request_status(
                general_admission.candidate.user,
                general_admission,
            )
        )

    def test_in_sic_status_extended(self):
        admission = DoctorateAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name,
            ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name,
            ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION.name,
            ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
            ChoixStatutPropositionDoctorale.INSCRIPTION_REFUSEE.name,
            ChoixStatutPropositionDoctorale.CLOTUREE.name,
            ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC.name,
        }

        for status in ChoixStatutPropositionDoctorale.get_names():
            admission.status = status
            self.assertEqual(
                doctorate.in_sic_status_extended(admission.candidate.user, admission),
                status in valid_statuses,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertFalse(doctorate.in_sic_status_extended(continuing_admission.candidate.user, continuing_admission))

        general_admission = GeneralEducationAdmissionFactory(status=ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertFalse(doctorate.in_sic_status_extended(general_admission.candidate.user, general_admission))

    def test_can_send_to_fac_faculty_decision(self):
        admission = DoctorateAdmissionFactory()

        for status in ChoixStatutPropositionDoctorale.get_names():
            admission.status = status
            self.assertEqual(
                doctorate.can_send_to_fac_faculty_decision(admission.candidate.user, admission),
                status in STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_CDD_POUR_DECISION,
                status,
            )

        continuing_admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertFalse(
            doctorate.can_send_to_fac_faculty_decision(
                continuing_admission.candidate.user,
                continuing_admission,
            )
        )

        general_admission = GeneralEducationAdmissionFactory(status=ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertFalse(
            doctorate.can_send_to_fac_faculty_decision(
                general_admission.candidate.user,
                general_admission,
            )
        )
