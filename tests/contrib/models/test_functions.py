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

from django.contrib.auth.models import User
from django.db.models import F
from django.test import TestCase

from admission.models.functions import AddMonths
from base.tests.factories.user import UserFactory


class FunctionsTestCase(TestCase):
    def test_add_months(self):
        created_user = UserFactory(
            date_joined=datetime.datetime(2020, 1, 1),
        )
        user = User.objects.annotate(
            date_joined_plus_0_month=AddMonths(F('date_joined'), months=0),
            date_joined_plus_1_month=AddMonths(F('date_joined'), months=1),
            date_joined_plus_5_months=AddMonths(F('date_joined'), months=5),
            date_joined_plus_12_months=AddMonths(F('date_joined'), months=12),
        ).get(pk=created_user.pk)

        self.assertEqual(user.date_joined_plus_0_month, datetime.datetime(2020, 1, 1))
        self.assertEqual(user.date_joined_plus_1_month, datetime.datetime(2020, 2, 1))
        self.assertEqual(user.date_joined_plus_5_months, datetime.datetime(2020, 6, 1))
        self.assertEqual(user.date_joined_plus_12_months, datetime.datetime(2021, 1, 1))
