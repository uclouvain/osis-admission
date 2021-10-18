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
from django.core.exceptions import ValidationError
from django.test import TestCase

from admission.contrib.models import CommitteeActor
from admission.contrib.models.enums.actor_type import ActorType
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.comittee import MainPromoterFactory, _ProcessFactory
from base.tests.factories.person import PersonFactory


class CommitteeActorTestCase(TestCase):
    def test_unique_main_promoter(self):
        existing = MainPromoterFactory()
        self.assertIsNone(CommitteeActor(
            process=_ProcessFactory(),
            person=PersonFactory(),
            type=ActorType.MAIN_PROMOTER.name,
        ).validate_unique())

        with self.assertRaises(ValidationError):
            CommitteeActor(
                process=existing.process,
                person=PersonFactory(),
                type=ActorType.MAIN_PROMOTER.name,
            ).validate_unique()


class DoctorateAdmissionTestCase(TestCase):
    def test_main_promoter(self):
        request = DoctorateAdmissionFactory()
        self.assertIsNone(request.main_promoter)

        request = DoctorateAdmissionFactory(committee=_ProcessFactory())
        self.assertIsNone(request.main_promoter)

        promoter = MainPromoterFactory()
        request = DoctorateAdmissionFactory(committee=promoter.process)
        self.assertEqual(request.main_promoter, promoter.person)
