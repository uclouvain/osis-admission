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
import uuid
from typing import Optional, List
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_200_OK, HTTP_302_FOUND

from admission.contrib.models import ConfirmationPaper
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixTypeAdmission
from admission.ddd.projet_doctoral.preparation.domain.model._financement import (
    ChoixTypeFinancement,
    ChoixTypeContratTravail,
)
from admission.ddd.projet_doctoral.preparation.domain.model.doctorat import ENTITY_CDE, ENTITY_CDSS
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.confirmation_paper import ConfirmationPaperFactory
from admission.tests.factories.roles import CddManagerFactory, AdreRoleFactory
from admission.tests.factories.supervision import PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class DoctorateAdmissionConfirmationFormViewTestCase(TestCase):
    admission_with_confirmation_papers = Optional[DoctorateAdmissionFactory]
    admission_without_confirmation_paper = Optional[DoctorateAdmissionFactory]
    confirmation_papers = List[ConfirmationPaperFactory]

    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        second_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=second_doctoral_commission, acronym=ENTITY_CDSS)

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create admissions
        cls.admission_without_confirmation_paper = DoctorateAdmissionFactory(
            doctorate__management_entity=first_doctoral_commission,
            doctorate__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=promoter.process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            pre_admission_submission_date=datetime.datetime.now(),
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
        )
        cls.admission_with_confirmation_papers = DoctorateAdmissionFactory(
            doctorate__management_entity=first_doctoral_commission,
            doctorate__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=promoter.process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            pre_admission_submission_date=datetime.datetime.now(),
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
        )
        cls.confirmation_papers = [
            ConfirmationPaperFactory(
                admission=cls.admission_with_confirmation_papers,
                confirmation_date=datetime.date(2022, 4, 1),
                confirmation_deadline=datetime.date(2022, 4, 5),
            ),
            ConfirmationPaperFactory(
                admission=cls.admission_with_confirmation_papers,
                confirmation_date=datetime.date(2022, 1, 1),
                confirmation_deadline=datetime.date(2022, 4, 5),
            ),
        ]
        cls.last_confirmation_paper = cls.confirmation_papers[0]

        cls.candidate = cls.admission_without_confirmation_paper.candidate

        # User with one cdd
        cls.cdd_person = CddManagerFactory(entity=first_doctoral_commission).person

        cls.default_updated_params = {
            'date': datetime.date(2023, 12, 1),
            'date_limite': datetime.date(2023, 12, 31),
        }

        cls.path = 'admission:doctorate:update:confirmation'

    def test_get_confirmation_form_cdd_user_without_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_confirmation_form_cdd_user_with_confirmation_papers(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertIsNotNone(response.context.get('doctorate'))
        self.assertEqual(response.context.get('doctorate').uuid, str(self.admission_with_confirmation_papers.uuid))

        self.assertIsNotNone(response.context.get('confirmation_paper'))
        self.assertEqual(response.context.get('confirmation_paper').uuid, str(self.last_confirmation_paper.uuid))
        self.assertEqual(
            response.context.get('form').initial,
            {
                'date_limite': self.last_confirmation_paper.confirmation_deadline,
                'date': self.last_confirmation_paper.confirmation_date,
                'rapport_recherche': self.last_confirmation_paper.research_report,
                'proces_verbal_ca': self.last_confirmation_paper.supervisor_panel_report,
                'avis_renouvellement_mandat_recherche': self.last_confirmation_paper.research_mandate_renewal_opinion,
            },
        )

    def test_get_confirmation_detail_cdd_user_with_unknown_doctorate(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[uuid.uuid4()])

        response = self.client.get(url, data={})

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_confirmation_detail_cdd_user_with_unknown_doctorate(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[uuid.uuid4()])

        response = self.client.post(url, data=self.default_updated_params)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_confirmation_form_cdd_user_without_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.post(url, data=self.default_updated_params)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_confirmation_form_cdd_user_with_confirmation_papers(self):
        self.client.force_login(user=self.cdd_person.user)

        confirmation_paper_to_update = ConfirmationPaperFactory(
            admission=self.admission_with_confirmation_papers,
            confirmation_date=datetime.date(2023, 1, 1),
            confirmation_deadline=datetime.date(2023, 4, 5),
        )

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.post(url, data=self.default_updated_params)

        self.assertEqual(response.status_code, HTTP_302_FOUND)

        updated_confirmation_paper = ConfirmationPaper.objects.get(pk=confirmation_paper_to_update.pk)

        self.assertEqual(updated_confirmation_paper.confirmation_date, self.default_updated_params['date'])
        self.assertEqual(updated_confirmation_paper.confirmation_deadline, self.default_updated_params['date_limite'])


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class DoctorateAdmissionConfirmationOpinionFormViewTestCase(TestCase):
    admission_with_confirmation_papers = Optional[DoctorateAdmissionFactory]
    admission_without_confirmation_paper = Optional[DoctorateAdmissionFactory]
    confirmation_papers = List[ConfirmationPaperFactory]

    @classmethod
    def setUpTestData(cls):
        cls.confirm_remote_upload_patcher = patch('osis_document.api.utils.confirm_remote_upload')
        patched = cls.confirm_remote_upload_patcher.start()
        patched.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'

        cls.get_remote_metadata_patcher = patch('osis_document.api.utils.get_remote_metadata')
        patched = cls.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf"}

        cls.get_remote_token_patcher = patch('osis_document.api.utils.get_remote_token')
        patched = cls.get_remote_token_patcher.start()
        patched.return_value = 'foobar'

        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        promoter = PromoterFactory()

        # Create admissions
        cls.admission_without_confirmation_paper = DoctorateAdmissionFactory(
            doctorate__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=promoter.process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            pre_admission_submission_date=datetime.datetime.now(),
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
        )
        cls.admission_with_confirmation_papers = DoctorateAdmissionFactory(
            doctorate__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=promoter.process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            pre_admission_submission_date=datetime.datetime.now(),
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
        )
        cls.confirmation_papers = [
            ConfirmationPaperFactory(
                admission=cls.admission_with_confirmation_papers,
                confirmation_date=datetime.date(2022, 4, 1),
                confirmation_deadline=datetime.date(2022, 4, 5),
                research_mandate_renewal_opinion=['avis_renouvellement_mandat_recherche_0'],
            ),
            ConfirmationPaperFactory(
                admission=cls.admission_with_confirmation_papers,
                confirmation_date=datetime.date(2022, 1, 1),
                confirmation_deadline=datetime.date(2022, 4, 5),
                research_mandate_renewal_opinion=['avis_renouvellement_mandat_recherche_0'],
            ),
        ]
        cls.last_confirmation_paper = cls.confirmation_papers[0]

        cls.candidate = cls.admission_without_confirmation_paper.candidate

        # User with one cdd
        cls.adre_person = AdreRoleFactory().person

        cls.default_updated_params = {
            'avis_renouvellement_mandat_recherche_0': 'avis_renouvellement_mandat_recherche_1',
        }

        cls.path = 'admission:doctorate:update:confirmation-opinion'

    @classmethod
    def tearDownClass(cls):
        cls.confirm_remote_upload_patcher.stop()
        cls.get_remote_metadata_patcher.stop()
        cls.get_remote_token_patcher.stop()
        super().tearDownClass()

    def test_get_confirmation_form_candidate_user(self):
        self.client.force_login(user=self.candidate.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.get(url)

        response.status_code = HTTP_403_FORBIDDEN

    def test_get_confirmation_form_cdd_user_without_confirmation_paper(self):
        self.client.force_login(user=self.adre_person.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_confirmation_form_cdd_user_with_confirmation_papers(self):
        self.client.force_login(user=self.adre_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertIsNotNone(response.context.get('doctorate'))
        self.assertEqual(response.context.get('doctorate').uuid, str(self.admission_with_confirmation_papers.uuid))

        self.assertIsNotNone(response.context.get('confirmation_paper'))
        self.assertEqual(response.context.get('confirmation_paper').uuid, str(self.last_confirmation_paper.uuid))
        self.assertEqual(
            response.context.get('form').initial,
            {
                'avis_renouvellement_mandat_recherche': [
                    uuid.UUID(self.last_confirmation_paper.research_mandate_renewal_opinion[0]),
                ],
            },
        )

    def test_get_confirmation_detail_cdd_user_with_unknown_doctorate(self):
        self.client.force_login(user=self.adre_person.user)

        url = reverse(self.path, args=[uuid.uuid4()])

        response = self.client.get(url, data={})

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_confirmation_detail_cdd_user_with_unknown_doctorate(self):
        self.client.force_login(user=self.adre_person.user)

        url = reverse(self.path, args=[uuid.uuid4()])

        response = self.client.post(url, data=self.default_updated_params)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_confirmation_form_cdd_user_without_confirmation_paper(self):
        self.client.force_login(user=self.adre_person.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.post(url, data=self.default_updated_params)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_confirmation_form_cdd_user_with_confirmation_papers(self):
        self.client.force_login(user=self.adre_person.user)

        confirmation_paper_to_update = ConfirmationPaperFactory(
            admission=self.admission_with_confirmation_papers,
            confirmation_date=datetime.date(2023, 1, 1),
            confirmation_deadline=datetime.date(2023, 4, 5),
        )

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.post(url, data=self.default_updated_params)

        self.assertEqual(response.status_code, HTTP_302_FOUND)

        updated_confirmation_paper = ConfirmationPaper.objects.get(pk=confirmation_paper_to_update.pk)

        self.assertEqual(
            updated_confirmation_paper.research_mandate_renewal_opinion,
            [uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')],
        )
