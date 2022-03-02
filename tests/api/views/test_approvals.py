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
from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.projet_doctoral.preparation.domain.model._detail_projet import ChoixLangueRedactionThese
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixStatutProposition
from admission.tests.factories import DoctorateAdmissionFactory, WriteTokenFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory
from osis_signature.enums import SignatureState


class ApprovalMixin:
    @classmethod
    def setUpTestData(cls):
        # Create promoters
        cls.promoter = PromoterFactory()
        cls.promoter.actor_ptr.switch_state(SignatureState.INVITED)

        cls.promoter_who_approved = PromoterFactory(process=cls.promoter.process)
        cls.promoter_who_approved.actor_ptr.switch_state(SignatureState.APPROVED)

        cls.other_promoter = PromoterFactory()

        # Create ca members
        cls.ca_member = CaMemberFactory(process=cls.promoter.process)
        cls.invited_ca_member = CaMemberFactory(process=cls.promoter.process)
        cls.invited_ca_member.actor_ptr.switch_state(SignatureState.INVITED)
        cls.other_ca_member = CaMemberFactory()

        # Create the admission
        cls.admission = DoctorateAdmissionFactory(
            status=ChoixStatutProposition.SIGNING_IN_PROGRESS.name,
            supervision_group=cls.promoter.process,
            cotutelle=False,
            project_title="title",
            project_abstract="abstract",
            thesis_language=ChoixLangueRedactionThese.FRENCH.name,
            project_document=[WriteTokenFactory().token],
            gantt_graph=[WriteTokenFactory().token],
            program_proposition=[WriteTokenFactory().token],
        )

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
        cls.url = resolve_url("approvals", uuid=cls.admission.uuid)


@override_settings(ROOT_URLCONF='admission.api.url_v1')
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

    def test_supervision_approve_proposition_api_invited_promoter(self):
        self.client.force_authenticate(user=self.promoter.person.user)
        response = self.client.post(self.url, {
            "matricule": self.promoter.person.global_id,
            **self.approved_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'uuid': str(self.admission.uuid)})

    def test_supervision_approve_proposition_api_promoter_who_approved(self):
        self.client.force_authenticate(user=self.promoter_who_approved.person.user)
        response = self.client.post(self.url, {
            "matricule": self.promoter_who_approved.person.global_id,
            **self.approved_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_approve_proposition_api_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter.person.user)
        response = self.client.post(self.url, {
            "matricule": self.other_promoter.person.global_id,
            **self.approved_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_approve_proposition_api_not_invited_ca_member(self):
        self.client.force_authenticate(user=self.ca_member.person.user)
        response = self.client.post(self.url, {
            "matricule": self.ca_member.person.global_id,
            **self.approved_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_approve_proposition_api_other_ca_member(self):
        self.client.force_authenticate(user=self.other_ca_member.person.user)
        response = self.client.post(self.url, {
            "matricule": self.other_ca_member.person.global_id,
            **self.approved_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_refuse_proposition_api_invited_promoter(self):
        self.client.force_authenticate(user=self.promoter.person.user)
        response = self.client.put(self.url, {
            "matricule": self.promoter.person.global_id,
            **self.refused_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'uuid': str(self.admission.uuid)})

    def test_supervision_refuse_proposition_api_invited_ca_member(self):
        self.client.force_authenticate(user=self.invited_ca_member.person.user)
        response = self.client.put(self.url, {
            "matricule": self.invited_ca_member.person.global_id,
            **self.refused_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'uuid': str(self.admission.uuid)})

    def test_supervision_refuse_proposition_api_promoter_who_approved(self):
        self.client.force_authenticate(user=self.promoter_who_approved.person.user)
        response = self.client.put(self.url, {
            "matricule": self.promoter_who_approved.person.global_id,
            **self.refused_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_refuse_proposition_api_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter.person.user)
        response = self.client.put(self.url, {
            "matricule": self.other_promoter.person.global_id,
            **self.refused_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_refuse_proposition_api_not_invited_ca_member(self):
        self.client.force_authenticate(user=self.ca_member.person.user)
        response = self.client.put(self.url, {
            "matricule": self.ca_member.person.global_id,
            **self.refused_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_refuse_proposition_api_other_ca_member(self):
        self.client.force_authenticate(user=self.other_ca_member.person.user)
        response = self.client.put(self.url, {
            "matricule": self.other_ca_member.person.global_id,
            **self.refused_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class ApproveByPdfApiTestCase(ApprovalMixin, APITestCase):
    def setUp(self):
        # Targeted url
        self.url = resolve_url("approve-by-pdf", uuid=self.admission.uuid)
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
        response = self.client.post(self.url, {
            "matricule": self.promoter.person.global_id,
            **self.approved_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_proposition_api_promoter_who_approved(self):
        self.client.force_authenticate(user=self.admission.candidate.user)
        response = self.client.post(self.url, {
            "matricule": self.promoter_who_approved.person.global_id,
            **self.approved_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approve_proposition_api_not_invited_ca_member(self):
        self.client.force_authenticate(user=self.admission.candidate.user)
        response = self.client.post(self.url, {
            "matricule": self.ca_member.person.global_id,
            **self.approved_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approve_proposition_api_by_pdf(self):
        self.client.force_authenticate(user=self.admission.candidate.user)
        response = self.client.post(self.url, {
            "matricule": self.promoter.person.global_id,
            **self.approved_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
