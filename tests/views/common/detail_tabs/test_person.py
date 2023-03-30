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

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from admission.contrib.models import ContinuingEducationAdmission, GeneralEducationAdmission, DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE, ENTITY_CDSS
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, SicManagerRoleFactory, CddManagerFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory


class ContinuingAdmissionPersonDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        cls.sic_manager_user = SicManagerRoleFactory().person.user

        cls.admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_FR,
        )

        cls.url = reverse('admission:continuing-education:person', args=[cls.admission.uuid])

    def test_person_detail_candidate_user(self):
        self.client.force_login(user=self.admission.candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.admission.uuid)
        self.assertEqual(response.context['person'], self.admission.candidate)

    def test_person_detail_other_candidate_user(self):
        self.client.force_login(user=CandidateFactory().person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_person_detail_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.admission.uuid)
        self.assertEqual(response.context['person'], self.admission.candidate)
        self.assertEqual(response.context['contact_language'], _('French'))


class GeneralAdmissionPersonDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        cls.sic_manager_user = SicManagerRoleFactory().person.user

        cls.admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
        )

        cls.url = reverse('admission:general-education:person', args=[cls.admission.uuid])

    def test_person_detail_candidate_user(self):
        self.client.force_login(user=self.admission.candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.admission.uuid)
        self.assertEqual(response.context['person'], self.admission.candidate)

    def test_person_detail_other_candidate_user(self):
        self.client.force_login(user=CandidateFactory().person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_person_detail_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.admission.uuid)
        self.assertEqual(response.context['person'], self.admission.candidate)
        self.assertEqual(response.context['contact_language'], _('English'))


class DoctorateAdmissionPersonDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        cls.cdd_manager = CddManagerFactory(
            entity=first_doctoral_commission,
        )

        cls.sic_manager_user = SicManagerRoleFactory().person.user

        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_FR,
        )

        cls.url = reverse('admission:doctorate:person', args=[cls.admission.uuid])

    def test_person_detail_candidate_user(self):
        self.client.force_login(user=self.admission.candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.admission.uuid)
        self.assertEqual(response.context['person'], self.admission.candidate)

    def test_person_detail_cdd_manager_user(self):
        self.client.force_login(user=self.cdd_manager.person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.admission.uuid)
        self.assertEqual(response.context['person'], self.admission.candidate)

    def test_person_detail_other_candidate_user(self):
        self.client.force_login(user=CandidateFactory().person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_person_detail_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.admission.uuid)
        self.assertEqual(response.context['person'], self.admission.candidate)
        self.assertEqual(response.context['contact_language'], _('French'))
