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
from osis_signature.enums import SignatureState
from osis_signature.models import StateHistory
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.preparation.projet_doctoral.commands import DemanderSignaturesCommand
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.tests.factories import DoctorateAdmissionFactory, WriteTokenFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class ApprovalsApiTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.promoter = PromoterFactory()
        cls.promoter.actor_ptr.last_state = StateHistory.objects.create(actor=cls.promoter, state=SignatureState.INVITED)
        cls.promoter.actor_ptr.switch_state(SignatureState.INVITED)
        CaMemberFactory(process=cls.promoter.process)
        cls.admission = DoctorateAdmissionFactory(
            supervision_group=cls.promoter.process,
            cotutelle=False,
            project_title="title",
            project_abstract="abstract",
            thesis_language="FR",
            project_document=[WriteTokenFactory().token],
            gantt_graph=[WriteTokenFactory().token],
            program_proposition=[WriteTokenFactory().token],

        )
        cls.url = resolve_url("approve-proposition", uuid=cls.admission.uuid)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.promoter.person.user)
        methods_not_allowed = ['get', 'delete', 'patch', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # @mock.patch(
    #     'admission.infrastructure.preparation.projet_doctoral.domain.service.promoteur.PromoteurTranslator.est_externe',
    #     return_value=True,
    # )
    def test_supervision_approve_proposition_api(self):
        # self.client.force_authenticate(user=self.admission.candidate.user)
        message_bus_in_memory_instance.invoke(DemanderSignaturesCommand(uuid_proposition=self.admission.uuid))
        self.client.force_authenticate(user=self.promoter.person.user)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
