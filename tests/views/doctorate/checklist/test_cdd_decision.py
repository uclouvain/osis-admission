# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

import copy
import datetime
import uuid
from email import message_from_string
from typing import List
from unittest import mock
from unittest.mock import patch

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    DecisionCDDEnum,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from admission.models import DoctorateAdmission
from admission.models.checklist import AdditionalApprovalCondition
from admission.tests import OsisDocumentMockTestMixin
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.comment import CommentEntryFactory
from admission.tests.factories.curriculum import (
    AdmissionEducationalValuatedExperiencesFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
)
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.faculty_decision import DoctorateRefusalReasonFactory
from admission.tests.factories.history import HistoryEntryFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from osis_profile.models import EducationalExperience, ProfessionalExperience


@override_settings(BACKEND_LINK_PREFIX='https//example.com')
class CddDecisionSendToCddViewTestCase(OsisDocumentMockTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
            enrollment_campus__sic_enrollment_email='mons@campus.be',
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        super().setUp()

        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            submitted=True,
            determined_academic_year=self.training.academic_year,
        )
        self.default_checklist = copy.deepcopy(self.admission.checklist)
        self.url = resolve_url(
            'admission:doctorate:cdd-decision-send-to-cdd',
            uuid=self.admission.uuid,
        )

    def test_send_to_cdd_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_send_to_cdd_is_forbidden_with_sic_user_if_the_admission_is_not_in_sic_statuses(self):
        self.client.force_login(user=self.sic_manager_user)

        invalid_statuses = ChoixStatutPropositionDoctorale.get_names_except(
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC,
            ChoixStatutPropositionDoctorale.CONFIRMEE,
            ChoixStatutPropositionDoctorale.RETOUR_DE_FAC,
        )

        for status in invalid_statuses:
            self.admission.status = status
            self.admission.save()

            response = self.client.post(self.url, **self.default_headers)

            self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2022-01-01')
    def test_send_to_cdd_with_sic_user_in_valid_sic_statuses(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.message_fr,
            'Le dossier a été soumis en CDD le 1 Janvier 2022 00:00.',
        )

        self.assertEqual(
            history_entry.message_en,
            'The dossier has been submitted to the CDD on Jan. 1, 2022, midnight.',
        )

        self.assertEqual(
            history_entry.author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )
        self.assertCountEqual(
            history_entry.tags,
            [
                'proposition',
                'cdd-decision',
                'send-to-cdd',
                'status-changed',
            ],
        )

    @freezegun.freeze_time('2022-01-01')
    def test_send_to_cdd_with_sic_user_in_valid_sic_statuses_but_with_invalid_recipient(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        # Check that no notification has been planned
        email_notifications = EmailNotification.objects.all()

        self.assertEqual(len(email_notifications), 0)

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.message_fr,
            'Le dossier a été soumis en CDD le 1 Janvier 2022 00:00.',
        )

        self.assertEqual(
            history_entry.message_en,
            'The dossier has been submitted to the CDD on Jan. 1, 2022, midnight.',
        )

        self.assertEqual(
            history_entry.author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )
        self.assertCountEqual(
            history_entry.tags,
            [
                'proposition',
                'cdd-decision',
                'send-to-cdd',
                'status-changed',
            ],
        )


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
@freezegun.freeze_time('2022-01-01')
class CddDecisionSendToSicViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            submitted=True,
        )
        self.default_checklist = copy.deepcopy(self.admission.checklist)
        self.url = resolve_url(
            'admission:doctorate:cdd-decision-send-to-sic',
            uuid=self.admission.uuid,
        )
        self.file_uuid = uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')

        self.confirm_remote_upload_patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = str(self.file_uuid)
        self.addCleanup(self.confirm_remote_upload_patcher.stop)

        self.confirm_multiple_remote_upload_patcher = mock.patch(
            'osis_document.contrib.fields.FileField._confirm_multiple_upload'
        )
        patched = self.confirm_multiple_remote_upload_patcher.start()
        patched.side_effect = lambda _, value, __: [str(self.file_uuid)] if value else []
        self.addCleanup(self.confirm_multiple_remote_upload_patcher.stop)

        self.get_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf", "size": 1}
        self.addCleanup(self.get_remote_metadata_patcher.stop)

        self.get_remote_token_patcher = mock.patch('osis_document.api.utils.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'foobar'
        self.addCleanup(self.get_remote_token_patcher.stop)

        patcher = patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {
            document_uuid: f'token-{index}' for index, document_uuid in enumerate(uuids)
        }
        self.addCleanup(patcher.stop)

        self.get_several_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        patched = self.get_several_remote_metadata_patcher.start()
        patched.return_value = {"foo": {"name": "test.pdf", "size": 1}}
        self.addCleanup(self.get_several_remote_metadata_patcher.stop)

        self.save_raw_content_remotely_patcher = mock.patch('osis_document.utils.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'
        self.addCleanup(self.save_raw_content_remotely_patcher.stop)

        patcher = mock.patch('admission.exports.utils.change_remote_metadata')
        self.change_remote_metadata_patcher = patcher.start()
        self.change_remote_metadata_patcher.return_value = 'a-token'
        self.addCleanup(patcher.stop)

        # Mock weasyprint
        patcher = mock.patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        self.get_pdf_from_template_patcher = patcher.start()
        self.addCleanup(patcher.stop)

    def test_send_to_sic_is_forbidden_with_fac_user_if_the_admission_is_not_in_specific_statuses(self):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name
        self.admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_send_to_sic_is_forbidden_with_sic_user_if_the_admission_is_not_in_specific_statuses(self):
        self.client.force_login(user=self.sic_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name
        self.admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_send_to_sic_with_fac_user_in_specific_statuses(self, frozen_time):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.checklist['current']['decision_cdd']['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        self.admission.save()

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name)
        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertEqual(history_entry.message_fr, 'Le dossier a été soumis au SIC par la CDD.')

        self.assertEqual(history_entry.message_en, 'The dossier has been submitted to the SIC by the CDD.')

        self.assertCountEqual(
            history_entry.tags,
            ['proposition', 'cdd-decision', 'send-to-sic', 'status-changed'],
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_send_to_sic_with_sic_user_in_specific_statuses(self, frozen_time):
        self.client.force_login(user=self.sic_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.checklist['current']['decision_cdd']['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        self.admission.save()

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name)
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        self.assertEqual(history_entry.message_fr, 'Le dossier a été soumis au SIC par le SIC.')

        self.assertEqual(history_entry.message_en, 'The dossier has been submitted to the SIC by the SIC.')

        self.assertCountEqual(
            history_entry.tags,
            ['proposition', 'cdd-decision', 'send-to-sic', 'status-changed'],
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_send_to_sic_with_fac_user_in_specific_statuses_to_refuse(self, frozen_time):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.refusal_reasons.all().delete()
        self.admission.other_refusal_reasons = []
        self.admission.cdd_refusal_certificate = []
        self.admission.save()

        # Simulate a comment from the CDD
        comment_entry = CommentEntryFactory(
            object_uuid=self.admission.uuid,
            tags=['decision_cdd', 'CDD_FOR_SIC'],
            content='The comment from the CDD to the SIC',
        )

        # Invalid request -> We need to specify a reason
        response = self.client.post(self.url + '?refusal=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            gettext('When refusing a proposition, the reason must be specified.'),
            [m.message for m in response.context['messages']],
        )

        self.admission.other_refusal_reasons = ['test']
        self.admission.save()

        frozen_time.move_to('2022-01-03')

        # Valid request
        response = self.client.post(self.url + '?refusal=1', **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name)
        self.assertEqual(
            self.admission.checklist['current']['decision_cdd']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.admission.checklist['current']['decision_cdd']['extra'],
            {
                'decision': DecisionCDDEnum.EN_DECISION.name,
            },
        )
        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        # A certificate has been generated
        self.assertEqual(self.admission.cdd_refusal_certificate, [self.file_uuid])

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('proposition', pdf_context)
        self.assertEqual(pdf_context['proposition'].uuid, self.admission.uuid)

        self.assertIn('cdd_decision_comment', pdf_context)
        self.assertEqual(pdf_context['cdd_decision_comment'], comment_entry)

        self.assertIn('manager', pdf_context)
        self.assertEqual(pdf_context['manager'].matricule, self.fac_manager_user.person.global_id)

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.admission.uuid)

        self.assertEqual(len(history_entries), 1)

        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertEqual(
            history_entry.message_fr,
            'Le dossier a été refusé par la CDD.',
        )

        self.assertEqual(
            history_entry.message_en,
            'The dossier has been refused by the CDD.',
        )

        self.assertCountEqual(
            history_entry.tags,
            ['proposition', 'cdd-decision', 'refusal', 'status-changed'],
        )


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CddRefusalDecisionViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(
            version__acronym=ENTITY_CDE,
            version__title='Commission doctorale 1',
        )
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(
                gender=ChoixGenre.H.name,
                language=settings.LANGUAGE_CODE_FR,
            ),
            submitted=True,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        self.default_checklist = copy.deepcopy(self.admission.checklist)
        self.url = resolve_url(
            'admission:doctorate:cdd-decision-refusal',
            uuid=self.admission.uuid,
        )
        self.file_uuid = uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')

        self.confirm_remote_upload_patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = str(self.file_uuid)
        self.addCleanup(self.confirm_remote_upload_patcher.stop)

        self.confirm_remote_upload_patcher = mock.patch(
            'osis_document.contrib.fields.FileField._confirm_multiple_upload'
        )
        patched = self.confirm_remote_upload_patcher.start()
        patched.side_effect = lambda _, value, __: [str(self.file_uuid)] if value else []
        self.addCleanup(self.confirm_remote_upload_patcher.stop)

        self.get_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf", "size": 1}
        self.addCleanup(self.get_remote_metadata_patcher.stop)

        self.get_remote_token_patcher = mock.patch('osis_document.api.utils.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'foobar'
        self.addCleanup(self.get_remote_token_patcher.stop)

        self.save_raw_content_remotely_patcher = mock.patch('osis_document.utils.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'
        self.addCleanup(self.save_raw_content_remotely_patcher.stop)

        patcher = mock.patch('admission.exports.utils.change_remote_metadata')
        self.change_remote_metadata_patcher = patcher.start()
        self.change_remote_metadata_patcher.return_value = 'a-token'
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {
            document_uuid: f'token-{index}' for index, document_uuid in enumerate(uuids)
        }
        self.addCleanup(patcher.stop)

        self.get_several_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        patched = self.get_several_remote_metadata_patcher.start()
        patched.return_value = {"foo": {"name": "test.pdf", "size": 1}}
        self.addCleanup(self.get_several_remote_metadata_patcher.stop)

        # Mock weasyprint
        patcher = mock.patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        self.get_pdf_from_template_patcher = patcher.start()
        self.addCleanup(patcher.stop)

    def test_submit_refusal_decision_is_forbidden_with_sic_user(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_submit_refusal_decision_is_forbidden_with_fac_user_if_the_admission_is_not_in_specific_statuses(self):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name
        self.admission.save()

        response = self.client.post(self.url, data={'save_transfer': '1'}, **self.default_headers)

        self.assertEqual(response.status_code, 403)

        self.admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_refusal_decision_form_initialization(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_refusal_form']

    def test_refusal_decision_form_submitting_with_invalid_data(self):
        self.client.force_login(user=self.fac_manager_user)

        # No data
        response = self.client.post(
            self.url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_refusal_form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('reasons', []))

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_refusal_decision_form_submitting_with_valid_data(self, frozen_time):
        self.client.force_login(user=self.fac_manager_user)

        refusal_reason = DoctorateRefusalReasonFactory()

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'cdd-decision-refusal-reasons': [refusal_reason.uuid],
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_refusal_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        refusal_reasons = self.admission.refusal_reasons.all()
        self.assertEqual(len(refusal_reasons), 1)
        self.assertEqual(refusal_reasons[0], refusal_reason)
        self.assertEqual(self.admission.other_refusal_reasons, [])
        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)
        self.assertEqual(
            self.admission.checklist['current']['decision_cdd']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.admission.checklist['current']['decision_cdd']['extra'],
            {'decision': DecisionCDDEnum.EN_DECISION.name},
        )
        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        # Choose another reason
        response = self.client.post(
            self.url,
            data={
                'cdd-decision-refusal-reasons': ['My other reason'],
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_refusal_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertFalse(self.admission.refusal_reasons.exists())
        self.assertEqual(self.admission.other_refusal_reasons, ['My other reason'])
        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

    def test_refusal_decision_is_not_possible_if_the_current_status_is_closed(self):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.checklist['current']['decision_cdd']['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        self.admission.checklist['current']['decision_cdd']['extra'] = {'decision': DecisionCDDEnum.CLOTURE.name}
        self.admission.save()

        response = self.client.post(
            self.url,
            data={'cdd-decision-refusal-reasons': ['My other reason']},
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_refusal_form']
        self.assertTrue(form.is_valid())

        self.assertIn(
            gettext('It is not possible to go from the "Closed" status to this status.'),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has not been updated
        self.admission.refresh_from_db()

        self.assertFalse(self.admission.refusal_reasons.exists())
        self.assertEqual(self.admission.other_refusal_reasons, [])

    @freezegun.freeze_time('2022-01-01')
    def test_refusal_decision_form_submitting_with_transfer_to_sic(self):
        self.client.force_login(user=self.fac_manager_user)

        refusal_reason = DoctorateRefusalReasonFactory()

        # Simulate a comment from the CDD
        comment_entry = CommentEntryFactory(
            object_uuid=self.admission.uuid,
            tags=['decision_cdd', 'CDD_FOR_SIC'],
            content='The comment from the CDD to the SIC',
        )

        # Chosen reason and transfer to SIC
        response = self.client.post(
            self.url,
            data={
                'cdd-decision-refusal-reasons': [refusal_reason.uuid],
                'save-transfer': '1',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_refusal_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        refusal_reasons = self.admission.refusal_reasons.all()
        self.assertEqual(len(refusal_reasons), 1)
        self.assertEqual(refusal_reasons[0], refusal_reason)
        self.assertEqual(self.admission.other_refusal_reasons, [])
        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name)
        self.assertEqual(
            self.admission.checklist['current']['decision_cdd']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.admission.checklist['current']['decision_cdd']['extra'],
            {'decision': DecisionCDDEnum.EN_DECISION.name},
        )
        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        # A certificate has been generated
        self.assertEqual(self.admission.cdd_refusal_certificate, [self.file_uuid])

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('proposition', pdf_context)
        self.assertEqual(pdf_context['proposition'].uuid, self.admission.uuid)

        self.assertIn('cdd_decision_comment', pdf_context)
        self.assertEqual(pdf_context['cdd_decision_comment'], comment_entry)

        self.assertIn('manager', pdf_context)
        self.assertEqual(pdf_context['manager'].matricule, self.fac_manager_user.person.global_id)

        # Check that an entry in the history has been created
        history_entries = HistoryEntry.objects.filter(object_uuid=self.admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertEqual(
            history_entry.message_fr,
            'Le dossier a été refusé par la CDD.',
        )

        self.assertEqual(
            history_entry.message_en,
            'The dossier has been refused by the CDD.',
        )

        self.assertCountEqual(
            history_entry.tags,
            ['proposition', 'cdd-decision', 'refusal', 'status-changed'],
        )


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CddApprovalDecisionViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group,
            person__language=settings.LANGUAGE_CODE_FR,
        ).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

        AdditionalApprovalCondition.objects.all().delete()

    def assertDjangoMessage(self, response, message):
        messages = [m.message for m in response.context['messages']]
        self.assertIn(message, messages)

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            submitted=True,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
            determined_academic_year=self.training.academic_year,
        )
        self.experience_uuid = str(self.admission.candidate.educationalexperience_set.first().uuid)
        self.default_checklist = copy.deepcopy(self.admission.checklist)
        self.url = resolve_url(
            'admission:doctorate:cdd-decision-approval',
            uuid=self.admission.uuid,
        )
        self.file_uuid = uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')

        self.confirm_remote_upload_patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = str(self.file_uuid)
        self.addCleanup(self.confirm_remote_upload_patcher.stop)

        self.confirm_remote_upload_patcher = mock.patch(
            'osis_document.contrib.fields.FileField._confirm_multiple_upload'
        )
        patched = self.confirm_remote_upload_patcher.start()
        patched.side_effect = lambda _, value, __: [str(self.file_uuid)] if value else []
        self.addCleanup(self.confirm_remote_upload_patcher.stop)

        self.get_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf", "size": 1}
        self.addCleanup(self.get_remote_metadata_patcher.stop)

        self.get_remote_token_patcher = mock.patch('osis_document.api.utils.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'foobar'
        self.addCleanup(self.get_remote_token_patcher.stop)

        patcher = patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {
            document_uuid: f'token-{index}' for index, document_uuid in enumerate(uuids)
        }
        self.addCleanup(patcher.stop)

        self.get_several_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        patched = self.get_several_remote_metadata_patcher.start()
        patched.return_value = {"foo": {"name": "test.pdf", "size": 1}}
        self.addCleanup(self.get_several_remote_metadata_patcher.stop)

        self.save_raw_content_remotely_patcher = mock.patch('osis_document.utils.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'
        self.addCleanup(self.save_raw_content_remotely_patcher.stop)

        patcher = mock.patch('admission.exports.utils.change_remote_metadata')
        self.change_remote_metadata_patcher = patcher.start()
        self.change_remote_metadata_patcher.return_value = 'a-token'
        self.addCleanup(patcher.stop)

    def test_submit_approval_decision_is_forbidden_with_sic_user(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_submit_approval_decision_is_forbidden_with_fac_user_if_the_admission_is_not_in_specific_statuses(self):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name
        self.admission.save()

        response = self.client.post(self.url, data={'save_transfer': '1'}, **self.default_headers)

        self.assertEqual(response.status_code, 403)

        self.admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_approval_decision_form_initialization(self):
        self.client.force_login(user=self.fac_manager_user)

        # No approval data
        self.admission.with_prerequisite_courses = None
        self.admission.prerequisite_courses.set([])
        self.admission.prerequisite_courses_fac_comment = ''
        self.admission.annual_program_contact_person_name = ''
        self.admission.annual_program_contact_person_email = ''
        self.admission.communication_to_the_candidate = ''
        self.admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_form']

        self.assertEqual(form.initial.get('with_prerequisite_courses'), None)
        self.assertEqual(form.initial.get('prerequisite_courses'), [])
        self.assertEqual(form.initial.get('prerequisite_courses_fac_comment'), '')
        self.assertEqual(form.initial.get('annual_program_contact_person_name'), '')
        self.assertEqual(form.initial.get('annual_program_contact_person_email'), '')
        self.assertEqual(form.initial.get('communication_to_the_candidate'), '')

        # Prerequisite courses
        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.admission.determined_academic_year),
            LearningUnitYearFactory(academic_year=self.admission.determined_academic_year),
        ]
        self.admission.prerequisite_courses.set(prerequisite_courses)
        self.admission.with_prerequisite_courses = True

        self.admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_form']

        # Prerequisite courses
        self.assertEqual(form.initial.get('with_prerequisite_courses'), True)
        self.assertCountEqual(
            form.initial.get('prerequisite_courses'),
            [
                prerequisite_courses[0].acronym,
                prerequisite_courses[1].acronym,
            ],
        )
        self.assertCountEqual(
            form.fields['prerequisite_courses'].choices,
            [
                (
                    prerequisite_courses[0].acronym,
                    f'{prerequisite_courses[0].acronym} - {prerequisite_courses[0].complete_title_i18n}',
                ),
                (
                    prerequisite_courses[1].acronym,
                    f'{prerequisite_courses[1].acronym} - {prerequisite_courses[1].complete_title_i18n}',
                ),
            ],
        )

    def test_approval_decision_form_submitting_with_invalid_data(self):
        self.client.force_login(user=self.fac_manager_user)

        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.admission.determined_academic_year),
        ]

        response = self.client.post(
            self.url,
            data={
                "cdd-decision-approval-prerequisite_courses": [prerequisite_courses[0].acronym, "UNKNOWN_ACRONYM"],
                'cdd-decision-approval-another_training': True,
                'cdd-decision-approval-with_prerequisite_courses': 'True',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_form']

        self.assertFalse(form.is_valid())

        self.assertCountEqual(
            form.fields['prerequisite_courses'].choices,
            [
                (
                    prerequisite_courses[0].acronym,
                    f'{prerequisite_courses[0].acronym} - {prerequisite_courses[0].complete_title_i18n}',
                ),
            ],
        )
        self.assertIn(
            'Sélectionnez des choix valides. "UNKNOWN_ACRONYM" n’en fait pas partie.',
            form.errors.get('prerequisite_courses', []),
        )

    @freezegun.freeze_time('2022-01-01')
    def test_approval_decision_form_submitting_with_valid_data(self):
        self.client.force_login(user=self.fac_manager_user)

        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.admission.determined_academic_year),
        ]

        # No data
        response = self.client.post(self.url, data={}, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_form']

        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)
        self.assertEqual(
            self.admission.checklist['current']['decision_cdd']['statut'],
            ChoixStatutChecklist.INITIAL_CANDIDAT.name,
        )
        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.admission.cdd_approval_certificate, [])
        self.assertIsNone(self.admission.with_prerequisite_courses)
        self.assertFalse(self.admission.prerequisite_courses.exists())
        self.assertEqual(self.admission.prerequisite_courses_fac_comment, '')
        self.assertEqual(self.admission.annual_program_contact_person_name, '')
        self.assertEqual(self.admission.annual_program_contact_person_email, '')
        self.assertEqual(self.admission.communication_to_the_candidate, '')

        # Some prerequisite courses are required but no one is specified for now
        response = self.client.post(
            self.url,
            data={
                "cdd-decision-approval-prerequisite_courses": [],
                'cdd-decision-approval-with_prerequisite_courses': 'True',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_form']

        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertTrue(self.admission.with_prerequisite_courses)
        self.assertFalse(self.admission.prerequisite_courses.exists())

        # No prerequisite course is required
        response = self.client.post(
            self.url,
            data={
                'cdd-decision-approval-with_prerequisite_courses': 'False',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_form']

        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertFalse(self.admission.with_prerequisite_courses)
        self.assertFalse(self.admission.prerequisite_courses.exists())

        # Full data
        response = self.client.post(
            self.url,
            data={
                "cdd-decision-approval-prerequisite_courses": [
                    prerequisite_courses[0].acronym,
                ],
                'cdd-decision-approval-with_prerequisite_courses': 'True',
                'cdd-decision-approval-prerequisite_courses_fac_comment': 'Comment about the additional trainings',
                'cdd-decision-approval-annual_program_contact_person_name': 'John Doe',
                'cdd-decision-approval-annual_program_contact_person_email': 'john.doe@example.be',
                'cdd-decision-approval-communication_to_the_candidate': 'Communication to the candidate',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_form']

        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)
        self.assertEqual(
            self.admission.checklist['current']['decision_cdd']['statut'],
            ChoixStatutChecklist.INITIAL_CANDIDAT.name,
        )
        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.admission.cdd_approval_certificate, [])
        self.assertEqual(self.admission.with_prerequisite_courses, True)
        prerequisite_courses = self.admission.prerequisite_courses.all()
        self.assertEqual(len(prerequisite_courses), 1)
        self.assertEqual(prerequisite_courses[0], prerequisite_courses[0])
        self.assertEqual(
            self.admission.prerequisite_courses_fac_comment,
            'Comment about the additional trainings',
        )
        self.assertEqual(self.admission.annual_program_contact_person_name, 'John Doe')
        self.assertEqual(self.admission.annual_program_contact_person_email, 'john.doe@example.be')
        self.assertEqual(self.admission.communication_to_the_candidate, 'Communication to the candidate')

    def test_approval_decision_is_not_possible_if_the_current_status_is_closed(self):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.checklist['current']['decision_cdd']['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        self.admission.checklist['current']['decision_cdd']['extra'] = {'decision': DecisionCDDEnum.CLOTURE.name}
        self.admission.save()

        response = self.client.post(
            self.url,
            data={
                'cdd-decision-approval-prerequisite_courses': [],
                'cdd-decision-approval-with_prerequisite_courses': 'True',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_form']
        self.assertTrue(form.is_valid())

        self.assertIn(
            gettext('It is not possible to go from the "Closed" status to this status.'),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has not been updated
        self.admission.refresh_from_db()

        self.assertFalse(self.admission.with_prerequisite_courses)
        self.assertFalse(self.admission.prerequisite_courses.exists())


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
@freezegun.freeze_time('2022-01-01')
class CddApprovalFinalDecisionViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.default_data = {
            'cdd-decision-approval-final-subject': 'Subject',
            'cdd-decision-approval-final-body': 'Body',
        }

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            submitted=True,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        self.default_checklist = copy.deepcopy(self.admission.checklist)
        self.url = resolve_url(
            'admission:doctorate:cdd-decision-approval-final',
            uuid=self.admission.uuid,
        )
        self.file_uuid = uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')

        self.confirm_remote_upload_patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = str(self.file_uuid)
        self.addCleanup(self.confirm_remote_upload_patcher.stop)

        self.confirm_multiple_remote_upload_patcher = mock.patch(
            'osis_document.contrib.fields.FileField._confirm_multiple_upload'
        )
        patched = self.confirm_multiple_remote_upload_patcher.start()
        patched.side_effect = lambda _, value, __: [str(self.file_uuid)] if value else []
        self.addCleanup(self.confirm_multiple_remote_upload_patcher.stop)

        self.get_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf", "size": 1}
        self.addCleanup(self.get_remote_metadata_patcher.stop)

        self.get_remote_token_patcher = mock.patch('osis_document.api.utils.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'foobar'
        self.addCleanup(self.get_remote_token_patcher.stop)

        patcher = patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {
            document_uuid: f'token-{index}' for index, document_uuid in enumerate(uuids)
        }
        self.addCleanup(patcher.stop)

        self.get_several_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        patched = self.get_several_remote_metadata_patcher.start()
        patched.return_value = {"foo": {"name": "test.pdf", "size": 1}}
        self.addCleanup(self.get_several_remote_metadata_patcher.stop)

        self.save_raw_content_remotely_patcher = mock.patch('osis_document.utils.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'
        self.addCleanup(self.save_raw_content_remotely_patcher.stop)

        patcher = mock.patch('admission.exports.utils.change_remote_metadata')
        self.change_remote_metadata_patcher = patcher.start()
        self.change_remote_metadata_patcher.return_value = 'a-token'
        self.addCleanup(patcher.stop)

        # Mock weasyprint
        patcher = mock.patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        self.get_pdf_from_template_patcher = patcher.start()
        self.addCleanup(patcher.stop)

    def test_cdd_approval_final_decision_is_forbidden_with_fac_user_if_the_admission_is_not_in_specific_statuses(self):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name
        self.admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_cdd_approval_final_decision_is_forbidden_with_sic_user_if_the_admission_is_not_in_specific_statuses(self):
        self.client.force_login(user=self.sic_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name
        self.admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_cdd_approval_final_decision_with_fac_user_in_specific_statuses(self, frozen_time):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.with_prerequisite_courses = None
        self.admission.are_secondary_studies_access_title = True
        self.admission.save()

        # Invalid form data -> We need to specify the subject and the body of the email
        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_final_form']
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('subject', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('body', []))

        self.admission.with_prerequisite_courses = False
        self.admission.are_secondary_studies_access_title = False
        self.admission.save()

        # Invalid request -> We need to choose an access title
        response = self.client.post(self.url, data=self.default_data, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            gettext(
                'Please select in the previous experience, the diploma(s), or non-academic activity(ies) giving '
                'access to the chosen program.'
            ),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has not been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)

        frozen_time.move_to('2022-01-03')

        # Valid request
        self.admission.are_secondary_studies_access_title = True
        self.admission.save(update_fields=['are_secondary_studies_access_title'])

        response = self.client.post(self.url, data=self.default_data, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name)
        self.assertEqual(
            self.admission.checklist['current']['decision_cdd']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.admission.approved_by_cdd_at, datetime.datetime.now())

        # A certificate has been generated
        self.assertEqual(self.admission.cdd_approval_certificate, [self.file_uuid])

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('proposition', pdf_context)
        self.assertEqual(pdf_context['proposition'].uuid, self.admission.uuid)

        self.assertIn('groupe_supervision', pdf_context)
        self.assertIsNotNone(pdf_context['groupe_supervision'])

        self.assertIn('cdd_president', pdf_context)

        # Check that an entry in the history has been created
        history_entries = HistoryEntry.objects.filter(object_uuid=self.admission.uuid).order_by('-id')

        self.assertEqual(len(history_entries), 2)

        self.assertEqual(
            history_entries[0].author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertEqual(
            history_entries[0].message_fr,
            'La CDD a informé le SIC de son acceptation.',
        )

        self.assertEqual(
            history_entries[0].message_en,
            'The CDD informed the SIC of its approval.',
        )

        self.assertCountEqual(
            history_entries[0].tags,
            ['proposition', 'cdd-decision', 'approval', 'status-changed'],
        )

        self.assertEqual(
            history_entries[1].author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertCountEqual(
            history_entries[1].tags,
            ['proposition', 'cdd-decision', 'approval', 'message'],
        )

        # Check that a notication has been planned
        notifications = EmailNotification.objects.filter(person=self.admission.candidate)

        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.admission.candidate.private_email)
        self.assertEqual(email_object['Subject'], 'Subject')
        self.assertIn('Body', notifications[0].payload)

    @freezegun.freeze_time('2022-01-01')
    def test_cdd_approval_final_decision_with_fac_user_with_secondary_studies_as_access_title(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, data=self.default_data, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            gettext(
                'Please select in the previous experience, the diploma(s), or non-academic activity(ies) giving '
                'access to the chosen program.'
            ),
            [m.message for m in response.context['messages']],
        )

        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)

        self.admission.are_secondary_studies_access_title = True
        self.admission.save(update_fields=['are_secondary_studies_access_title'])

        response = self.client.post(self.url, data=self.default_data, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name)

    def test_cdd_approval_final_decision_is_not_possible_if_the_current_status_is_closed(self):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.checklist['current']['decision_cdd']['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        self.admission.checklist['current']['decision_cdd']['extra'] = {'decision': DecisionCDDEnum.CLOTURE.name}
        self.admission.save()

        self.admission.are_secondary_studies_access_title = True
        self.admission.save(update_fields=['are_secondary_studies_access_title'])

        response = self.client.post(self.url, data=self.default_data, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_final_form']
        self.assertTrue(form.is_valid())

        self.assertIn(
            gettext('It is not possible to go from the "Closed" status to this status.'),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has not been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)

    @freezegun.freeze_time('2022-01-01')
    def test_cdd_approval_final_decision_with_fac_user_with_a_cv_academic_experience_as_access_title(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, data=self.default_data, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            gettext(
                'Please select in the previous experience, the diploma(s), or non-academic activity(ies) giving '
                'access to the chosen program.'
            ),
            [m.message for m in response.context['messages']],
        )

        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)

        academic_experience = EducationalExperience.objects.filter(
            person=self.admission.candidate,
        ).first()

        academic_experience.obtained_diploma = True
        academic_experience.save()

        admission_educational_valuated_experience = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.admission,
            educationalexperience=academic_experience,
            is_access_title=True,
        )

        response = self.client.post(self.url, data=self.default_data, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name)

    @freezegun.freeze_time('2022-01-01')
    def test_cdd_approval_final_decision_with_fac_user_with_a_cv_non_academic_experience_as_access_title(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, data=self.default_data, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            gettext(
                'Please select in the previous experience, the diploma(s), or non-academic activity(ies) giving '
                'access to the chosen program.'
            ),
            [m.message for m in response.context['messages']],
        )

        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)

        non_academic_experience = ProfessionalExperience.objects.filter(
            person=self.admission.candidate,
        ).first()

        admission_non_educational_valuated_experience = AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=self.admission,
            professionalexperience=non_academic_experience,
            is_access_title=True,
        )

        response = self.client.post(self.url, data=self.default_data, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CddDecisionClosedViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(
            version__acronym=ENTITY_CDE,
            version__title='Commission doctorale 1',
        )
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            submitted=True,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        self.default_checklist = copy.deepcopy(self.admission.checklist)
        self.url = resolve_url(
            'admission:doctorate:cdd-decision-closed',
            uuid=self.admission.uuid,
        )

    def test_close_the_admission_is_forbidden_with_sic_user(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_close_the_admission_is_forbidden_with_fac_user_in_invalid_status(self):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.admission.save(update_fields=['status'])

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2023-01-01')
    def test_close_the_admission_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        self.assertNotIn(
            gettext('It is not possible to go from the "Closed" status to this status.'),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.CLOTUREE.name)

        cdd_decision_checklist = self.admission.checklist['current']['decision_cdd']

        self.assertEqual(cdd_decision_checklist['statut'], ChoixStatutChecklist.GEST_BLOCAGE.name)
        self.assertEqual(cdd_decision_checklist['extra'], {'decision': DecisionCDDEnum.CLOTURE.name})

        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(history_entry.message_fr, 'Le dossier a été clôturé par la CDD.')

        self.assertEqual(history_entry.message_en, 'The dossier has been closed by the CDD.')

        self.assertEqual(
            history_entry.author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertCountEqual(history_entry.tags, ['proposition', 'cdd-decision', 'closed', 'status-changed'])

        # Simulate that SIC sent to the CDD the admission
        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.save(update_fields=['status'])

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        self.assertIn(
            gettext('It is not possible to go from the "Closed" status to this status.'),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has not been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)

        # Check that no entry in the history has been created
        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.admission.uuid).count(), 1)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CddDecisionToProcessedViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(
            version__acronym=ENTITY_CDE,
            version__title='Commission doctorale 1',
        )
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            submitted=True,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        self.default_checklist = copy.deepcopy(self.admission.checklist)
        self.url = resolve_url(
            'admission:doctorate:cdd-decision-to-processed',
            uuid=self.admission.uuid,
        )

    def test_move_to_to_processed_status_is_forbidden_with_sic_user(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_move_to_to_processed_status_is_forbidden_with_fac_user_in_invalid_status(self):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.admission.save(update_fields=['status'])

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2023-01-01')
    def test_move_to_to_processed_status_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        self.assertNotIn(
            gettext('It is not possible to go from the "Closed" status to this status.'),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        cdd_decision_checklist = self.admission.checklist['current']['decision_cdd']

        self.assertEqual(cdd_decision_checklist['statut'], ChoixStatutChecklist.INITIAL_CANDIDAT.name)
        self.assertEqual(cdd_decision_checklist['extra'], {})

        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CddDecisionTakenInChargeViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(
            version__acronym=ENTITY_CDE,
            version__title='Commission doctorale 1',
        )
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            submitted=True,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        self.default_checklist = copy.deepcopy(self.admission.checklist)
        self.url = resolve_url(
            'admission:doctorate:cdd-decision-taken-in-charge',
            uuid=self.admission.uuid,
        )

    def test_move_to_taken_in_charge_status_is_forbidden_with_sic_user(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_move_to_taken_in_charge_status_is_forbidden_with_fac_user_in_invalid_status(self):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.admission.save(update_fields=['status'])

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2023-01-01')
    def test_move_to_taken_in_charge_status_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        self.assertNotIn(
            gettext('It is not possible to go from the "Closed" status to this status.'),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        cdd_decision_checklist = self.admission.checklist['current']['decision_cdd']

        self.assertEqual(cdd_decision_checklist['statut'], ChoixStatutChecklist.GEST_EN_COURS.name)
        self.assertEqual(cdd_decision_checklist['extra'], {})

        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        # Simulate that we are in the closed status
        closed_status = {
            'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
            'extra': {'decision': 'CLOTURE'},
        }
        self.admission.checklist['current']['decision_cdd'] = closed_status

        self.admission.save(update_fields=['checklist'])

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        self.assertIn(
            gettext('It is not possible to go from the "Closed" status to this status.'),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has not been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.checklist['current']['decision_cdd'], closed_status)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CddDecisionToCompleteBySicViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(
            version__acronym=ENTITY_CDE,
            version__title='Commission doctorale 1',
        )
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            submitted=True,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        self.default_checklist = copy.deepcopy(self.admission.checklist)
        self.url = resolve_url(
            'admission:doctorate:cdd-decision-to-complete-by-sic',
            uuid=self.admission.uuid,
        )

    def test_move_to_to_complete_by_sic_status_is_forbidden_with_sic_user(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_move_to_to_complete_by_sic_status_is_forbidden_with_fac_user_in_invalid_status(self):
        self.client.force_login(user=self.fac_manager_user)

        self.admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.admission.save(update_fields=['status'])

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2023-01-01')
    def test_move_to_to_complete_by_sic_status_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        self.assertNotIn(
            gettext('It is not possible to go from the "Closed" status to this status.'),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        cdd_decision_checklist = self.admission.checklist['current']['decision_cdd']

        self.assertEqual(cdd_decision_checklist['statut'], ChoixStatutChecklist.GEST_BLOCAGE.name)
        self.assertEqual(cdd_decision_checklist['extra'], {'decision': 'HORS_DECISION'})

        self.assertEqual(self.admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        # Simulate that we are in the closed status
        closed_status = {
            'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
            'extra': {'decision': 'CLOTURE'},
        }
        self.admission.checklist['current']['decision_cdd'] = closed_status

        self.admission.save(update_fields=['checklist'])

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        self.assertIn(
            gettext('It is not possible to go from the "Closed" status to this status.'),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has not been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.checklist['current']['decision_cdd'], closed_status)
