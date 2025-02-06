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
from django.forms.widgets import Select, HiddenInput
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
    ENTITY_CDSS,
    ENTITY_CLSM,
    SIGLE_SCIENCES,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.models import DoctorateAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import MainEntityVersionFactory


class ChoixFormationDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user

        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group,
        ).person.user

        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self):
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            submitted=True,
        )

        self.url = resolve_url(
            'admission:doctorate:choix-formation-detail',
            uuid=self.admission.uuid,
        )

    def test_get_htmx(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('admission', response.context)

    def test_get_without_htmx(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_get_with_program_manager(self):
        self.client.force_login(user=self.program_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.save(update_fields=['status'])

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)


@freezegun.freeze_time('2023-01-01')
class ChoixFormationFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022, 2023]]

        main_entity = MainEntityVersionFactory().entity

        cls.cde_entity = EntityWithVersionFactory(
            version__parent=main_entity,
            version__acronym=ENTITY_CDE,
        )

        cls.cde_training = DoctorateFactory(
            management_entity=cls.cde_entity,
            academic_year=cls.academic_years[0],
        )

        cls.other_cde_training = DoctorateFactory(
            education_group=cls.cde_training.education_group,
            management_entity=cls.cde_training.management_entity,
            acronym=cls.cde_training.acronym,
            partial_acronym=cls.cde_training.partial_acronym,
            academic_year=cls.academic_years[1],
        )

        cls.other_cdss_training = DoctorateFactory(
            management_entity=EntityWithVersionFactory(
                version__parent=main_entity,
                version__acronym=ENTITY_CDSS,
            ),
            academic_year=cls.academic_years[1],
        )

        cls.other_clsm_training = DoctorateFactory(
            management_entity=EntityWithVersionFactory(
                version__parent=main_entity,
                version__acronym=ENTITY_CLSM,
            ),
            academic_year=cls.academic_years[1],
        )

        cls.other_science_training = DoctorateFactory(
            management_entity__version__parent=main_entity,
            acronym=SIGLE_SCIENCES,
        )

        cls.other_training_without_proximity_commission = DoctorateFactory(
            management_entity__version__parent=main_entity,
            acronym='ABCDEF',
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=main_entity).person.user

        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.cde_training.education_group,
        ).person.user

        cls.data = {
            'type_demande': 'INSCRIPTION',
            'annee_academique': cls.other_cde_training.academic_year.year,
            'commission_proximite': ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
        }

        cls.default_headers = {'HTTP_HX-Request': 'true'}

        cls.url_namespace = 'admission:doctorate:choix-formation-update'

    def setUp(self):
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.cde_training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )
        self.url = resolve_url(self.url_namespace, uuid=self.admission.uuid)

    def test_get_htmx(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        admission_type_field = response.context['form'].fields['type_demande']
        self.assertFalse(admission_type_field.disabled)
        self.assertIsInstance(admission_type_field.widget, Select)

        proximity_commission_field = response.context['form'].fields['commission_proximite']
        self.assertTrue(proximity_commission_field.required)
        self.assertFalse(proximity_commission_field.disabled)
        self.assertIsInstance(proximity_commission_field.widget, Select)
        self.assertCountEqual(proximity_commission_field.choices, ChoixCommissionProximiteCDEouCLSM.choices())

        self.admission.training = self.other_cdss_training
        self.admission.save(update_fields=['training'])

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        proximity_commission_choices = response.context['form'].fields['commission_proximite'].choices
        self.assertCountEqual(proximity_commission_choices, ChoixCommissionProximiteCDSS.choices())

        self.admission.training = self.other_clsm_training
        self.admission.save(update_fields=['training'])

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        proximity_commission_choices = response.context['form'].fields['commission_proximite'].choices
        self.assertCountEqual(proximity_commission_choices, ChoixCommissionProximiteCDEouCLSM.choices())

        self.admission.training = self.other_science_training
        self.admission.save(update_fields=['training'])

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        proximity_commission_choices = response.context['form'].fields['commission_proximite'].choices
        self.assertCountEqual(proximity_commission_choices, ChoixSousDomaineSciences.choices())

        admission_type_field = response.context['form'].fields['type_demande']
        self.assertFalse(admission_type_field.disabled)
        self.assertIsInstance(admission_type_field.widget, Select)

        self.admission.training = self.other_training_without_proximity_commission
        self.admission.save(update_fields=['training'])

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        proximity_commission_field = response.context['form'].fields['commission_proximite']
        self.assertFalse(proximity_commission_field.required)
        self.assertTrue(proximity_commission_field.disabled)
        self.assertIsInstance(proximity_commission_field.widget, HiddenInput)
        self.assertCountEqual(proximity_commission_field.choices, [])

    def test_post_htmx(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, data=self.data, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.headers['HX-Refresh'], 'true')

        self.admission.refresh_from_db()

        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.admission.training, self.other_cde_training)
        self.assertEqual(self.admission.type_demande, TypeDemande.INSCRIPTION.name)
        self.assertEqual(self.admission.proximity_commission, ChoixCommissionProximiteCDEouCLSM.ECONOMY.name)

    def test_get_with_program_manager(self):
        self.client.force_login(user=self.program_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.save(update_fields=['status'])

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertTrue(form.fields['type_demande'].required)
        self.assertTrue(form.fields['type_demande'].disabled)
        self.assertIsInstance(form.fields['type_demande'].widget, HiddenInput)

    def test_post_with_program_manager(self):
        self.client.force_login(user=self.program_manager_user)

        response = self.client.post(self.url, data=self.data, **self.default_headers)

        self.assertEqual(response.status_code, 403)

        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.save(update_fields=['status'])

        response = self.client.post(self.url, data=self.data, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Refresh'], 'true')

        self.admission.refresh_from_db()
        self.assertEqual(self.admission.last_update_author, self.program_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.admission.training, self.other_cde_training)
        self.assertEqual(self.admission.type_demande, TypeDemande.ADMISSION.name)  # Read-only for the CDD managers
        self.assertEqual(self.admission.proximity_commission, ChoixCommissionProximiteCDEouCLSM.ECONOMY.name)

    def test_get_without_htmx(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_post_unknown_training(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            data={
                'type_demande': 'INSCRIPTION',
                'annee_academique': self.academic_years[2].year,
                'commission_proximite': ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']

        self.assertIn(
            gettext('No training found for the specific year.'),
            form.errors.get('annee_academique', []),
        )
