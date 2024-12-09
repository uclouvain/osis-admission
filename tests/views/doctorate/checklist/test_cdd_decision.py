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
from django.test import TestCase
from django.test import override_settings
from django.utils.translation import gettext
from osis_history.models import HistoryEntry
from osis_mail_template.models import MailTemplate
from osis_notification.models import EmailNotification

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import ENTITY_CDE
from admission.models import DoctorateAdmission
from admission.models.checklist import (
    AdditionalApprovalCondition,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    DecisionCDDEnum,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from admission.mail_templates import ADMISSION_EMAIL_CDD_REFUSAL_DOCTORATE
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import (
    AdmissionEducationalValuatedExperiencesFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
)
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from osis_profile.models import (
    EducationalExperience,
    ProfessionalExperience,
)


class CddDecisionViewTestCase(TestCase):
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
            'admission:doctorate:cdd-decision-change-status',
            uuid=self.admission.uuid,
            status=ChoixStatutChecklist.GEST_BLOCAGE.name,
        )

    def test_change_the_checklist_status_is_forbidden_with_sic_user(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_change_the_checklist_status_is_forbidden_with_fac_user_if_the_admission_has_just_been_confirmed(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_change_the_checklist_status_with_a_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        # TRAITEMENT_FAC > update the checklist status
        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.save()

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.checklist['current']['decision_cdd']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )

    def test_change_the_checklist_status_and_extra_data_with_a_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        # COMPLETEE_POUR_FAC > update the checklist status and the extra data
        self.admission.status = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC.name
        self.admission.save()

        response = self.client.post(self.url + '?decision=EN_DECISION', **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()
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

        # Replace the status and clean the extra data
        url = resolve_url(
            'admission:doctorate:cdd-decision-change-status',
            uuid=self.admission.uuid,
            status=ChoixStatutChecklist.INITIAL_CANDIDAT.name,
        )

        response = self.client.post(url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.checklist['current']['decision_cdd']['statut'],
            ChoixStatutChecklist.INITIAL_CANDIDAT.name,
        )
        self.assertEqual(self.admission.checklist['current']['decision_cdd']['extra'], {})


@override_settings(ADMISSION_BACKEND_LINK_PREFIX='https//example.com')
class CddDecisionSendToCddViewTestCase(TestCase):
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

        mail = MailTemplate.objects.get(
            identifier=ADMISSION_EMAIL_CDD_REFUSAL_DOCTORATE,
            language=settings.LANGUAGE_CODE_FR,
        )

        self.assertEqual(
            form.initial.get('subject'),
            mail.render_subject(
                tokens={
                    'admission_reference': f'-CDE21-{str(self.admission)}',
                },
            ),
        )

        teaching_campus = self.admission.training.educationgroupversion_set.first().root_group.main_teaching_campus
        self.assertEqual(
            form.initial.get('body'),
            mail.body_as_html(
                tokens={
                    'greetings': 'Cher',
                    'doctoral_commission': 'Commission doctorale 1',
                    'sender_name': f'{self.fac_manager_user.person.first_name} '
                    f'{self.fac_manager_user.person.last_name}',
                    'admission_reference': f'-CDE21-{str(self.admission)}',
                    'candidate_first_name': self.admission.candidate.first_name,
                    'candidate_last_name': self.admission.candidate.last_name,
                    'training_acronym': self.admission.training.acronym,
                    'training_title': self.admission.training.title,
                    'training_campus': teaching_campus.name,
                    'academic_year': self.admission.training.academic_year.year,
                }
            ),
        )

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
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('subject', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('body', []))

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_refusal_decision_form_submitting_with_valid_data(self, frozen_time):
        self.client.force_login(user=self.fac_manager_user)

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'cdd-decision-refusal-subject': 'Subject',
                'cdd-decision-refusal-body': 'Body',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_refusal_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.INSCRIPTION_REFUSEE.name)
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

        # Check that a notication has been planned
        notifications = EmailNotification.objects.filter(person=self.admission.candidate)

        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.admission.candidate.private_email)
        self.assertEqual(email_object['Subject'], 'Subject')
        self.assertIn('Body', notifications[0].payload)

        # Check that entries in the history have been created
        history_entries = HistoryEntry.objects.filter(object_uuid=self.admission.uuid).order_by('-id')

        self.assertEqual(len(history_entries), 2)

        self.assertEqual(
            history_entries[0].author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertEqual(
            history_entries[0].message_fr,
            'Le dossier a été refusé par la CDD.',
        )

        self.assertEqual(
            history_entries[0].message_en,
            'The dossier has been refused by the CDD.',
        )

        self.assertCountEqual(
            history_entries[0].tags,
            ['proposition', 'cdd-decision', 'refusal', 'status-changed'],
        )

        self.assertCountEqual(
            history_entries[1].tags,
            ['proposition', 'cdd-decision', 'refusal', 'message'],
        )

        self.assertEqual(
            history_entries[1].author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
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
        self.admission.program_planned_years_number = None
        self.admission.annual_program_contact_person_name = ''
        self.admission.annual_program_contact_person_email = ''
        self.admission.join_program_fac_comment = ''
        self.admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_form']

        self.assertEqual(form.initial.get('with_prerequisite_courses'), None)
        self.assertEqual(form.initial.get('prerequisite_courses'), [])
        self.assertEqual(form.initial.get('prerequisite_courses_fac_comment'), '')
        self.assertEqual(form.initial.get('program_planned_years_number'), None)
        self.assertEqual(form.initial.get('annual_program_contact_person_name'), '')
        self.assertEqual(form.initial.get('annual_program_contact_person_email'), '')
        self.assertEqual(form.initial.get('join_program_fac_comment'), '')

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
                "cdd-decision-approval-prerequisite_courses": [],
                'cdd-decision-approval-with_prerequisite_courses': 'True',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_form']

        self.assertFalse(form.is_valid())

        # Missing fields
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('program_planned_years_number', []))
        self.assertNotIn(FIELD_REQUIRED_MESSAGE, form.errors.get('prerequisite_courses', []))

        response = self.client.post(
            self.url,
            data={
                'cdd-decision-approval-with_prerequisite_courses': 'False',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_form']

        self.assertFalse(form.is_valid())

        # Missing fields
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('program_planned_years_number', []))
        self.assertNotIn(FIELD_REQUIRED_MESSAGE, form.errors.get('prerequisite_courses', []))

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

        # Prerequisite courses
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

        response = self.client.post(
            self.url,
            data={
                "cdd-decision-approval-prerequisite_courses": [
                    prerequisite_courses[0].acronym,
                ],
                'cdd-decision-approval-with_prerequisite_courses': 'True',
                'cdd-decision-approval-prerequisite_courses_fac_comment': 'Comment about the additional trainings',
                'cdd-decision-approval-program_planned_years_number': 5,
                'cdd-decision-approval-annual_program_contact_person_name': 'John Doe',
                'cdd-decision-approval-annual_program_contact_person_email': 'john.doe@example.be',
                'cdd-decision-approval-join_program_fac_comment': 'Comment about the join program',
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
        self.assertEqual(self.admission.program_planned_years_number, 5)
        self.assertEqual(self.admission.annual_program_contact_person_name, 'John Doe')
        self.assertEqual(self.admission.annual_program_contact_person_email, 'john.doe@example.be')
        self.assertEqual(self.admission.join_program_fac_comment, 'Comment about the join program')


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
            program_planned_years_number=5,
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
        self.admission.program_planned_years_number = None
        self.admission.are_secondary_studies_access_title = True
        self.admission.save()

        # Invalid form data -> We need to specify the subject and the body of the email
        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['cdd_decision_approval_final_form']
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('subject', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('body', []))

        # Invalid request -> We need to specify the missing data related to the approval decision
        response = self.client.post(self.url, data=self.default_data, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            gettext(
                'When accepting a proposition, all the required information in the approval form must be specified.'
            ),
            [m.message for m in response.context['messages']],
        )

        self.admission.with_prerequisite_courses = False
        self.admission.program_planned_years_number = 5
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
