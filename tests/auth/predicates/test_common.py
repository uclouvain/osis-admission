# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib.auth.models import User
from django.test import TestCase

from admission.auth.predicates import common
from admission.auth.predicates.common import (
    is_scoped_entity_manager,
    no_candidate_merge_proposal_in_progress,
)
from admission.auth.roles.central_manager import CentralManager
from admission.auth.scope import Scope
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, CentralManagerRoleFactory
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class BasePredicatesTestCase(TestCase):
    def setUp(self):
        self.predicate_context_patcher = mock.patch(
            "rules.Predicate.context",
            new_callable=mock.PropertyMock,
            return_value={'perm_name': 'dummy-perm'},
        )
        self.predicate_context_patcher.start()
        self.addCleanup(self.predicate_context_patcher.stop)


class PredicatesTestCase(BasePredicatesTestCase):
    def test_is_admission_request_author(self):
        candidate1 = CandidateFactory().person
        candidate2 = CandidateFactory().person
        request = DoctorateAdmissionFactory(candidate=candidate1)
        self.assertTrue(common.is_admission_request_author(candidate1.user, request))
        self.assertFalse(common.is_admission_request_author(candidate2.user, request))


class TestIsEntityManager(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector_entity = EntityVersionFactory(acronym='SSH')

        cls.faculty_entity_1 = EntityVersionFactory(acronym='LSM', parent=cls.sector_entity.entity)
        cls.faculty_entity_2 = EntityVersionFactory(acronym='AGRO', parent=cls.sector_entity.entity)
        cls.faculty_entity_3 = EntityVersionFactory(acronym='LOCI', parent=cls.sector_entity.entity)

        cls.school_entity_1 = EntityVersionFactory(acronym='CLSM', parent=cls.faculty_entity_1.entity)

    def setUp(self):
        self.predicate_context_mock = mock.patch(
            "rules.Predicate.context",
            new_callable=mock.PropertyMock,
            return_value={
                'perm_name': 'dummy_perm',
                'role_qs': CentralManager.objects.none(),
            },
        )
        self.mock = self.predicate_context_mock.start()
        self.addCleanup(self.predicate_context_mock.stop)

    def test_is_entity_manager_depending_on_the_training_management_entity(self):
        entity_manager = CentralManagerRoleFactory(
            entity=self.faculty_entity_1.entity,
            scopes=[Scope.GENERAL.name, Scope.DOCTORAT.name, Scope.IUFC.name],
            with_child=False,
        )

        entity_manager_user = entity_manager.person.user

        self.mock.return_value['role_qs'] = CentralManager.objects.filter(person=entity_manager.person)

        # Correct with direct entity
        admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.faculty_entity_1.entity,
        )

        self.assertTrue(is_scoped_entity_manager(entity_manager_user, admission))

        # Wrong with direct entity
        admission.training.management_entity = self.faculty_entity_2.entity
        admission.training.save(update_fields=['management_entity'])
        self.assertFalse(is_scoped_entity_manager(entity_manager_user, admission))

        # Wrong with child entity
        admission.training.management_entity = self.school_entity_1.entity
        admission.training.save(update_fields=['management_entity'])
        self.assertFalse(is_scoped_entity_manager(entity_manager_user, admission))

        # Correct with child entity
        self.mock.return_value['role_qs'] = CentralManager.objects.filter(person=entity_manager.person)
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)

        entity_manager.with_child = True
        entity_manager.save(update_fields=['with_child'])
        self.assertTrue(is_scoped_entity_manager(entity_manager_user, admission))

    def test_is_entity_manager_depending_on_the_scope(self):
        entity_manager = CentralManagerRoleFactory(
            entity=self.faculty_entity_1.entity,
            scopes=[],
            with_child=False,
        )

        other_role = CentralManagerRoleFactory(
            person=entity_manager.person,
            scopes=[Scope.GENERAL.name, Scope.DOCTORAT.name, Scope.IUFC.name],
            with_child=False,
            entity=self.school_entity_1.entity,
        )

        entity_manager_user = entity_manager.person.user

        self.mock.return_value['role_qs'] = CentralManager.objects.filter(person=entity_manager.person)

        # General education admission
        admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.faculty_entity_1.entity,
        )

        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertFalse(is_scoped_entity_manager(entity_manager_user, admission))

        entity_manager.scopes = [Scope.GENERAL.name]
        entity_manager.save(update_fields=['scopes'])
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertTrue(is_scoped_entity_manager(entity_manager_user, admission))

        entity_manager.scopes = [Scope.DOCTORAT.name]
        entity_manager.save(update_fields=['scopes'])
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertFalse(is_scoped_entity_manager(entity_manager_user, admission))

        entity_manager.scopes = [Scope.IUFC.name]
        entity_manager.save(update_fields=['scopes'])
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertFalse(is_scoped_entity_manager(entity_manager_user, admission))

        # Doctorate education admission
        entity_manager.scopes = []
        entity_manager.save(update_fields=['scopes'])
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)

        admission = DoctorateAdmissionFactory(
            training__management_entity=self.faculty_entity_1.entity,
        )

        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertFalse(is_scoped_entity_manager(entity_manager_user, admission))

        entity_manager.scopes = [Scope.GENERAL.name]
        entity_manager.save(update_fields=['scopes'])
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertFalse(is_scoped_entity_manager(entity_manager_user, admission))

        entity_manager.scopes = [Scope.DOCTORAT.name]
        entity_manager.save(update_fields=['scopes'])
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertTrue(is_scoped_entity_manager(entity_manager_user, admission))

        entity_manager.scopes = [Scope.IUFC.name]
        entity_manager.save(update_fields=['scopes'])
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertFalse(is_scoped_entity_manager(entity_manager_user, admission))

        # Continuing education admission
        entity_manager.scopes = []
        entity_manager.save(update_fields=['scopes'])
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)

        admission = ContinuingEducationAdmissionFactory(
            training__management_entity=self.faculty_entity_1.entity,
        )

        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertFalse(is_scoped_entity_manager(entity_manager_user, admission))

        entity_manager.scopes = [Scope.GENERAL.name]
        entity_manager.save(update_fields=['scopes'])
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertFalse(is_scoped_entity_manager(entity_manager_user, admission))

        entity_manager.scopes = [Scope.DOCTORAT.name]
        entity_manager.save(update_fields=['scopes'])
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertFalse(is_scoped_entity_manager(entity_manager_user, admission))

        entity_manager.scopes = [Scope.IUFC.name]
        entity_manager.save(update_fields=['scopes'])
        entity_manager_user = User.objects.get(pk=entity_manager_user.pk)
        self.assertTrue(is_scoped_entity_manager(entity_manager_user, admission))


