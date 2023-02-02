# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE, ENTITY_CDSS
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.tests.exports.test_admission_recap import BaseAdmissionRecapTestCaseMixin
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CddManagerFactory
from admission.tests.factories.supervision import PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DoctorateAdmissionPDFRecapExportViewTestCase(BaseAdmissionRecapTestCaseMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # Entities
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)
        second_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=second_doctoral_commission, acronym=ENTITY_CDSS)

        # Create admissions
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=PromoterFactory().process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            pre_admission_submission_date=datetime.datetime.now(),
            admitted=True,
        )

        cls.candidate = cls.admission.candidate

        # User with one cdd
        cls.cdd_person = CddManagerFactory(entity=first_doctoral_commission).person
        cls.other_cdd_person = CddManagerFactory(entity=second_doctoral_commission).person

        # Targeted path
        cls.url = resolve_url("admission:doctorate:pdf-recap", uuid=cls.admission.uuid)
        cls.unknown_doctorate_url = resolve_url("admission:doctorate:pdf-recap", uuid=uuid.uuid4())

    def test_pdf_recap_export_other_cdd_user_is_forbidden(self):
        self.client.force_login(user=self.other_cdd_person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_pdf_recap_export_cdd_user_with_unknown_doctorate_returns_not_found(self):
        self.client.force_login(user=self.cdd_person.user)
        response = self.client.get(self.unknown_doctorate_url)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_pdf_recap_export_cdd_user_redirects_to_file_url(self):
        self.client.force_login(user=self.cdd_person.user)
        response = self.client.get(self.url)
        self.assertRedirects(response, 'http://dummyurl/file/pdf-token', fetch_redirect_response=False)
