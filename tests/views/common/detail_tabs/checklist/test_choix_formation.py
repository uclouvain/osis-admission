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
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    PoursuiteDeCycle,
)
from admission.tests.factories.general_education import (
    GeneralEducationTrainingFactory,
    GeneralEducationAdmissionFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory


class ChoixFormationDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )
        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user

        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def test_get_htmx(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:choix-formation-detail',
            uuid=self.general_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('admission', response.context)

    def test_get_without_htmx(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:choix-formation-detail',
            uuid=self.general_admission.uuid,
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)


class ChoixFormationFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
            education_group_type__name=TrainingType.BACHELOR.name,
        )
        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            cycle_pursuit=PoursuiteDeCycle.TO_BE_DETERMINED.name,
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user

        cls.data = {
            'type_demande': 'ADMISSION',
            'annee_academique': cls.training.academic_year.year,
            'formation': cls.training.acronym,
            'poursuite_cycle': 'YES',
        }

        cls.default_headers = {'HTTP_HX-Request': 'true'}

        cls.url_namespace = 'admission:general-education:choix-formation-update'
        cls.url = resolve_url(cls.url_namespace, uuid=cls.general_admission.uuid)

    def test_get_htmx(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_post_htmx_with_bachelor(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, data=self.data, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Refresh'], 'true')

        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.cycle_pursuit, 'YES')

    def test_get_without_htmx(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_post_without_htmx_with_bachelor(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)

    def test_post_with_master(self):
        self.client.force_login(user=self.sic_manager_user)

        master_training = GeneralEducationTrainingFactory(
            management_entity=self.first_doctoral_commission,
            academic_year=self.academic_years[0],
            education_group_type__name=TrainingType.MASTER_MD_120.name,
        )
        master_general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=master_training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            cycle_pursuit=PoursuiteDeCycle.YES.name,
        )

        response = self.client.post(
            resolve_url(self.url_namespace, uuid=master_general_admission.uuid),
            data={
                'type_demande': 'ADMISSION',
                'annee_academique': master_training.academic_year.year,
                'formation': master_training.acronym,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        master_general_admission.refresh_from_db()
        self.assertEqual(master_general_admission.cycle_pursuit, PoursuiteDeCycle.TO_BE_DETERMINED.name)

        master_general_admission.cycle_pursuit = PoursuiteDeCycle.YES.name
        master_general_admission.save()

        response = self.client.post(
            resolve_url(self.url_namespace, uuid=master_general_admission.uuid),
            data={
                'type_demande': 'ADMISSION',
                'annee_academique': master_training.academic_year.year,
                'formation': master_training.acronym,
                'poursuite_cycle': PoursuiteDeCycle.NO.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        master_general_admission.refresh_from_db()
        self.assertEqual(master_general_admission.cycle_pursuit, PoursuiteDeCycle.TO_BE_DETERMINED.name)

    def test_post_with_bachelor(self):
        self.client.force_login(user=self.sic_manager_user)

        bachelor_training = GeneralEducationTrainingFactory(
            management_entity=self.first_doctoral_commission,
            academic_year=self.academic_years[0],
            education_group_type__name=TrainingType.BACHELOR.name,
        )
        bachelor_general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=bachelor_training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            cycle_pursuit=PoursuiteDeCycle.YES.name,
        )

        response = self.client.post(
            resolve_url(self.url_namespace, uuid=bachelor_general_admission.uuid),
            data={
                'type_demande': 'ADMISSION',
                'annee_academique': bachelor_training.academic_year.year,
                'formation': bachelor_training.acronym,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('poursuite_cycle', []))

        bachelor_general_admission.refresh_from_db()
        self.assertEqual(bachelor_general_admission.cycle_pursuit, PoursuiteDeCycle.YES.name)

        response = self.client.post(
            resolve_url(self.url_namespace, uuid=bachelor_general_admission.uuid),
            data={
                'type_demande': 'ADMISSION',
                'annee_academique': bachelor_training.academic_year.year,
                'formation': bachelor_training.acronym,
                'poursuite_cycle': PoursuiteDeCycle.NO.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        bachelor_general_admission.refresh_from_db()
        self.assertEqual(bachelor_general_admission.cycle_pursuit, PoursuiteDeCycle.NO.name)
