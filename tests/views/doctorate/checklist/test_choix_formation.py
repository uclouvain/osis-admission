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

import freezegun
from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext

from admission.models import DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory


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
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.other_training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[1],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user

        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group,
        ).person.user

        cls.data = {
            'type_demande': 'INSCRIPTION',
            'annee_academique': cls.other_training.academic_year.year,
            'formation': cls.other_training.acronym,
            'poursuite_cycle': 'YES',
        }

        cls.default_headers = {'HTTP_HX-Request': 'true'}

        cls.url_namespace = 'admission:doctorate:choix-formation-update'

    def setUp(self):
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )
        self.url = resolve_url(self.url_namespace, uuid=self.admission.uuid)

    def test_get_htmx(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_post_htmx(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, data=self.data, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Refresh'], 'true')

        self.admission.refresh_from_db()

        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.admission.training, self.other_training)
        self.assertEqual(self.admission.type_demande, TypeDemande.INSCRIPTION.name)

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
        self.assertEqual(self.admission.training, self.other_training)
        self.assertEqual(self.admission.type_demande, TypeDemande.INSCRIPTION.name)

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
                'annee_academique': self.academic_years[1].year,
                'formation': self.training.acronym,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']

        self.assertIn(
            gettext('No training found for the specific year.'),
            form.errors.get(NON_FIELD_ERRORS, []),
        )
