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

from admission.auth import predicates
from admission.auth.roles.cdd_manager import CddManager
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.comittee import MainPromoterFactory
from admission.tests.factories.roles import CandidateFactory, PromoterFactory, CddManagerFactory
from base.tests.factories.entity import EntityFactory
from osis_signature.tests.factories import ProcessFactory


class PredicatesTestCase(TestCase):
    def test_is_admission_request_author(self):
        author1 = CandidateFactory().person
        author2 = CandidateFactory().person
        request = DoctorateAdmissionFactory(author=author1)
        self.assertTrue(predicates.is_admission_request_author(author1.user, request))
        self.assertFalse(predicates.is_admission_request_author(author2.user, request))

    def test_is_main_promoter(self):
        author = CandidateFactory().person
        promoter1 = PromoterFactory()
        promoter2 = PromoterFactory()
        process = ProcessFactory()
        MainPromoterFactory(actor_ptr__person_id=promoter2.person_id, actor_ptr__process=process)
        request = DoctorateAdmissionFactory(committee=process)
        self.assertFalse(predicates.is_admission_request_promoter(author.user, request))
        self.assertFalse(predicates.is_admission_request_promoter(promoter1.person.user, request))
        self.assertTrue(predicates.is_admission_request_promoter(promoter2.person.user, request))

    def test_is_part_of_doctoral_commission(self):
        predicate_context_mock = mock.patch(
            "rules.Predicate.context",
            new_callable=mock.PropertyMock,
            return_value={
                'perm_name': 'dummy-perm'
            }
        )
        predicate_context_mock.start()

        doctoral_commission = EntityFactory()
        request = DoctorateAdmissionFactory(doctoral_commission=doctoral_commission)
        manager1 = CddManagerFactory(entity=doctoral_commission)
        manager2 = CddManagerFactory()

        predicate_context_mock.target.context['role_qs'] = CddManager.objects.filter(person=manager1.person)
        self.assertTrue(predicates.is_part_of_doctoral_commission(manager1.person.user, request))

        predicate_context_mock.target.context['role_qs'] = CddManager.objects.filter(person=manager2.person)
        self.assertFalse(predicates.is_part_of_doctoral_commission(manager2.person.user, request))

        predicate_context_mock.stop()

    def test_is_part_of_committee(self):
        # Promoter is part of the committee
        promoter = MainPromoterFactory()
        request = DoctorateAdmissionFactory(committee=promoter.process)
        self.assertTrue(predicates.is_part_of_committee(promoter.person.user, request))
