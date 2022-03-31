# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List

from django.test import TestCase
from django.urls import reverse

from admission.contrib.models import DoctorateAdmission
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixStatutProposition, ChoixTypeAdmission
from admission.ddd.projet_doctoral.preparation.domain.model._financement import (
    ChoixTypeFinancement,
    BourseRecherche,
    ChoixTypeContratTravail,
)
from admission.ddd.projet_doctoral.preparation.domain.model.doctorat import ENTITY_CDE, ENTITY_CDSS
from admission.ddd.projet_doctoral.validation.domain.model._enums import ChoixStatutCDD, ChoixStatutSIC
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, CddManagerFactory
from admission.tests.factories.supervision import PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from reference.tests.factories.country import CountryFactory


class CddDoctorateAdmissionProjectDetailViewTestCase(TestCase):
    admissions = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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
        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create admissions
        cls.admissions: List[DoctorateAdmission] = [
            DoctorateAdmissionFactory(
                doctorate__management_entity=first_doctoral_commission,
                doctorate__academic_year=academic_years[0],
                cotutelle=False,
                supervision_group=promoter.process,
                financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
                financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
                type=ChoixTypeAdmission.PRE_ADMISSION.name,
                pre_admission_submission_date=datetime.datetime.now(),
            ),
            DoctorateAdmissionFactory(
                doctorate__management_entity=first_doctoral_commission,
                doctorate__academic_year=academic_years[0],
                status=ChoixStatutProposition.SUBMITTED.name,
                candidate=candidate.person,
                financing_type=ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
                scholarship_grant=BourseRecherche.ARC.name,
                financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
                type=ChoixTypeAdmission.ADMISSION.name,
                admission_submission_date=datetime.datetime.now(),
                status_cdd=ChoixStatutCDD.TO_BE_VERIFIED.name,
                status_sic=ChoixStatutSIC.VALID.name,
            ),
            DoctorateAdmissionFactory(
                doctorate__management_entity=second_doctoral_commission,
                doctorate__academic_year=academic_years[0],
            ),
        ]

        # User with one cdd
        cdd_person_user = CddManagerFactory(entity=first_doctoral_commission).person
        cls.one_cdd_user = cdd_person_user.user

    def test_project_detail_candidate_user(self):
        self.client.force_login(user=self.admissions[0].candidate.user)

        url = reverse('admission:doctorate:cdd:project', args=[self.admissions[0].uuid])

        response = self.client.get(url)

        response.status_code = 403

    def test_project_detail_cdd_user_admission(self):
        self.client.force_login(user=self.one_cdd_user)

        url = reverse('admission:doctorate:cdd:project', args=[self.admissions[0].uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context.get('admission'))
        self.assertIsNone(response.context.get('folder'))

    def test_project_detail_cdd_user_folder(self):
        self.client.force_login(user=self.one_cdd_user)

        url = reverse('admission:doctorate:cdd:project', args=[self.admissions[1].uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context.get('admission'))
        self.assertIsNotNone(response.context.get('dossier'))
