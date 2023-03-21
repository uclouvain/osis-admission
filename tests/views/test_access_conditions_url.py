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

import freezegun
from django.test import TestCase
from django.urls import reverse

from admission.tests import QueriesAssertionsMixin
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import SicManagerRoleFactory


@freezegun.freeze_time('2023-01-01')
class AdmissionAccessConditionsURLTestCase(QueriesAssertionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctorate_admission = DoctorateAdmissionFactory()

        cls.sic_manager_user = SicManagerRoleFactory().person.user

        # Targeted url
        cls.conditions_url = 'admission:access-conditions-url'

    def test_access_conditions_url_with_a_doctorate(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(
            reverse(
                '%s' % self.conditions_url,
                kwargs={
                    'training_type': self.doctorate_admission.training.education_group_type.name,
                    'training_acronym': self.doctorate_admission.training.acronym,
                    'partial_training_acronym': self.doctorate_admission.training.partial_acronym,
                },
            )
        )

        self.assertRedirects(
            response=response,
            expected_url='https://uclouvain.be/fr/etudier/inscriptions/conditions-doctorats.html',
            status_code=302,
            fetch_redirect_response=False,
        )
