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
from unittest import mock

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
    RegleDeFinancement,
)
from admission.tests.factories.general_education import (
    GeneralEducationTrainingFactory,
    GeneralEducationAdmissionFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import ProgramManagerRoleFactory, SicManagementRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory


class FinancabiliteChangeStatusViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url = resolve_url(
            'admission:general-education:financability-change-status',
            uuid=cls.general_admission.uuid,
            status=ChoixStatutChecklist.GEST_BLOCAGE.name,
        )

    def test_post(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.checklist['current']['financabilite']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )


@freezegun.freeze_time('2022-01-01')
class FinancabiliteApprovalViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url = resolve_url(
            'admission:general-education:financability-approval',
            uuid=cls.general_admission.uuid,
        )

    def test_post(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            data={'financabilite-financability_rule': RegleDeFinancement.ACQUIS_75_POURCENTS_CREDITS.name},
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.financability_rule,
            RegleDeFinancement.ACQUIS_75_POURCENTS_CREDITS.name,
        )
        self.assertEqual(
            self.general_admission.financability_rule_established_by,
            self.sic_manager_user.person,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['financabilite']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())


class FinancabiliteComputeRuleViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url = resolve_url(
            'admission:general-education:financability-compute-rule',
            uuid=cls.general_admission.uuid,
        )

    def setUp(self) -> None:
        patcher = mock.patch(
            'admission.contrib.models.general_education.GeneralEducationAdmission.update_financability_computed_rule'
        )
        self.update_financability_computed_rule_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_post(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        self.update_financability_computed_rule_mock.assert_called()