class NoCandidateMergeProposalInProgressTestCase(BasePredicatesTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admission = GeneralEducationAdmissionFactory()
        cls.user_id = cls.admission.candidate.user.pk
        cls.other_person = PersonFactory()

        cls.default_params = dict(
            status=PersonMergeStatus.PENDING.name,
            last_similarity_result_update=datetime.datetime.now(),
            original_person=cls.admission.candidate,
        )

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=self.user_id)

    def test_without_person_merge_proposal(self):
        result = no_candidate_merge_proposal_in_progress(user_obj=self.user, obj=self.admission)
        self.assertTrue(result)

    def test_with_a_person_merge_proposal_with_the_candidate_as_the_original_person(self):
        PersonMergeProposal.objects.create(**self.default_params)
        result = no_candidate_merge_proposal_in_progress(user_obj=self.user, obj=self.admission)

        self.assertFalse(result)

    def test_with_a_person_merge_proposal_with_the_candidate_as_the_proposal_merge_person(self):
        params = self.default_params.copy()
        params['original_person'] = self.other_person
        params['proposal_merge_person'] = self.admission.candidate

        PersonMergeProposal.objects.create(**params)

        result = no_candidate_merge_proposal_in_progress(user_obj=self.user, obj=self.admission)
        self.assertFalse(result)

    def test_with_various_person_merge_statuses(self):
        merge_proposal = PersonMergeProposal.objects.create(**self.default_params)

        in_progress_statuses = {
            PersonMergeStatus.PENDING,
            PersonMergeStatus.IN_PROGRESS,
        }

        for status in PersonMergeStatus:
            with self.subTest(status=status.value):
                self.user = User.objects.get(pk=self.user_id)
                merge_proposal.status = status.name
                merge_proposal.save(update_fields=['status'])

                result = no_candidate_merge_proposal_in_progress(user_obj=self.user, obj=self.admission)

                if status in in_progress_statuses:
                    self.assertFalse(result)
                else:
                    self.assertTrue(result)
