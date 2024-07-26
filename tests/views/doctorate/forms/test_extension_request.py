# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
import uuid

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from admission.models import ConfirmationPaper
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.confirmation_paper import ConfirmationPaperFactory
from admission.tests.factories.supervision import PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class DoctorateAdmissionExtensionRequestFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create admissions
        cls.admission_without_confirmation_paper = DoctorateAdmissionFactory(
            training__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=promoter.process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            pre_admission_submission_date=datetime.datetime.now(),
            admitted=True,
        )
        cls.admission_with_confirmation_papers = DoctorateAdmissionFactory(
            training=cls.admission_without_confirmation_paper.training,
            cotutelle=False,
            supervision_group=promoter.process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            pre_admission_submission_date=datetime.datetime.now(),
            admitted=True,
        )

        # User with one cdd
        cls.manager = ProgramManagerFactory(
            education_group=cls.admission_without_confirmation_paper.training.education_group
        ).person.user
        cls.update_path = 'admission:doctorate:update:extension-request'
        cls.read_path = 'admission:doctorate:extension-request'

    def setUp(self):
        self.client.force_login(user=self.manager)
        self.confirmation_paper_with_extension_request = ConfirmationPaperFactory(
            admission=self.admission_with_confirmation_papers,
            confirmation_date=datetime.date(2022, 4, 1),
            confirmation_deadline=datetime.date(2022, 4, 5),
            extended_deadline=datetime.date(2023, 1, 1),
            cdd_opinion='My opinion',
            justification_letter=[],
            brief_justification='My reason',
        )

    def test_get_extension_request_detail_cdd_user_with_unknown_doctorate(self):
        url = reverse(self.update_path, args=[uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_extension_request_detail_cdd_user_without_confirmation_paper(self):
        url = reverse(self.update_path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_extension_request_detail_cdd_user_with_confirmation_paper_with_extension_request(self):
        url = reverse(self.update_path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(
            response.context.get('doctorate').uuid,
            str(self.admission_with_confirmation_papers.uuid),
        )
        self.assertEqual(
            response.context['form'].initial['avis_cdd'],
            'My opinion',
        )

    def test_get_extension_request_detail_cdd_user_with_confirmation_paper_without_extension_request(self):
        self.confirmation_paper_without_extension_request = ConfirmationPaperFactory(
            admission=self.admission_with_confirmation_papers,
            confirmation_date=datetime.date(2022, 6, 1),
            confirmation_deadline=datetime.date(2022, 6, 5),
        )

        url = reverse(self.update_path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(
            response.context.get('doctorate').uuid,
            str(self.admission_with_confirmation_papers.uuid),
        )
        self.assertEqual(response.context['form'].initial, {})

    def test_post_extension_request_detail_cdd_user_with_confirmation_paper_with_extension_request(self):
        url = reverse(self.update_path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.post(url, data={'avis_cdd': 'My new opinion'})

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.admission_with_confirmation_papers.uuid))

        updated_confirmation_paper = ConfirmationPaper.objects.get(
            uuid=self.confirmation_paper_with_extension_request.uuid,
        )
        self.assertEqual(updated_confirmation_paper.cdd_opinion, 'My new opinion')

    def test_post_extension_request_detail_cdd_user_with_confirmation_paper_without_extension_request(self):
        self.confirmation_paper_without_extension_request = ConfirmationPaperFactory(
            admission=self.admission_with_confirmation_papers,
            confirmation_date=datetime.date(2022, 6, 1),
            confirmation_deadline=datetime.date(2022, 6, 5),
        )

        url = reverse(self.update_path, kwargs={'uuid': self.admission_with_confirmation_papers.uuid})

        response = self.client.post(url, data={'avis_cdd': 'My new opinion'})

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(
            response.wsgi_request.path,
            resolve_url(self.update_path, uuid=self.admission_with_confirmation_papers.uuid),
        )
        self.assertFormError(response, 'form', None, ['Demande de prolongation non définie.'])
