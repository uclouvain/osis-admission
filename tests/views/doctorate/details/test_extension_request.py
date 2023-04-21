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

import datetime

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.confirmation_paper import ConfirmationPaperFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory


class DoctorateAdmissionExtensionRequestDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # Create admissions
        cls.admission_without_confirmation_paper = DoctorateAdmissionFactory(
            training__academic_year=academic_years[0],
            admitted=True,
        )
        cls.admission_with_confirmation_papers = DoctorateAdmissionFactory(
            training=cls.admission_without_confirmation_paper.training,
            admitted=True,
        )

        # User with one cdd
        cls.cdd_person = ProgramManagerFactory(
            education_group=cls.admission_without_confirmation_paper.training.education_group
        ).person
        cls.detail_path = 'admission:doctorate:extension-request'

    def setUp(self):
        self.client.force_login(user=self.cdd_person.user)
        self.confirmation_paper_with_extension_request = ConfirmationPaperFactory(
            admission=self.admission_with_confirmation_papers,
            confirmation_date=datetime.date(2022, 4, 1),
            confirmation_deadline=datetime.date(2022, 4, 5),
            extended_deadline=datetime.date(2023, 1, 1),
            cdd_opinion='My opinion',
            justification_letter=[],
            brief_justification='My reason',
        )

    def test_extension_request_detail_cdd_user_without_confirmation_paper(self):
        url = reverse(self.detail_path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_extension_request_detail_cdd_user_with_confirmation_paper(self):
        url = reverse(self.detail_path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.context.get('doctorate').uuid,
            str(self.admission_with_confirmation_papers.uuid),
        )
        self.assertEqual(
            response.context.get('confirmation_paper').uuid,
            str(self.confirmation_paper_with_extension_request.uuid),
        )
