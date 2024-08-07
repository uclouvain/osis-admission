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

import freezegun
from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.translation import gettext
from rest_framework import status

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
)
from admission.tests.views.common.detail_tabs.test_document import BaseDocumentViewTestCase


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class InProgressDocumentTestCase(BaseDocumentViewTestCase):
    # The details page is different when the application is in progress
    @freezegun.freeze_time('2022-01-01')
    def test_general_document_detail_sic_manager_when_in_progress(self):
        self.general_admission.status = ChoixStatutPropositionGenerale.EN_BROUILLON.name
        self.general_admission.save(update_fields=['status'])

        url = resolve_url('admission:general-education:documents', uuid=self.general_admission.uuid)

        self.client.force_login(user=self.second_sic_manager_user)

        # Get the list and the request form
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertInHTML(
            gettext('Until the application is submitted, you can generate a recap of the application on this page.'),
            response.content.decode('utf-8'),
        )

    def test_general_sic_manager_generated_in_progress_analysis_folder(self):
        self._mock_folder_generation()

        url = resolve_url(
            'admission:general-education:document:in-progress-analysis-folder-generation',
            uuid=self.general_admission.uuid,
        )

        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.general_admission.status = ChoixStatutPropositionGenerale.EN_BROUILLON.name
        self.general_admission.save(update_fields=['status'])

        response = self.client.get(url)

        self.assertRedirects(
            response=response,
            expected_url='http://dummyurl/file/pdf-token',
            fetch_redirect_response=False,
        )

    # The details page is different when the application is in progress
    @freezegun.freeze_time('2022-01-01')
    def test_continuing_document_detail_sic_manager_when_in_progress(self):
        self.continuing_admission.status = ChoixStatutPropositionContinue.EN_BROUILLON.name
        self.continuing_admission.save(update_fields=['status'])

        url = resolve_url('admission:continuing-education:documents', uuid=self.continuing_admission.uuid)

        self.client.force_login(user=self.second_sic_manager_user)

        # Get the list and the request form
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertInHTML(
            gettext('Until the application is submitted, you can generate a recap of the application on this page.'),
            response.content.decode('utf-8'),
        )

    @freezegun.freeze_time('2022-01-01')
    def test_continuing_document_detail_fac_manager_when_in_progress(self):
        self.continuing_admission.status = ChoixStatutPropositionContinue.EN_BROUILLON.name
        self.continuing_admission.save(update_fields=['status'])

        url = resolve_url('admission:continuing-education:documents', uuid=self.continuing_admission.uuid)

        self.client.force_login(user=self.continuing_fac_manager_user)

        # Get the list and the request form
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertInHTML(
            gettext('Until the application is submitted, you can generate a recap of the application on this page.'),
            response.content.decode('utf-8'),
        )

    def test_continuing_fac_manager_generated_in_progress_analysis_folder(self):
        self._mock_folder_generation()

        url = resolve_url(
            'admission:continuing-education:document:in-progress-analysis-folder-generation',
            uuid=self.continuing_admission.uuid,
        )

        self.client.force_login(user=self.continuing_fac_manager_user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.continuing_admission.status = ChoixStatutPropositionContinue.EN_BROUILLON.name
        self.continuing_admission.save(update_fields=['status'])

        response = self.client.get(url)

        self.assertRedirects(
            response=response,
            expected_url='http://dummyurl/file/pdf-token',
            fetch_redirect_response=False,
        )

    @freezegun.freeze_time('2022-01-01')
    def test_doctorate_document_detail_sic_manager_when_in_progress(self):
        self.doctorate_admission.status = ChoixStatutPropositionDoctorale.EN_BROUILLON.name
        self.doctorate_admission.save(update_fields=['status'])

        url = resolve_url('admission:doctorate:documents', uuid=self.doctorate_admission.uuid)

        self.client.force_login(user=self.second_sic_manager_user)

        # Get the list and the request form
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertInHTML(
            gettext('Until the application is submitted, you can generate a recap of the application on this page.'),
            response.content.decode('utf-8'),
        )

    def test_doctorate_sic_manager_generated_in_progress_analysis_folder(self):
        self._mock_folder_generation()

        url = resolve_url(
            'admission:doctorate:document:in-progress-analysis-folder-generation',
            uuid=self.doctorate_admission.uuid,
        )

        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.doctorate_admission.status = ChoixStatutPropositionDoctorale.EN_BROUILLON.name
        self.doctorate_admission.save(update_fields=['status'])

        response = self.client.get(url)

        self.assertRedirects(
            response=response,
            expected_url='http://dummyurl/file/pdf-token',
            fetch_redirect_response=False,
        )
