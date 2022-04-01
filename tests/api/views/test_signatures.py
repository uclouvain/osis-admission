# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import patch

from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.projet_doctoral.preparation.domain.model._detail_projet import ChoixLangueRedactionThese
from admission.ddd.projet_doctoral.preparation.domain.model._financement import ChoixTypeFinancement
from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import (
    CotutelleDoitAvoirAuMoinsUnPromoteurExterneException,
    MembreCAManquantException,
    PromoteurManquantException,
)
from admission.tests.factories import DoctorateAdmissionFactory, WriteTokenFactory
from admission.tests.factories.roles import CddManagerFactory
from admission.tests.factories.supervision import CaMemberFactory, ExternalPromoterFactory, PromoterFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class RequestSignaturesApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.patcher = patch('osis_document.contrib.fields.FileField._confirm_upload')
        patched = cls.patcher.start()
        patched.return_value = "550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"
        cls.admission = DoctorateAdmissionFactory(
            cotutelle=False,
            project_title="title",
            project_abstract="abstract",
            financing_type=ChoixTypeFinancement.SELF_FUNDING.name,
            thesis_language=ChoixLangueRedactionThese.FRENCH.name,
            project_document=[WriteTokenFactory().token],
            gantt_graph=[WriteTokenFactory().token],
            program_proposition=[WriteTokenFactory().token],
        )
        CddManagerFactory(entity=cls.admission.doctorate.management_entity)
        cls.patcher.stop()
        cls.candidate = cls.admission.candidate
        cls.url = resolve_url("request-signatures", uuid=cls.admission.uuid)

    def setUp(self):
        patched = self.patcher.start()
        patched.return_value = "550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"
        self.addCleanup(self.patcher.stop)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_request_signatures_using_api(self):
        self.client.force_authenticate(user=self.candidate.user)
        promoter = PromoterFactory()
        CaMemberFactory(process=promoter.process)
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_request_signatures_using_api_without_ca_members_must_fail(self):
        self.client.force_authenticate(user=self.candidate.user)

        promoter = PromoterFactory()
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], MembreCAManquantException.status_code)

    def test_request_signatures_using_api_cotutelle_without_external_promoter_must_fail(self):
        self.client.force_authenticate(user=self.candidate.user)
        admission = DoctorateAdmissionFactory(
            candidate=self.candidate,
            cotutelle=True,
            cotutelle_motivation="Very motivated",
            cotutelle_institution="Somewhere",
            cotutelle_opening_request=[WriteTokenFactory().token],
            cotutelle_convention=[WriteTokenFactory().token],
            financing_type=ChoixTypeFinancement.SELF_FUNDING.name,
            project_title="title",
            project_abstract="abstract",
            thesis_language=ChoixLangueRedactionThese.FRENCH.name,
            project_document=[WriteTokenFactory().token],
            gantt_graph=[WriteTokenFactory().token],
            program_proposition=[WriteTokenFactory().token],
        )
        url = resolve_url("request-signatures", uuid=admission.uuid)

        promoter = PromoterFactory()
        CaMemberFactory(process=promoter.actor_ptr.process)
        admission.supervision_group = promoter.actor_ptr.process
        admission.save()

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            CotutelleDoitAvoirAuMoinsUnPromoteurExterneException.status_code,
        )

    def test_request_signatures_using_api_cotutelle_with_external_promoter(self):
        self.client.force_authenticate(user=self.candidate.user)
        admission = DoctorateAdmissionFactory(
            candidate=self.candidate,
            cotutelle=True,
            cotutelle_motivation="Very motivated",
            cotutelle_institution="Somewhere",
            cotutelle_opening_request=[WriteTokenFactory().token],
            cotutelle_convention=[WriteTokenFactory().token],
            financing_type=ChoixTypeFinancement.SELF_FUNDING.name,
            project_title="title",
            project_abstract="abstract",
            thesis_language=ChoixLangueRedactionThese.FRENCH.name,
            project_document=[WriteTokenFactory().token],
            gantt_graph=[WriteTokenFactory().token],
            program_proposition=[WriteTokenFactory().token],
        )
        url = resolve_url("request-signatures", uuid=admission.uuid)

        promoter = ExternalPromoterFactory()
        PromoterFactory(process=promoter.actor_ptr.process)
        CaMemberFactory(process=promoter.actor_ptr.process)
        admission.supervision_group = promoter.actor_ptr.process
        admission.save()

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_request_signatures_using_api_without_promoter_must_fail(self):
        self.client.force_authenticate(user=self.candidate.user)

        ca_member = CaMemberFactory()
        self.admission.supervision_group = ca_member.actor_ptr.process
        self.admission.save()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], PromoteurManquantException.status_code)
