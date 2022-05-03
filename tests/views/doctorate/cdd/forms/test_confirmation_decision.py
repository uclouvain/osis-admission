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
from osis_notification.models import EmailNotification
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_200_OK

from admission.contrib.models import DoctorateAdmission
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import RecupererEpreuvesConfirmationQuery
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixTypeAdmission
from admission.ddd.projet_doctoral.preparation.domain.model._financement import (
    ChoixTypeFinancement,
    ChoixTypeContratTravail,
)
from admission.ddd.projet_doctoral.preparation.domain.model.doctorat import ENTITY_CDE, ENTITY_CDSS
from admission.mail_templates import (
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.confirmation_paper import ConfirmationPaperFactory
from admission.tests.factories.mail_template import CddMailTemplateFactory
from admission.tests.factories.roles import CddManagerFactory
from admission.tests.factories.supervision import PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from infrastructure.messages_bus import message_bus_instance


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CddDoctorateAdmissionConfirmationSuccessDecisionViewTestCase(TestCase):
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
        cls.admission_with_incomplete_confirmation_paper = DoctorateAdmissionFactory(
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
                supervisor_panel_report=['f2'],
            ),
            ConfirmationPaperFactory(
                admission=cls.admission_with_incomplete_confirmation_paper,
                confirmation_deadline=datetime.date(2022, 4, 5),
                supervisor_panel_report=['f2'],
            ),
        ]

        cls.candidate = cls.admission_without_confirmation_paper.candidate

        # User with one cdd
        cls.cdd_person = CddManagerFactory(entity=first_doctoral_commission).person

        # Targeted path
        cls.path = 'admission:doctorate:cdd:confirmation-success'

    @classmethod
    def tearDownClass(cls):
        cls.confirm_remote_upload_patcher.stop()
        cls.get_remote_metadata_patcher.stop()
        cls.get_remote_token_patcher.stop()

    def test_confirmation_success_decision_candidate_user(self):
        self.client.force_login(user=self.candidate.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_confirmation_success_decision_cdd_user_with_unknown_doctorate(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[uuid.uuid4()])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_confirmation_success_decision_cdd_user_without_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_confirmation_success_decision_cdd_user_with_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.post(url)

        self.assertRedirects(
            response,
            reverse(
                'admission:doctorate:cdd:confirmation',
                args=[self.admission_with_confirmation_papers.uuid],
            ),
        )

        doctorate: DoctorateAdmission = DoctorateAdmission.objects.get(
            uuid=self.admission_with_confirmation_papers.uuid
        )
        self.assertEqual(doctorate.post_enrolment_status, ChoixStatutDoctorat.PASSED_CONFIRMATION.name)

    def test_confirmation_success_decision_cdd_user_with_incomplete_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_incomplete_confirmation_paper.uuid])

        response = self.client.post(url)

        self.assertRedirects(
            response,
            reverse(
                'admission:doctorate:cdd:confirmation',
                args=[self.admission_with_incomplete_confirmation_paper.uuid],
            ),
        )

        doctorate: DoctorateAdmission = DoctorateAdmission.objects.get(
            uuid=self.admission_with_incomplete_confirmation_paper.uuid
        )
        self.assertEqual(doctorate.post_enrolment_status, ChoixStatutDoctorat.ADMITTED.name)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CddDoctorateAdmissionConfirmationFailureDecisionViewTestCase(TestCase):
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
        cls.admission_with_incomplete_confirmation_paper = DoctorateAdmissionFactory(
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
                supervisor_panel_report=['f2'],
            ),
            ConfirmationPaperFactory(
                admission=cls.admission_with_incomplete_confirmation_paper,
                confirmation_deadline=datetime.date(2022, 4, 5),
                supervisor_panel_report=['f2'],
            ),
        ]
        cls.custom_cdd_mail_template = CddMailTemplateFactory(
            identifier=ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
            language=cls.admission_with_confirmation_papers.candidate.language,
            cdd=cls.admission_with_confirmation_papers.doctorate.management_entity,
            name='My custom mail',
            subject='The email subject',
            body='The email body',
        )

        cls.candidate = cls.admission_without_confirmation_paper.candidate

        # User with one cdd
        cls.cdd_person = CddManagerFactory(entity=first_doctoral_commission).person

        # Targeted path
        cls.path = 'admission:doctorate:cdd:confirmation-failure'

    @classmethod
    def tearDownClass(cls):
        cls.confirm_remote_upload_patcher.stop()
        cls.get_remote_metadata_patcher.stop()
        cls.get_remote_token_patcher.stop()

    def test_get_confirmation_failure_decision_cdd_user_with_unknown_doctorate(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_confirmation_failure_decision_cdd_user_without_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_confirmation_failure_decision_cdd_user_with_confirmation_paper_and_generic_email(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIsNotNone(response.context.get('select_template_form'))
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)

    def test_get_confirmation_failure_decision_cdd_user_with_confirmation_paper_and_custom_email(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.get(
            url,
            {
                'template': self.custom_cdd_mail_template.pk,
            },
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIsNotNone(response.context.get('select_template_form'))
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)
        self.assertEqual(message_form.initial.get('subject'), self.custom_cdd_mail_template.subject)
        self.assertEqual(message_form.initial.get('body'), self.custom_cdd_mail_template.body)

    def test_get_confirmation_failure_decision_cdd_user_with_confirmation_paper_and_custom_email_and_htmx(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.get(
            url,
            {'template': self.custom_cdd_mail_template.pk},
            **{"HTTP_HX-Request": 'true'},
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)
        self.assertEqual(message_form.initial.get('subject'), self.custom_cdd_mail_template.subject)
        self.assertEqual(message_form.initial.get('body'), self.custom_cdd_mail_template.body)

    def test_post_confirmation_failure_decision_candidate_user(self):
        self.client.force_login(user=self.candidate.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_post_confirmation_failure_decision_cdd_user_with_unknown_doctorate(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[uuid.uuid4()])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_confirmation_failure_decision_cdd_user_without_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_confirmation_failure_decision_cdd_user_with_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.post(
            url,
            {
                'subject': 'The subject of the message',
                'body': 'The body of the message',
            },
        )

        self.assertRedirects(
            response,
            reverse(
                'admission:doctorate:cdd:confirmation',
                args=[self.admission_with_confirmation_papers.uuid],
            ),
        )

        doctorate: DoctorateAdmission = DoctorateAdmission.objects.get(
            uuid=self.admission_with_confirmation_papers.uuid
        )
        self.assertEqual(doctorate.post_enrolment_status, ChoixStatutDoctorat.NOT_ALLOWED_TO_CONTINUE.name)

        self.assertEqual(EmailNotification.objects.count(), 1)
        self.assertEqual(EmailNotification.objects.first().person, self.admission_with_confirmation_papers.candidate)

    def test_post_confirmation_failure_decision_cdd_user_with_incomplete_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_incomplete_confirmation_paper.uuid])

        response = self.client.post(
            url,
            {
                'subject': 'The subject of the message',
                'body': 'The body of the message',
            },
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFormError(
            response,
            'form',
            None,
            [
                "L'épreuve de confirmation n'est pas complète : veuillez vous assurer que la date "
                "et le procès verbal de l'épreuve ont bien été complétés."
            ],
        )

        doctorate: DoctorateAdmission = DoctorateAdmission.objects.get(
            uuid=self.admission_with_incomplete_confirmation_paper.uuid
        )
        self.assertEqual(doctorate.post_enrolment_status, ChoixStatutDoctorat.ADMITTED.name)

    def test_post_confirmation_failure_decision_cdd_user_with_incomplete_form(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.post(
            url,
            {
                'subject': 'The subject of the message',
            },
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFormError(response, 'form', 'body', ['Ce champ est obligatoire.'])


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CddDoctorateAdmissionConfirmationRetakingDecisionViewTestCase(TestCase):
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
        cls.admission_with_incomplete_confirmation_paper = DoctorateAdmissionFactory(
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
                supervisor_panel_report=['f2'],
            ),
            ConfirmationPaperFactory(
                admission=cls.admission_with_incomplete_confirmation_paper,
                confirmation_deadline=datetime.date(2022, 4, 5),
                confirmation_date=datetime.date(2022, 4, 5),
            ),
        ]
        cls.custom_cdd_mail_template = CddMailTemplateFactory(
            identifier=ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
            language=cls.admission_with_confirmation_papers.candidate.language,
            cdd=cls.admission_with_confirmation_papers.doctorate.management_entity,
            name='My custom mail',
            subject='The email subject',
            body='The email body',
        )

        cls.candidate = cls.admission_without_confirmation_paper.candidate

        # User with one cdd
        cls.cdd_person = CddManagerFactory(entity=first_doctoral_commission).person

        # Targeted path
        cls.path = 'admission:doctorate:cdd:confirmation-retaking'

    @classmethod
    def tearDownClass(cls):
        cls.confirm_remote_upload_patcher.stop()
        cls.get_remote_metadata_patcher.stop()
        cls.get_remote_token_patcher.stop()

    def test_get_confirmation_retaking_decision_cdd_user_with_unknown_doctorate(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_confirmation_retaking_decision_cdd_user_without_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_confirmation_retaking_decision_cdd_user_with_confirmation_paper_and_generic_email(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIsNotNone(response.context.get('select_template_form'))
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)

    def test_get_confirmation_retaking_decision_cdd_user_with_confirmation_paper_and_custom_email(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.get(
            url,
            {
                'template': self.custom_cdd_mail_template.pk,
            },
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIsNotNone(response.context.get('select_template_form'))
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)
        self.assertEqual(message_form.initial.get('subject'), self.custom_cdd_mail_template.subject)
        self.assertEqual(message_form.initial.get('body'), self.custom_cdd_mail_template.body)

    def test_get_confirmation_retaking_decision_cdd_user_with_confirmation_paper_and_custom_email_and_htmx(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.get(
            url,
            {'template': self.custom_cdd_mail_template.pk},
            **{"HTTP_HX-Request": 'true'},
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)
        self.assertEqual(message_form.initial.get('subject'), self.custom_cdd_mail_template.subject)
        self.assertEqual(message_form.initial.get('body'), self.custom_cdd_mail_template.body)

    def test_post_confirmation_retaking_decision_candidate_user(self):
        self.client.force_login(user=self.candidate.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_post_confirmation_retaking_decision_cdd_user_with_unknown_doctorate(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[uuid.uuid4()])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_confirmation_retaking_decision_cdd_user_without_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_confirmation_retaking_decision_cdd_user_with_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.post(
            url,
            {
                'subject': 'The subject of the message',
                'body': 'The body of the message',
                'date_limite': datetime.date(2022, 1, 1),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                'admission:doctorate:cdd:confirmation',
                args=[self.admission_with_confirmation_papers.uuid],
            ),
        )

        doctorate: DoctorateAdmission = DoctorateAdmission.objects.get(
            uuid=self.admission_with_confirmation_papers.uuid
        )
        self.assertEqual(doctorate.post_enrolment_status, ChoixStatutDoctorat.CONFIRMATION_TO_BE_REPEATED.name)

        self.assertEqual(EmailNotification.objects.count(), 1)
        self.assertEqual(EmailNotification.objects.first().person, self.admission_with_confirmation_papers.candidate)

        confirmation_papers = message_bus_instance.invoke(
            RecupererEpreuvesConfirmationQuery(doctorat_uuid=doctorate.uuid)
        )

        self.assertEqual(len(confirmation_papers), 2)
        self.assertEqual(confirmation_papers[0].date_limite, datetime.date(2022, 1, 1))

    def test_post_confirmation_retaking_decision_cdd_user_with_incomplete_confirmation_paper(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_incomplete_confirmation_paper.uuid])

        response = self.client.post(
            url,
            {
                'subject': 'The subject of the message',
                'body': 'The body of the message',
                'date_limite': datetime.date(2022, 1, 1),
            },
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFormError(
            response,
            'form',
            None,
            [
                "L'épreuve de confirmation n'est pas complète : veuillez vous assurer que la date "
                "et le procès verbal de l'épreuve ont bien été complétés."
            ],
        )

        doctorate: DoctorateAdmission = DoctorateAdmission.objects.get(
            uuid=self.admission_with_incomplete_confirmation_paper.uuid
        )

        self.assertEqual(doctorate.post_enrolment_status, ChoixStatutDoctorat.ADMITTED.name)

        confirmation_papers = message_bus_instance.invoke(
            RecupererEpreuvesConfirmationQuery(doctorat_uuid=doctorate.uuid)
        )

        self.assertEqual(len(confirmation_papers), 1)

    def test_post_confirmation_retaking_decision_cdd_user_with_incomplete_form(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path, args=[self.admission_with_confirmation_papers.uuid])

        response = self.client.post(
            url,
            {
                'subject': 'The subject of the message',
                'body': 'The body of the message',
            },
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFormError(response, 'form', 'date_limite', ['Ce champ est obligatoire.'])
