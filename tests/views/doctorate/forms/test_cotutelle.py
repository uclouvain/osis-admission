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
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import ProgramManagerRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CotutelleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        # Create admissions
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
        )

        # Users
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.admission.training.education_group
        ).person.user

        # Urls
        cls.url = reverse('admission:doctorate:update:cotutelle', args=[cls.admission.uuid])
        cls.details_url = reverse('admission:doctorate:cotutelle', args=[cls.admission.uuid])

    def setUp(self):
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", "mimetype": "application/pdf", "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_detail_no_permission(self):
        # Anonymous user
        self.client.force_login(user=UserFactory())
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 403)

    def test_update_no_permission(self):
        # Anonymous user
        self.client.force_login(user=UserFactory())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_cotutelle_get(self):
        self.client.force_login(user=self.program_manager_user)
        response = self.client.get(self.details_url)
        self.assertTemplateUsed(response, 'admission/doctorate/details/cotutelle.html')

    def test_cotutelle_get_form(self):
        self.client.force_login(user=self.program_manager_user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admission/doctorate/forms/cotutelle.html')

    def test_cotutelle_update_with_data(self, *args):
        self.client.force_login(user=self.program_manager_user)
        entity_version = EntityVersionFactory()
        response = self.client.post(
            self.url,
            {
                'cotutelle': "YES",
                'motivation': "Barbaz",
                'institution': str(entity_version.entity.organization.uuid),
                'institution_fwb': False,
                'demande_ouverture_0': "34eab30c-27e3-40db-b92e-0b51546a2448",
                'convention': [],
                'autres_documents': [],
            },
            follow=True,
        )
        self.assertTemplateUsed(response, 'admission/doctorate/details/cotutelle.html')

    def test_cotutelle_update_missing_data(self):
        self.client.force_login(user=self.program_manager_user)
        response = self.client.post(self.url, {"cotutelle": "YES", "motivation": "Barbaz"})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'institution', _("This field is required."))
