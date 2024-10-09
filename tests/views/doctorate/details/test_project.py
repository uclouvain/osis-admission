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
import datetime
from typing import List

from django.test import TestCase
from django.urls import reverse

from admission.contrib.models import AdmissionViewer, DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE, ENTITY_CDSS
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    BourseRecherche,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD, ChoixStatutSIC
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import (
    CandidateFactory,
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from reference.tests.factories.country import CountryFactory


class DoctorateAdmissionProjectDetailViewTestCase(TestCase):
    admissions = []

    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        second_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=second_doctoral_commission, acronym=ENTITY_CDSS)

        candidate = CandidateFactory(
            person__country_of_citizenship=CountryFactory(
                iso_code='be',
                name='Belgique',
                name_en='Belgium',
            )
        )
        # Create admissions
        admission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            submitted_at=datetime.datetime.now(),
        )
        cls.admissions: List[DoctorateAdmission] = [
            admission,
            DoctorateAdmissionFactory(
                training=admission.training,
                status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
                candidate=candidate.person,
                financing_type=ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
                other_international_scholarship=BourseRecherche.ARC.name,
                financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
                type=ChoixTypeAdmission.ADMISSION.name,
                submitted_at=datetime.datetime.now(),
                status_cdd=ChoixStatutCDD.TO_BE_VERIFIED.name,
                status_sic=ChoixStatutSIC.VALID.name,
                submitted_profile={
                    "coordinates": {
                        "city": "Louvain-La-Neuves",
                        "email": "user@uclouvain.be",
                        "place": "",
                        "street": "Place de l'Université",
                        "country": "BE",
                        "postal_box": "",
                        "postal_code": "1348",
                        "street_number": "2",
                    },
                    "identification": {
                        "gender": "M",
                        "last_name": "Doe",
                        "first_name": "John",
                        "country_of_citizenship": "BE",
                    },
                },
            ),
            DoctorateAdmissionFactory(
                training__management_entity=second_doctoral_commission,
                training__academic_year=academic_years[0],
            ),
        ]

        cls.sic_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.manager = ProgramManagerRoleFactory(education_group=admission.training.education_group).person.user

    def test_project_detail_manager_admission(self):
        self.client.force_login(user=self.manager)

        url = reverse('admission:doctorate:project', args=[self.admissions[0].uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context.get('admission'))
        self.assertIsNone(response.context.get('folder'))

    def test_project_detail_manager_folder(self):
        self.client.force_login(user=self.manager)

        url = reverse('admission:doctorate:project', args=[self.admissions[1].uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context.get('admission'))

    def test_project_detail_with_sic(self):
        self.client.force_login(user=self.sic_user)

        self.assertFalse(
            AdmissionViewer.objects.filter(
                admission=self.admissions[0],
                person=self.sic_user.person,
            ).exists()
        )

        url = reverse('admission:doctorate:project', args=[self.admissions[0].uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            AdmissionViewer.objects.filter(
                admission=self.admissions[0],
                person=self.sic_user.person,
            ).exists()
        )
