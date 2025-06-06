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

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils import timezone

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    DerogationFinancement,
)
from admission.models import DoctorateAdmission
from admission.tests import OsisDocumentMockTestMixin
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.faculty_decision import DoctorateRefusalReasonFactory
from admission.tests.factories.form_item import AdmissionFormItemFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from ddd.logic.financabilite.domain.model.enums.situation import SituationFinancabilite
from infrastructure.financabilite.domain.service.financabilite import PASS_ET_LAS_LABEL


# @override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class FinancabiliteChangeStatusViewTestCase(OsisDocumentMockTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            submitted=True,
            financability_rule=SituationFinancabilite.PLUS_FINANCABLE.name,
            financability_established_by=CompletePersonFactory(),
        )
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url = resolve_url(
            'admission:doctorate:financability-change-status',
            uuid=cls.admission.uuid,
            status=ChoixStatutChecklist.GEST_BLOCAGE.name,
        )

    def test_post(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.checklist['current']['financabilite']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(self.admission.financability_rule, '')
        self.assertIsNone(self.admission.financability_established_by)


@freezegun.freeze_time('2022-01-01')
class FinancabiliteApprovalSetRuleViewTestCase(OsisDocumentMockTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            submitted=True,
            specific_question_answers={str(AdmissionFormItemFactory(internal_label=PASS_ET_LAS_LABEL).uuid): 0},
        )
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url = resolve_url(
            'admission:doctorate:financability-approval-set-rule',
            uuid=cls.admission.uuid,
        )

    def test_post(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            data={
                'financabilite-approval-financability_rule': SituationFinancabilite.ACQUIS_100_POURCENT_EN_N_MOINS_1.name
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get("HX-Refresh"))
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.financability_rule,
            SituationFinancabilite.ACQUIS_100_POURCENT_EN_N_MOINS_1.name,
        )
        self.assertEqual(
            self.admission.financability_established_by,
            self.sic_manager_user.person,
        )
        self.assertEqual(
            self.admission.checklist['current']['financabilite']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())


@freezegun.freeze_time('2022-01-01')
class FinancabiliteApprovalViewTestCase(OsisDocumentMockTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            submitted=True,
            financability_computed_rule=EtatFinancabilite.FINANCABLE.name,
            financability_computed_rule_situation=SituationFinancabilite.FINANCABLE_D_OFFICE.name,
            financability_computed_rule_on=timezone.now(),
            specific_question_answers={str(AdmissionFormItemFactory(internal_label=PASS_ET_LAS_LABEL).uuid): 0},
        )
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url = resolve_url(
            'admission:doctorate:financability-approval',
            uuid=cls.admission.uuid,
        )

    def test_post(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.financability_rule,
            SituationFinancabilite.FINANCABLE_D_OFFICE.name,
        )
        self.assertEqual(
            self.admission.financability_established_by,
            self.sic_manager_user.person,
        )
        self.assertEqual(
            self.admission.checklist['current']['financabilite']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

    def test_post_with_faculty_manager(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(
            self.url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 403)


@freezegun.freeze_time('2022-01-01')
class FinancabiliteNotFinanceableSetRuleViewTestCase(OsisDocumentMockTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            specific_question_answers={str(AdmissionFormItemFactory(internal_label=PASS_ET_LAS_LABEL).uuid): 0},
        )
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url = resolve_url(
            'admission:doctorate:financability-not-financeable-set-rule',
            uuid=cls.admission.uuid,
        )

    def test_post(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            data={'financabilite-not-financeable-financability_rule': SituationFinancabilite.PLUS_FINANCABLE.name},
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get("HX-Refresh"))
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.financability_rule,
            SituationFinancabilite.PLUS_FINANCABLE.name,
        )
        self.assertEqual(
            self.admission.financability_established_by,
            self.sic_manager_user.person,
        )
        self.assertEqual(
            self.admission.checklist['current']['financabilite']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

    def test_post_with_faculty_manager(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(
            self.url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 403)


@freezegun.freeze_time('2022-01-01')
class FinancabiliteNotFinanceableViewTestCase(OsisDocumentMockTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            financability_computed_rule=EtatFinancabilite.NON_FINANCABLE.name,
            financability_computed_rule_situation=SituationFinancabilite.PLUS_FINANCABLE.name,
            financability_computed_rule_on=timezone.now(),
            specific_question_answers={str(AdmissionFormItemFactory(internal_label=PASS_ET_LAS_LABEL).uuid): 0},
        )
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url = resolve_url(
            'admission:doctorate:financability-not-financeable',
            uuid=cls.admission.uuid,
        )

    def test_post(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.financability_rule,
            SituationFinancabilite.PLUS_FINANCABLE.name,
        )
        self.assertEqual(
            self.admission.financability_established_by,
            self.sic_manager_user.person,
        )
        self.assertEqual(
            self.admission.checklist['current']['financabilite']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

    def test_post_with_faculty_manager(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(
            self.url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 403)


class FinancabiliteDerogationViewTestCase(OsisDocumentMockTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            specific_question_answers={str(AdmissionFormItemFactory(internal_label=PASS_ET_LAS_LABEL).uuid): 0},
        )
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def test_non_concerne_post(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:doctorate:financability-derogation-non-concerne',
            uuid=self.admission.uuid,
        )
        response = self.client.post(
            url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.financability_dispensation_status,
            DerogationFinancement.NON_CONCERNE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(
            self.admission.financability_established_by,
            self.sic_manager_user.person,
        )

        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(
            url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 403)

    def test_abandon_candidat_post(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:doctorate:financability-derogation-abandon',
            uuid=self.admission.uuid,
        )
        response = self.client.post(
            url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.financability_dispensation_status,
            DerogationFinancement.ABANDON_DU_CANDIDAT.name,
        )
        self.assertEqual(
            self.admission.financability_established_by,
            self.sic_manager_user.person,
        )

        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(
            url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 403)

    def test_refus_post(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:doctorate:financability-derogation-refus',
            uuid=self.admission.uuid,
        )
        response = self.client.post(
            url,
            data={'financability-dispensation-refusal-reasons': ['Autre']},
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.financability_dispensation_status,
            DerogationFinancement.REFUS_DE_DEROGATION_FACULTAIRE.name,
        )
        self.assertEqual(
            self.admission.financability_established_by,
            self.sic_manager_user.person,
        )

        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(
            url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 403)

    def test_refus_post_with_other_reasons(self):
        self.client.force_login(user=self.sic_manager_user)

        refusal_reason = DoctorateRefusalReasonFactory()
        self.admission.refusal_reasons.set([refusal_reason])

        url = resolve_url(
            'admission:doctorate:financability-derogation-refus',
            uuid=self.admission.uuid,
        )
        response = self.client.post(
            url,
            data={'financability-dispensation-refusal-reasons': [str(refusal_reason.uuid), 'Autre']},
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.financability_dispensation_status,
            DerogationFinancement.REFUS_DE_DEROGATION_FACULTAIRE.name,
        )
        self.assertQuerysetEqual(
            self.admission.refusal_reasons.all(),
            [refusal_reason],
        )
        self.assertListEqual(
            self.admission.other_refusal_reasons,
            ['Autre'],
        )
        self.assertEqual(
            self.admission.financability_established_by,
            self.sic_manager_user.person,
        )

    def test_accord_post(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:doctorate:financability-derogation-accord',
            uuid=self.admission.uuid,
        )
        response = self.client.post(
            url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.financability_dispensation_status,
            DerogationFinancement.ACCORD_DE_DEROGATION_FACULTAIRE.name,
        )
        self.assertEqual(
            self.admission.financability_established_by,
            self.sic_manager_user.person,
        )

        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(
            url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 403)

    def test_notification_candidat(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:doctorate:financability-derogation-notification',
            uuid=self.admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'financability-dispensation-notification-subject': 'foo',
                'financability-dispensation-notification-body': 'bar',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        self.admission.refresh_from_db()
        self.assertEqual(self.admission.financability_dispensation_status, DerogationFinancement.CANDIDAT_NOTIFIE.name)
        self.assertEqual(self.admission.financability_dispensation_first_notification_by, self.sic_manager_user.person)

        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(
            url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 403)


@freezegun.freeze_time('2022-01-01')
class FinancabiliteNotConcernedViewTestCase(OsisDocumentMockTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2022)

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_year,
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            financability_computed_rule=EtatFinancabilite.FINANCABLE.name,
            financability_computed_rule_situation=SituationFinancabilite.FINANCABLE_D_OFFICE.name,
            financability_computed_rule_on=timezone.now(),
            specific_question_answers={str(AdmissionFormItemFactory(internal_label=PASS_ET_LAS_LABEL).uuid): 0},
        )
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url = resolve_url(
            'admission:doctorate:financability-not-concerned',
            uuid=cls.admission.uuid,
        )

    def test_post(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('admission/general_education/includes/checklist/financabilite.html')

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.financability_rule, '')
        self.assertEqual(
            self.admission.financability_established_by,
            self.sic_manager_user.person,
        )
        self.assertEqual(
            self.admission.checklist['current']['financabilite']['statut'],
            ChoixStatutChecklist.INITIAL_NON_CONCERNE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

    def test_post_with_faculty_manager(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(
            self.url,
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 403)
