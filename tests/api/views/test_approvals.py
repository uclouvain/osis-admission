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

from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.tests.factories import DoctorateAdmissionFactory, WriteTokenFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.supervision import CaMemberFactory, ExternalPromoterFactory, PromoterFactory
from base.tests.factories.user import UserFactory
from osis_signature.enums import SignatureState
from osis_signature.utils import get_signing_token


class ApprovalMixin:
    @classmethod
    def setUpTestData(cls):
        # Create promoters
        cls.promoter = PromoterFactory(is_reference_promoter=True)
        cls.promoter.actor_ptr.switch_state(SignatureState.INVITED)

        cls.promoter_who_approved = PromoterFactory(process=cls.promoter.process)
        cls.promoter_who_approved.actor_ptr.switch_state(SignatureState.APPROVED)

        cls.external_promoter = ExternalPromoterFactory(process=cls.promoter.process)
        cls.external_promoter.actor_ptr.switch_state(SignatureState.INVITED)

        cls.other_promoter = PromoterFactory()

        # Create ca members
        cls.ca_member = CaMemberFactory(process=cls.promoter.process)
        cls.invited_ca_member = CaMemberFactory(process=cls.promoter.process)
        cls.invited_ca_member.actor_ptr.switch_state(SignatureState.INVITED)
        cls.other_ca_member = CaMemberFactory()

        # Create the admission
        cls.admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
            supervision_group=cls.promoter.process,
            cotutelle=False,
        )

        AdmissionAcademicCalendarFactory.produce_all_required()

        # Mocked data
        cls.approved_data = {
            "commentaire_interne": "A wonderful internal comment",
            "commentaire_externe": "An external comment",
        }
        cls.refused_data = {
            **cls.approved_data,
            "motif_refus": "Incomplete proposition",
        }

        # Targeted url
        cls.url = resolve_url("admission_api_v1:approvals", uuid=cls.admission.uuid)
        cls.supervision_url = resolve_url("admission_api_v1:supervision", uuid=cls.admission.uuid)


