# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock

from django.test import TestCase
from osis_signature.enums import SignatureState

from admission.auth import predicates
from admission.auth.predicates import (
    unconfirmed_proposition,
    is_enrolled,
    is_being_enrolled,
    confirmation_paper_in_progress,
)
from admission.auth.roles.cdd_manager import CddManager
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixStatutProposition
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, CddManagerFactory, PromoterRoleFactory
from admission.tests.factories.supervision import PromoterFactory as PromoterActorFactory, _ProcessFactory
from base.tests.factories.entity import EntityFactory


class PredicatesTestCase(TestCase):
    def setUp(self):
        self.predicate_context_patcher = mock.patch(
            "rules.Predicate.context", new_callable=mock.PropertyMock, return_value={'perm_name': 'dummy-perm'}
        )
        self.predicate_context_patcher.start()
        self.addCleanup(self.predicate_context_patcher.stop)

    def test_is_admission_request_author(self):
        candidate1 = CandidateFactory().person
        candidate2 = CandidateFactory().person
        request = DoctorateAdmissionFactory(candidate=candidate1)
        self.assertTrue(predicates.is_admission_request_author(candidate1.user, request))
        self.assertFalse(predicates.is_admission_request_author(candidate2.user, request))

    def test_is_main_promoter(self):
        author = CandidateFactory().person
        promoter1 = PromoterRoleFactory()
        promoter2 = PromoterRoleFactory()
        process = _ProcessFactory()
        PromoterActorFactory(actor_ptr__person_id=promoter2.person_id, actor_ptr__process=process)
        request = DoctorateAdmissionFactory(supervision_group=process)
        self.assertFalse(predicates.is_admission_request_promoter(author.user, request))
        self.assertFalse(predicates.is_admission_request_promoter(promoter1.person.user, request))
        self.assertTrue(predicates.is_admission_request_promoter(promoter2.person.user, request))

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
        self.assertTrue(predicates.is_part_of_committee_and_invited(invited_promoter.person.user, request))
        self.assertFalse(predicates.is_part_of_committee_and_invited(approved_promoter.person.user, request))
        self.assertFalse(predicates.is_part_of_committee_and_invited(unknown_promoter.person.user, request))

    def test_is_part_of_doctoral_commission(self):
        doctoral_commission = EntityFactory()
        request = DoctorateAdmissionFactory(doctorate__management_entity=doctoral_commission)
        manager1 = CddManagerFactory(entity=doctoral_commission)
        manager2 = CddManagerFactory()

        self.predicate_context_patcher.target.context['role_qs'] = CddManager.objects.filter(person=manager1.person)
        self.assertTrue(predicates.is_part_of_doctoral_commission(manager1.person.user, request))

        self.predicate_context_patcher.target.context['role_qs'] = CddManager.objects.filter(person=manager2.person)
        self.assertFalse(predicates.is_part_of_doctoral_commission(manager2.person.user, request))

    def test_is_part_of_committee(self):
        # Promoter is part of the supervision group
        promoter = PromoterActorFactory()
        request = DoctorateAdmissionFactory(supervision_group=promoter.process)
        self.assertTrue(predicates.is_part_of_committee(promoter.person.user, request))

    def test_unconfirmed_proposition(self):
        admission = DoctorateAdmissionFactory()

        valid_status = [
            ChoixStatutProposition.IN_PROGRESS.name,
            ChoixStatutProposition.SIGNING_IN_PROGRESS.name,
        ]
        invalid_status = [
            ChoixStatutProposition.CANCELLED.name,
            ChoixStatutProposition.SUBMITTED.name,
            ChoixStatutProposition.ENROLLED.name,
        ]

        for status in valid_status:
            admission.status = status
            self.assertTrue(
                unconfirmed_proposition(admission.candidate.user, admission),
                'This status must be accepted: {}'.format(status),
            )

        for status in invalid_status:
            admission.status = status
            self.assertFalse(
                unconfirmed_proposition(admission.candidate.user, admission),
                'This status must not be accepted: {}'.format(status),
            )

    def test_is_enrolled(self):
        admission = DoctorateAdmissionFactory()

        valid_status = [
            ChoixStatutProposition.ENROLLED.name,
        ]
        invalid_status = [
            ChoixStatutProposition.IN_PROGRESS.name,
            ChoixStatutProposition.SIGNING_IN_PROGRESS.name,
            ChoixStatutProposition.SUBMITTED.name,
            ChoixStatutProposition.CANCELLED.name,
        ]

        for status in valid_status:
            admission.status = status
            self.assertTrue(
                is_enrolled(admission.candidate.user, admission), 'This status must be accepted: {}'.format(status)
            )

        for status in invalid_status:
            admission.status = status
            self.assertFalse(
                is_enrolled(admission.candidate.user, admission), 'This status must not be accepted: {}'.format(status)
            )

    def test_is_being_enrolled(self):
        admission = DoctorateAdmissionFactory()

        valid_status = [
            ChoixStatutProposition.IN_PROGRESS.name,
            ChoixStatutProposition.SIGNING_IN_PROGRESS.name,
            ChoixStatutProposition.SUBMITTED.name,
        ]
        invalid_status = [
            ChoixStatutProposition.ENROLLED.name,
            ChoixStatutProposition.CANCELLED.name,
        ]

        for status in valid_status:
            admission.status = status
            self.assertTrue(
                is_being_enrolled(admission.candidate.user, admission),
                'This status must be accepted: {}'.format(status),
            )

        for status in invalid_status:
            admission.status = status
            self.assertFalse(
                is_being_enrolled(admission.candidate.user, admission),
                'This status must not be accepted: {}'.format(status),
            )

    def test_confirmation_paper_in_progress(self):
        admission = DoctorateAdmissionFactory()

        valid_status = [
            ChoixStatutDoctorat.ADMITTED.name,
            ChoixStatutDoctorat.SUBMITTED_CONFIRMATION.name,
            ChoixStatutDoctorat.CONFIRMATION_TO_BE_REPEATED.name,
        ]
        invalid_status = [
            ChoixStatutDoctorat.ADMISSION_IN_PROGRESS.name,
            ChoixStatutDoctorat.PASSED_CONFIRMATION.name,
            ChoixStatutDoctorat.NOT_ALLOWED_TO_CONTINUE.name,
        ]

        for status in valid_status:
            admission.post_enrolment_status = status
            self.assertTrue(
                confirmation_paper_in_progress(admission.candidate.user, admission),
                'This status must be accepted: {}'.format(status),
            )

        for status in invalid_status:
            admission.post_enrolment_status = status
            self.assertFalse(
                confirmation_paper_in_progress(admission.candidate.user, admission),
                'This status must not be accepted: {}'.format(status),
            )
