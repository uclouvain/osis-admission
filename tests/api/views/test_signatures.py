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
from rest_framework.test import APITestCase

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixLangueRedactionThese,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    CotutelleDoitAvoirAuMoinsUnPromoteurExterneException,
    MembreCAManquantException,
    PromoteurManquantException,
    SignataireNonTrouveException,
)
from admission.tests.factories import DoctorateAdmissionFactory, WriteTokenFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.roles import ProgramManagerRoleFactory
from admission.tests.factories.supervision import CaMemberFactory, ExternalPromoterFactory, PromoterFactory
from osis_notification.models import EmailNotification

from reference.tests.factories.language import FrenchLanguageFactory


class RequestSignaturesApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.patcher = patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = cls.patcher.start()
        patched.side_effect = lambda _, value, __: ["550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"] if value else []
        cls.language_fr = FrenchLanguageFactory()
        cls.admission = DoctorateAdmissionFactory(
            cotutelle=False,
            project_title="title",
            project_abstract="abstract",
            financing_type=ChoixTypeFinancement.SELF_FUNDING.name,
            thesis_language=cls.language_fr,
            project_document=[WriteTokenFactory().token],
            gantt_graph=[WriteTokenFactory().token],
            program_proposition=[WriteTokenFactory().token],
        )
        ProgramManagerRoleFactory(education_group_id=cls.admission.training.education_group_id)
        AdmissionAcademicCalendarFactory.produce_all_required()
        cls.patcher.stop()
        cls.candidate = cls.admission.candidate
        cls.url = resolve_url("admission_api_v1:request-signatures", uuid=cls.admission.uuid)

    def setUp(self):
        patched = self.patcher.start()
        patched.side_effect = lambda _, value, __: ["550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"] if value else []
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
        promoter = PromoterFactory(is_reference_promoter=True)
        CaMemberFactory(process=promoter.process)
        CaMemberFactory(process=promoter.process)
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EmailNotification.objects.count(), 4)

    def test_request_signatures_using_api_without_ca_members_must_fail(self):
        self.client.force_authenticate(user=self.candidate.user)

        promoter = PromoterFactory(is_reference_promoter=True)
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], MembreCAManquantException.status_code)

    def test_request_signatures_using_api_cotutelle_without_external_promoter_must_fail(self):
        self.client.force_authenticate(user=self.candidate.user)
        admission = DoctorateAdmissionFactory(
            candidate=self.candidate,
            with_cotutelle=True,
            financing_type=ChoixTypeFinancement.SELF_FUNDING.name,
            project_title="title",
            project_abstract="abstract",
            thesis_language=self.language_fr,
            project_document=[WriteTokenFactory().token],
            gantt_graph=[WriteTokenFactory().token],
            program_proposition=[WriteTokenFactory().token],
        )
        url = resolve_url("admission_api_v1:request-signatures", uuid=admission.uuid)

        promoter = PromoterFactory(is_reference_promoter=True)
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
            with_cotutelle=True,
            financing_type=ChoixTypeFinancement.SELF_FUNDING.name,
            project_title="title",
            project_abstract="abstract",
            thesis_language=self.language_fr,
            project_document=[WriteTokenFactory().token],
            gantt_graph=[WriteTokenFactory().token],
            program_proposition=[WriteTokenFactory().token],
        )
        url = resolve_url("admission_api_v1:request-signatures", uuid=admission.uuid)

        promoter = ExternalPromoterFactory()
        PromoterFactory(process=promoter.actor_ptr.process, is_reference_promoter=True)
        CaMemberFactory(process=promoter.actor_ptr.process)
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

    def test_resend_signature(self):
        self.client.force_authenticate(user=self.candidate.user)

        promoter = PromoterFactory(is_reference_promoter=True)
        external_promoter = ExternalPromoterFactory(process=promoter.process)
        CaMemberFactory(process=promoter.process)
        CaMemberFactory(process=promoter.process)
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()

        # Send first time
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        EmailNotification.objects.all().delete()

        # Resend for internal must fail
        response = self.client.put(self.url, {'uuid_membre': promoter.uuid})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            SignataireNonTrouveException.status_code,
        )

        # Resend for external
        response = self.client.put(self.url, {'uuid_membre': external_promoter.uuid})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(EmailNotification.objects.count(), 1)
