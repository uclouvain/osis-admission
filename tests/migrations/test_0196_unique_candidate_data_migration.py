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
from django.test import TestCase

from admission.auth.roles.promoter import Promoter
from admission.migrations.utils.remove_duplicates_candidates import remove_duplicate_candidates
from admission.tests.factories.roles import PromoterRoleFactory


class RemoveDuplicateCandidatesTestCase(TestCase):
    # Note that we use here the Promoter role instead of the Candidate role because it hasn't got the unique constraint

    @classmethod
    def setUpTestData(cls):
        Promoter.objects.all().delete()

    @staticmethod
    def _remove_duplicates():
        remove_duplicate_candidates(Promoter)

    def test_with_no_role(self):
        self._remove_duplicates()
        self.assertFalse(Promoter.objects.exists())

    def test_with_no_duplicate_role(self):
        roles = [PromoterRoleFactory() for _ in range(5)]

        self._remove_duplicates()

        self.assertEqual(Promoter.objects.count(), len(roles))

    def test_with_duplicate_roles(self):
        original_roles = [PromoterRoleFactory() for _ in range(5)]

        # Add duplicate roles
        for _ in range(2):
            Promoter.objects.create(person=original_roles[0].person)
        for _ in range(3):
            Promoter.objects.create(person=original_roles[2].person)
        for _ in range(1):
            Promoter.objects.create(person=original_roles[3].person)

        self.assertEqual(Promoter.objects.all().count(), 11)

        self._remove_duplicates()

        roles_persons_ids = Promoter.objects.all().values_list('person_id', flat=True)

        self.assertCountEqual(roles_persons_ids, [role.person_id for role in original_roles])