class ApprovalsApiTestCase(ApprovalMixin, APITestCase):
    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.promoter.person.user)
        methods_not_allowed = ['get', 'delete', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_supervision_get(self):
        self.client.force_authenticate(user=self.promoter.person.user)
        response = self.client.get(self.supervision_url)
        data = response.json()
        self.assertIn('promoteur_reference', data)
        self.assertEqual(data['promoteur_reference'], str(self.promoter.uuid))

    def test_supervision_approve_proposition_api_invited_promoter(self):
        self.client.force_authenticate(user=self.promoter.person.user)
        response = self.client.post(self.url, {"uuid_membre": str(self.promoter.uuid), **self.approved_data})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(response.json(), {'uuid': str(self.admission.uuid)})
        response = self.client.get(self.supervision_url)
        self.assertEqual(response.json()['promoteur_reference'], str(self.promoter.uuid))

    def test_supervision_approve_proposition_api_promoter_who_approved(self):
        self.client.force_authenticate(user=self.promoter_who_approved.person.user)
        response = self.client.post(
            self.url, {"uuid_membre": str(self.promoter_who_approved.uuid), **self.approved_data}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_approve_proposition_api_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter.person.user)
        response = self.client.post(self.url, {"uuid_membre": str(self.other_promoter.uuid), **self.approved_data})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_approve_proposition_api_not_invited_ca_member(self):
        self.client.force_authenticate(user=self.ca_member.person.user)
        response = self.client.post(self.url, {"uuid_membre": str(self.ca_member.uuid), **self.approved_data})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_approve_proposition_api_other_ca_member(self):
        self.client.force_authenticate(user=self.other_ca_member.person.user)
        response = self.client.post(self.url, {"uuid_membre": str(self.other_ca_member.uuid), **self.approved_data})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_refuse_proposition_api_invited_promoter(self):
        self.client.force_authenticate(user=self.promoter.person.user)
        response = self.client.put(self.url, {"uuid_membre": str(self.promoter.uuid), **self.refused_data})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'uuid': str(self.admission.uuid)})

    def test_supervision_refuse_proposition_api_invited_ca_member(self):
        self.client.force_authenticate(user=self.invited_ca_member.person.user)
        response = self.client.put(self.url, {"uuid_membre": str(self.invited_ca_member.uuid), **self.refused_data})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'uuid': str(self.admission.uuid)})

    def test_supervision_refuse_proposition_api_promoter_who_approved(self):
        self.client.force_authenticate(user=self.promoter_who_approved.person.user)
        response = self.client.put(self.url, {"uuid_membre": str(self.promoter_who_approved.uuid), **self.refused_data})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_refuse_proposition_api_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter.person.user)
        response = self.client.put(self.url, {"uuid_membre": str(self.other_promoter.uuid), **self.refused_data})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_refuse_proposition_api_not_invited_ca_member(self):
        self.client.force_authenticate(user=self.ca_member.person.user)
        response = self.client.put(self.url, {"uuid_membre": str(self.ca_member.uuid), **self.refused_data})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_refuse_proposition_api_other_ca_member(self):
        self.client.force_authenticate(user=self.other_ca_member.person.user)
        response = self.client.put(self.url, {"uuid_membre": str(self.other_ca_member.uuid), **self.refused_data})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ExternalAprovalApiTestCase(ApprovalMixin, APITestCase):
    def setUp(self):
        self.external_user = UserFactory()
        self.url = resolve_url(
            "admission_api_v1:external-approvals",
            uuid=self.admission.uuid,
            token=get_signing_token(self.external_promoter),
        )

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.external_user)
        methods_not_allowed = ['delete', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_supervision_bad_token(self):
        self.client.force_authenticate(user=self.external_user)
        url = resolve_url("admission_api_v1:external-approvals", uuid=self.admission.uuid, token='bad-token')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_get_info(self):
        self.client.force_authenticate(user=self.external_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('supervision', data)
        self.assertEqual(len(data['supervision']['signatures_promoteurs']), 3)
        self.assertIn('proposition', data)
        self.assertIn('fiche_archive_signatures_envoyees', data['proposition'])

    def test_supervision_approve_proposition_api_invited_promoter(self):
        self.client.force_authenticate(user=self.external_user)
        response = self.client.post(self.url, {"uuid_membre": "unused", **self.approved_data})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'uuid': str(self.admission.uuid)})

    def test_supervision_refuse_proposition_api_invited_promoter(self):
        self.client.force_authenticate(user=self.external_user)
        response = self.client.put(self.url, {"uuid_membre": "unsused", **self.refused_data})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'uuid': str(self.admission.uuid)})


class ApproveByPdfApiTestCase(ApprovalMixin, APITestCase):
    def setUp(self):
        # Targeted url
        self.url = resolve_url("admission_api_v1:approve-by-pdf", uuid=self.admission.uuid)
        self.approved_data = {
            "pdf": [WriteTokenFactory().token],
        }

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.promoter.person.user)
        methods_not_allowed = ['get', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_approve_proposition_api_by_promoter(self):
        self.client.force_authenticate(user=self.promoter.person.user)
        response = self.client.post(self.url, {"uuid_membre": str(self.promoter.uuid), **self.approved_data})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_proposition_api_promoter_who_approved(self):
        self.client.force_authenticate(user=self.admission.candidate.user)
        response = self.client.post(
            self.url, {"uuid_membre": str(self.promoter_who_approved.uuid), **self.approved_data}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approve_proposition_api_not_invited_ca_member(self):
        self.client.force_authenticate(user=self.admission.candidate.user)
        response = self.client.post(self.url, {"uuid_membre": str(self.ca_member.uuid), **self.approved_data})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
    @patch('osis_document.api.utils.get_several_remote_metadata')
    @patch('osis_document.api.utils.confirm_remote_upload')
    def test_approve_proposition_api_by_pdf(self, confirm_remote_upload, get_several_remote_metadata, confirm_upload):
        get_several_remote_metadata.side_effect = lambda tokens: {token: {"name": "test.pdf"} for token in tokens}
        confirm_remote_upload.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'
        confirm_upload.return_value = ['4bdffb42-552d-415d-9e4c-725f10dce228']
        self.client.force_authenticate(user=self.admission.candidate.user)
        response = self.client.post(self.url, {"uuid_membre": str(self.promoter.uuid), **self.approved_data})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
