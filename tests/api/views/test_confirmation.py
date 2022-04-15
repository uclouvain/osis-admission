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
import datetime
from typing import Optional, List
from unittest.mock import patch

from django.contrib.auth.models import User
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models import ConfirmationPaper
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationDateIncorrecteException,
    EpreuveConfirmationNonTrouveeException,
)
from admission.ddd.projet_doctoral.preparation.domain.model._enums import (
    ChoixStatutProposition,
)

from admission.tests.factories import DoctorateAdmissionFactory, WriteTokenFactory
from admission.tests.factories.confirmation_paper import ConfirmationPaperFactory
from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.supervision import PromoterFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class ConfirmationAPIViewTestCase(APITestCase):
    admission: Optional[DoctorateAdmissionFactory] = None
    doctorate: Optional[DoctorateAdmissionFactory] = None
    other_doctorate: Optional[DoctorateAdmissionFactory] = None
    commission: Optional[EntityVersionFactory] = None
    sector: Optional[EntityVersionFactory] = None
    student: Optional[CandidateFactory] = None
    other_student: Optional[CandidateFactory] = None
    no_role_user: Optional[User] = None
    promoter: Optional[User] = None
    other_promoter: Optional[User] = None
    doctorate_url: Optional[str] = None
    other_doctorate_url: Optional[str] = None
    admission_url: Optional[str] = None
    confirmation_papers: List[ConfirmationPaperFactory] = []

    @classmethod
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()
        other_promoter = PromoterFactory()

        # Create doctorate management entity
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.doctorate = DoctorateAdmissionFactory(
            status=ChoixStatutProposition.ENROLLED.name,
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
            doctorate__management_entity=cls.commission,
            supervision_group=promoter.process,
        )
        cls.admission = DoctorateAdmissionFactory(
            doctorate__management_entity=cls.commission,
            candidate=cls.doctorate.candidate,
        )
        cls.other_doctorate = DoctorateAdmissionFactory(
            status=ChoixStatutProposition.ENROLLED.name,
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
            doctorate__management_entity=cls.commission,
            supervision_group=other_promoter.process,
        )

        # Users
        cls.student = cls.doctorate.candidate
        cls.other_student = cls.other_doctorate.candidate
        cls.no_role_user = PersonFactory().user
        cls.promoter = promoter.person.user
        cls.other_promoter = other_promoter.person.user

        cls.doctorate_url = resolve_url('admission_api_v1:confirmation', uuid=cls.doctorate.uuid)
        cls.other_doctorate_url = resolve_url('admission_api_v1:confirmation', uuid=cls.other_doctorate.uuid)
        cls.admission_url = resolve_url('admission_api_v1:confirmation', uuid=cls.admission.uuid)

        cls.supervised_doctorate_url = resolve_url('admission_api_v1:supervised_confirmation', uuid=cls.doctorate.uuid)
        cls.supervised_other_doctorate_url = resolve_url(
            'admission_api_v1:supervised_confirmation',
            uuid=cls.other_doctorate.uuid,
        )
        cls.supervised_admission_url = resolve_url('admission_api_v1:supervised_confirmation', uuid=cls.admission.uuid)

    @patch("osis_document.contrib.fields.FileField._confirm_upload")
    def setUp(self, confirm_upload):
        confirm_upload.return_value = "550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"
        self.confirmation_papers = [
            ConfirmationPaperFactory(
                admission=self.doctorate,
                confirmation_date=datetime.date(2022, 4, 1),
                confirmation_deadline=datetime.date(2022, 4, 5),
                research_report=[WriteTokenFactory().token],
                supervisor_panel_report=[WriteTokenFactory().token],
                thesis_funding_renewal=[WriteTokenFactory().token],
                research_mandate_renewal_opinion=[WriteTokenFactory().token],
            ),
            ConfirmationPaperFactory(
                admission=self.doctorate,
                confirmation_deadline=datetime.date(2022, 4, 10),
                research_report=[WriteTokenFactory().token],
                supervisor_panel_report=[WriteTokenFactory().token],
                thesis_funding_renewal=[WriteTokenFactory().token],
                research_mandate_renewal_opinion=[WriteTokenFactory().token],
            ),
        ]

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'patch',
            'post',
            'put',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.doctorate_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_confirmation_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.doctorate_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        self.assertEqual(len(json_response), 2)

        # Check the first confirmation paper
        self.assertEqual(json_response[0]['uuid'], str(self.confirmation_papers[1].uuid))
        self.assertEqual(json_response[0]['date_limite'], '2022-04-10')
        self.assertIsNone(json_response[0]['date'])
        self.assertIsNone(json_response[0]['demande_prolongation'])

        # Check the second confirmation paper
        self.assertEqual(json_response[1]['uuid'], str(self.confirmation_papers[0].uuid))
        self.assertEqual(json_response[1]['date'], '2022-04-01')
        self.assertEqual(json_response[1]['date_limite'], '2022-04-05')
        self.assertIsNone(json_response[1]['demande_prolongation'])

    def test_get_confirmation_promoter(self):
        self.client.force_authenticate(user=self.promoter)
        response = self.client.get(self.doctorate_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_confirmation_promoter_with_doctorate_invalid_status(self):
        self.client.force_authenticate(user=self.promoter)
        response = self.client.get(self.admission_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter)
        response = self.client.get(self.doctorate_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_student_with_doctorate_invalid_status(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.admission_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_with_doctorate_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.doctorate_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("osis_document.contrib.fields.FileField._confirm_upload")
    def test_put_confirmation_promoter(self, confirm_upload):
        confirmation_paper_uuid = self.confirmation_papers[1].uuid

        token = WriteTokenFactory()

        confirm_upload.return_value = token.upload.uuid

        self.client.force_authenticate(user=self.promoter)

        response = self.client.put(
            self.supervised_doctorate_url,
            format='json',
            data={
                'proces_verbal_ca': [token.token],
                'avis_renouvellement_mandat_recherche': [token.token],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        self.assertEqual(response.json()['uuid'], str(self.doctorate.uuid))

        # Check the first confirmation paper
        confirmation_paper = ConfirmationPaper.objects.get(uuid=confirmation_paper_uuid)

        self.assertEqual(confirmation_paper.uuid, confirmation_paper_uuid)
        self.assertEqual(confirmation_paper.supervisor_panel_report, [token.upload.uuid])
        self.assertEqual(confirmation_paper.research_mandate_renewal_opinion, [token.upload.uuid])

    def test_put_confirmation_by_promoter_with_invalid_doctorate_status(self):
        self.client.force_authenticate(user=self.promoter)
        response = self.client.put(
            self.supervised_admission_url,
            format='json',
            data={
                'proces_verbal_ca': ['f1'],
                'avis_renouvellement_mandat_recherche': ['f2'],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_confirmation_by_promoter_with_doctorate_other_student(self):
        self.client.force_authenticate(user=self.promoter)
        response = self.client.put(
            self.supervised_other_doctorate_url,
            format='json',
            data={
                'proces_verbal_ca': ['f1'],
                'avis_renouvellement_mandat_recherche': ['f2'],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_confirmation_by_promoter_with_doctorate_without_confirmation_paper(self):
        self.client.force_authenticate(user=self.other_promoter)
        response = self.client.put(
            self.supervised_other_doctorate_url,
            format='json',
            data={
                'proces_verbal_ca': ['f1'],
                'avis_renouvellement_mandat_recherche': ['f2'],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            EpreuveConfirmationNonTrouveeException.status_code,
        )

    def test_put_confirmation_promoter_without_supervisor_panel_report(self):
        self.client.force_authenticate(user=self.promoter)
        response = self.client.put(
            self.supervised_doctorate_url,
            format='json',
            data={
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['proces_verbal_ca'][0],
            'Ce champ est obligatoire.',
        )


class LastConfirmationAPIViewTestCase(APITestCase):
    admission: Optional[DoctorateAdmissionFactory] = None
    doctorate: Optional[DoctorateAdmissionFactory] = None
    other_doctorate: Optional[DoctorateAdmissionFactory] = None
    commission: Optional[EntityVersionFactory] = None
    sector: Optional[EntityVersionFactory] = None
    student: Optional[CandidateFactory] = None
    other_student: Optional[CandidateFactory] = None
    no_role_user: Optional[User] = None
    doctorate_url: Optional[str] = None
    other_doctorate_url: Optional[str] = None
    admission_url: Optional[str] = None
    confirmation_papers: List[ConfirmationPaperFactory] = []

    @classmethod
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()

        # Create doctorate management entity
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.doctorate = DoctorateAdmissionFactory(
            status=ChoixStatutProposition.ENROLLED.name,
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
            doctorate__management_entity=cls.commission,
            supervision_group=promoter.process,
        )
        cls.admission = DoctorateAdmissionFactory(
            doctorate__management_entity=cls.commission,
            candidate=cls.doctorate.candidate,
        )
        cls.other_doctorate = DoctorateAdmissionFactory(
            status=ChoixStatutProposition.ENROLLED.name,
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
            doctorate__management_entity=cls.commission,
        )

        # Users
        cls.student = cls.doctorate.candidate
        cls.other_student = cls.other_doctorate.candidate
        cls.no_role_user = PersonFactory().user

        cls.doctorate_url = resolve_url('admission_api_v1:last_confirmation', uuid=cls.doctorate.uuid)
        cls.other_doctorate_url = resolve_url('admission_api_v1:last_confirmation', uuid=cls.other_doctorate.uuid)
        cls.admission_url = resolve_url('admission_api_v1:last_confirmation', uuid=cls.admission.uuid)

    def setUp(self):
        self.confirmation_papers = [
            ConfirmationPaperFactory(
                admission=self.doctorate,
                confirmation_date=datetime.date(2022, 4, 1),
                confirmation_deadline=datetime.date(2022, 4, 5),
            ),
            ConfirmationPaperFactory(
                admission=self.doctorate,
                confirmation_deadline=datetime.date(2022, 4, 10),
            ),
        ]

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'patch',
            'post',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.doctorate_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_confirmation_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.doctorate_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        # Check the first confirmation paper
        self.assertEqual(json_response['uuid'], str(self.confirmation_papers[1].uuid))
        self.assertEqual(json_response['date_limite'], '2022-04-10')
        self.assertIsNone(json_response['date'])
        self.assertIsNone(json_response['demande_prolongation'])

    def test_get_confirmation_with_doctorate_invalid_status(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.admission_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_with_doctorate_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.doctorate_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_confirmation_student_invalid_date(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.put(
            self.doctorate_url,
            format='json',
            data={
                'date': '2022-05-15',
                'rapport_recherche': [],
                'proces_verbal_ca': [],
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            EpreuveConfirmationDateIncorrecteException.status_code,
        )

    def test_put_confirmation_student_without_date(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.put(
            self.doctorate_url,
            format='json',
            data={
                'rapport_recherche': [],
                'proces_verbal_ca': [],
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['date'][0],
            'Ce champ est obligatoire.',
        )

    @patch("osis_document.contrib.fields.FileField._confirm_upload")
    def test_put_confirmation_student(self, confirm_upload):
        confirmation_paper_uuid = self.confirmation_papers[1].uuid

        token = WriteTokenFactory()

        confirm_upload.return_value = token.upload.uuid

        self.client.force_authenticate(user=self.student.user)
        response = self.client.put(
            self.doctorate_url,
            format='json',
            data={
                'date': '2022-04-08',
                'rapport_recherche': [token.token],
                'proces_verbal_ca': [token.token],
                'avis_renouvellement_mandat_recherche': [token.token],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        self.assertEqual(response.json()['uuid'], str(self.doctorate.uuid))

        # Check the first confirmation paper
        confirmation_paper = ConfirmationPaper.objects.get(uuid=confirmation_paper_uuid)

        self.assertEqual(confirmation_paper.uuid, confirmation_paper_uuid)
        self.assertEqual(confirmation_paper.confirmation_deadline, datetime.date(2022, 4, 10))
        self.assertEqual(confirmation_paper.confirmation_date, datetime.date(2022, 4, 8))
        self.assertEqual(confirmation_paper.research_report, [token.upload.uuid])
        self.assertEqual(confirmation_paper.supervisor_panel_report, [token.upload.uuid])
        self.assertEqual(confirmation_paper.research_mandate_renewal_opinion, [token.upload.uuid])

    def test_put_confirmation_with_doctorate_invalid_status(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.put(
            self.admission_url,
            format='json',
            data={
                'date': '2022-05-15',
                'rapport_recherche': [],
                'proces_verbal_ca': [],
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_confirmation_with_doctorate_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.put(
            self.doctorate_url,
            format='json',
            data={
                'date': '2022-05-15',
                'rapport_recherche': [],
                'proces_verbal_ca': [],
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_confirmation_with_doctorate_without_confirmation_paper(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.put(
            self.other_doctorate_url,
            format='json',
            data={
                'date': '2022-05-15',
                'rapport_recherche': [],
                'proces_verbal_ca': [],
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            EpreuveConfirmationNonTrouveeException.status_code,
        )
