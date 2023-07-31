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

from unittest import mock

from django.test import TestCase
from osis_signature.enums import SignatureState

from admission.auth import predicates
from admission.auth.predicates import (
    unconfirmed_proposition,
    is_enrolled,
    is_being_enrolled,
    confirmation_paper_in_progress,
    is_invited_to_complete,
    is_invited_to_pay_after_submission,
    is_invited_to_pay_after_request,
    checklist_is_initialized,
)
from admission.auth.roles.cdd_configurator import CddConfigurator
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, CddConfiguratorFactory, PromoterRoleFactory
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
        request = DoctorateAdmissionFactory(training__management_entity=doctoral_commission)
        manager1 = CddConfiguratorFactory(entity=doctoral_commission)
        manager2 = CddConfiguratorFactory()

        self.predicate_context_patcher.target.context['role_qs'] = CddConfigurator.objects.filter(
            person=manager1.person
        )
        self.assertTrue(predicates.is_part_of_doctoral_commission(manager1.person.user, request))

        self.predicate_context_patcher.target.context['role_qs'] = CddConfigurator.objects.filter(
            person=manager2.person
        )
        self.assertFalse(predicates.is_part_of_doctoral_commission(manager2.person.user, request))

    def test_is_part_of_committee(self):
        # Promoter is part of the supervision group
        promoter = PromoterActorFactory()
        request = DoctorateAdmissionFactory(supervision_group=promoter.process)
        self.assertTrue(predicates.is_part_of_committee(promoter.person.user, request))

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

    def test_is_invited_to_complete(self):
        admission = GeneralEducationAdmissionFactory()

        valid_statuses = {
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
        }

        for status in ChoixStatutPropositionGenerale.get_names():
            admission.status = status
            self.assertEqual(is_invited_to_complete(admission.candidate.user, admission), status in valid_statuses)

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
                is_invited_to_pay_after_submission(
                    admission_with_checklist.candidate.user,
                    admission_with_checklist,
                ),
                status_is_valid,
                f'With checklist, the status "{status}" must{"" if status_is_valid else " not "} be accepted',
            )

            admission_without_checklist.status = status
            self.assertFalse(
                is_invited_to_pay_after_submission(
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
                is_invited_to_pay_after_request(
                    admission_with_checklist.candidate.user,
                    admission_with_checklist,
                ),
                status in valid_statuses,
                f'With checklist, the status "{status}" must{"" if status_is_valid else " not"} be accepted',
            )

            admission_without_checklist.status = status
            self.assertFalse(
                is_invited_to_pay_after_request(
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

    def test_checklist_is_initialized(self):
        admission_without_checklist = GeneralEducationAdmissionFactory(checklist={})
        admission_with_checklist = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        )

        self.assertFalse(
            checklist_is_initialized(
                admission_without_checklist.candidate.user,
                admission_without_checklist,
            ),
        )

        self.assertTrue(
            checklist_is_initialized(
                admission_with_checklist.candidate.user,
                admission_with_checklist,
            ),
        )
