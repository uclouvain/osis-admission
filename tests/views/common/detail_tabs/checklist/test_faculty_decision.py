# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid
from typing import List
from unittest import mock

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.test import override_settings
from osis_history.models import HistoryEntry

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    MotifRefusFacultaireNonSpecifieException,
    InformationsAcceptationFacultaireNonSpecifieesException,
)
from admission.tests.factories.faculty_decision import RefusalReasonFactory, AdditionalApprovalConditionFactory
from admission.tests.factories.general_education import (
    GeneralEducationTrainingFactory,
    GeneralEducationAdmissionFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


class FacultyDecisionViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )
        self.default_checklist = copy.deepcopy(self.general_admission.checklist)
        self.url = resolve_url(
            'admission:general-education:fac-decision-change-status',
            uuid=self.general_admission.uuid,
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
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save()

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )

    def test_change_the_checklist_status_and_extra_data_with_a_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        # COMPLETEE_POUR_FAC > update the checklist status and the extra data
        self.general_admission.status = ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC.name
        self.general_admission.save()

        response = self.client.post(self.url + '?decision=1', **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['extra'],
            {
                'decision': '1',
            },
        )


class FacultyDecisionSendToFacultyViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )
        self.default_checklist = copy.deepcopy(self.general_admission.checklist)
        self.url = resolve_url(
            'admission:general-education:fac-decision-send-to-faculty',
            uuid=self.general_admission.uuid,
        )

    def test_send_to_faculty_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_send_to_faculty_is_forbidden_with_sic_user_if_the_admission_is_not_in_sic_statuses(self):
        self.client.force_login(user=self.sic_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name
        self.general_admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2022-01-01')
    @mock.patch(
        'admission.infrastructure.admission.formation_generale.domain.service.notification.send_mail_to_generic_email'
    )
    def test_send_to_faculty_with_sic_user_in_sic_statuses(self, send_mail):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)

        # Check that a message has been submitted
        send_mail.assert_called()

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.message_fr,
            'Un mail informant de la soumission du dossier en faculté a été envoyé à '
            '"mail-inscription-formation-a-developper@uclouvain.be" le 1 Janvier 2022 00:00.',
        )

        self.assertEqual(
            history_entry.message_en,
            'An e-mail notifying that the dossier had been submitted to the faculty was sent to '
            '"mail-inscription-formation-a-developper@uclouvain.be" on 1 Janvier 2022 00:00.',
        )

        self.assertEqual(
            history_entry.author, f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}'
        )
        self.assertCountEqual(
            history_entry.tags,
            [
                'proposition',
                'fac-decision',
                'send-to-fac',
                'status-changed',
            ],
        )


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class FacultyDecisionSendToSicViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )
        self.default_checklist = copy.deepcopy(self.general_admission.checklist)
        self.url = resolve_url(
            'admission:general-education:fac-decision-send-to-sic',
            uuid=self.general_admission.uuid,
        )
        self.file_uuid = uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')

        self.confirm_remote_upload_patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = str(self.file_uuid)

        self.get_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf"}

        self.get_remote_token_patcher = mock.patch('osis_document.api.utils.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'foobar'

        self.save_raw_content_remotely_patcher = mock.patch('osis_document.utils.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'

        patcher = mock.patch('admission.exports.utils.change_remote_metadata')
        self.change_remote_metadata_patcher = patcher.start()
        self.change_remote_metadata_patcher.return_value = 'a-token'
        self.addCleanup(patcher.stop)

        # Mock weasyprint
        patcher = mock.patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_send_to_sic_is_forbidden_with_sic_user(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_send_to_sic_is_forbidden_with_fac_user_if_the_admission_is_not_in_specific_statuses(self):
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name
        self.general_admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2022-01-01')
    def test_send_to_sic_with_fac_user_in_specific_statuses_to_refuse(self):
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.fac_refusal_reason = None
        self.general_admission.other_fac_refusal_reason = ''
        self.general_admission.fac_refusal_certificate = []
        self.general_admission.save()

        # Invalid request -> we need to specify that it is a refusal
        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 400)

        # Invalid request -> We need to specify a reason
        with self.assertRaises(MultipleBusinessExceptions) as context:
            response = self.client.post(self.url + '?refusal=1', **self.default_headers)
            self.assertEqual(response.status_code, 400)
            self.assertIsInstance(context.exception.exceptions.pop(), MotifRefusFacultaireNonSpecifieException)

        self.general_admission.other_fac_refusal_reason = 'test'
        self.general_admission.save()

        # Valid request
        response = self.client.post(self.url + '?refusal=1', **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['extra'],
            {
                'decision': '1',
            },
        )

        # A certificate has been generated
        self.assertEqual(self.general_admission.fac_refusal_certificate, [self.file_uuid])

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertEqual(
            history_entry.message_fr,
            'La faculté a informé le SIC de son refus.',
        )

        self.assertEqual(
            history_entry.message_en,
            'The faculty informed the SIC of its refusal.',
        )

        self.assertCountEqual(
            history_entry.tags,
            ['proposition', 'fac-decision', 'refusal-send-to-sic', 'status-changed'],
        )

    @freezegun.freeze_time('2022-01-01')
    def test_send_to_sic_with_fac_user_in_specific_statuses_to_approve(self):
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.with_additional_approval_conditions = None
        self.general_admission.with_prerequisite_courses = None
        self.general_admission.program_planned_years_number = None
        self.general_admission.save()

        # Invalid request -> we need to specify that it is an approval
        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 400)

        # Invalid request -> We need to specify the
        with self.assertRaises(MultipleBusinessExceptions) as context:
            response = self.client.post(self.url + '?approval=1', **self.default_headers)
            self.assertEqual(response.status_code, 400)
            self.assertIsInstance(
                context.exception.exceptions.pop(),
                InformationsAcceptationFacultaireNonSpecifieesException,
            )

        self.general_admission.with_additional_approval_conditions = False
        self.general_admission.with_prerequisite_courses = False
        self.general_admission.program_planned_years_number = 5
        self.general_admission.save()

        # Valid request
        response = self.client.post(self.url + '?approval=1', **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )

        # A certificate has been generated
        self.assertEqual(self.general_admission.fac_approval_certificate, [self.file_uuid])

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertEqual(
            history_entry.message_fr,
            'La faculté a informé le SIC de son acceptation.',
        )

        self.assertEqual(
            history_entry.message_en,
            'The faculty informed the SIC of its approval.',
        )

        self.assertCountEqual(
            history_entry.tags,
            ['proposition', 'fac-decision', 'approval-send-to-sic', 'status-changed'],
        )


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class FacultyRefusalDecisionViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name,
        )
        self.default_checklist = copy.deepcopy(self.general_admission.checklist)
        self.url = resolve_url(
            'admission:general-education:fac-decision-refusal',
            uuid=self.general_admission.uuid,
        )
        self.file_uuid = uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')

        self.confirm_remote_upload_patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = str(self.file_uuid)

        self.get_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf"}

        self.get_remote_token_patcher = mock.patch('osis_document.api.utils.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'foobar'

        self.save_raw_content_remotely_patcher = mock.patch('osis_document.utils.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'

        patcher = mock.patch('admission.exports.utils.change_remote_metadata')
        self.change_remote_metadata_patcher = patcher.start()
        self.change_remote_metadata_patcher.return_value = 'a-token'
        self.addCleanup(patcher.stop)

        # Mock weasyprint
        patcher = mock.patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_submit_refusal_decision_is_forbidden_with_sic_user(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_submit_refusal_decision_is_forbidden_with_fac_user_if_the_admission_is_not_in_specific_statuses(self):
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name
        self.general_admission.save()

        response = self.client.post(self.url, data={'save_transfer': '1'}, **self.default_headers)

        self.assertEqual(response.status_code, 403)

        self.general_admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.general_admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_refusal_decision_form_initialization(self):
        self.client.force_login(user=self.fac_manager_user)

        refusal_reason = RefusalReasonFactory()

        # The reason is empty
        self.general_admission.fac_refusal_reason = None
        self.general_admission.other_fac_refusal_reason = ''

        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']

        self.assertEqual(form.initial.get('reason'), None)
        self.assertEqual(form.initial.get('other_reason'), '')
        self.assertEqual(form.initial.get('category'), '')

        # The existing reason is selected
        self.general_admission.fac_refusal_reason = refusal_reason
        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']

        self.assertEqual(form.initial.get('reason'), refusal_reason)
        self.assertEqual(form.initial.get('other_reason'), '')
        self.assertEqual(form.initial.get('category'), refusal_reason.category)

        # The other reason is selected
        self.general_admission.fac_refusal_reason = None
        self.general_admission.other_fac_refusal_reason = 'Other reason'
        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']

        self.assertEqual(form.initial.get('reason'), None)
        self.assertEqual(form.initial.get('other_reason'), 'Other reason')
        self.assertEqual(form.initial.get('category'), 'OTHER')

    def test_refusal_decision_form_submitting_with_invalid_data(self):
        self.client.force_login(user=self.fac_manager_user)

        refusal_reason = RefusalReasonFactory()

        # Check form submitting
        self.general_admission.fac_refusal_reason = None
        self.general_admission.other_fac_refusal_reason = ''
        self.general_admission.save()

        # No chosen category
        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('category', []))

        # Chosen category but no chosen reason
        response = self.client.post(
            self.url,
            data={
                'fac-decision-refusal-category': refusal_reason.category_id,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('reason', []))

        # Chosen category (=OTHER) but no specified other reason
        response = self.client.post(
            self.url,
            data={
                'fac-decision-refusal-category': 'OTHER',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('other_reason', []))

    def test_refusal_decision_form_submitting_with_valid_data(self):
        self.client.force_login(user=self.fac_manager_user)

        refusal_reason = RefusalReasonFactory()

        # Chosen category and existing reason
        response = self.client.post(
            self.url,
            data={
                'fac-decision-refusal-category': refusal_reason.category_id,
                'fac-decision-refusal-reason': refusal_reason.uuid,
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.fac_refusal_reason, refusal_reason)
        self.assertEqual(self.general_admission.other_fac_refusal_reason, '')
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['extra'],
            {'decision': '1'},
        )

        # Chosen category (=OTHER) and specified other reason
        response = self.client.post(
            self.url,
            data={
                'fac-decision-refusal-category': 'OTHER',
                'fac-decision-refusal-other_reason': 'My other reason',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.fac_refusal_reason, None)
        self.assertEqual(self.general_admission.other_fac_refusal_reason, 'My other reason')

    def test_refusal_decision_form_submitting_with_transfer_to_sic(self):
        self.client.force_login(user=self.fac_manager_user)

        refusal_reason = RefusalReasonFactory()

        # Chosen category and reason and transfer to SIC
        response = self.client.post(
            self.url,
            data={
                'fac-decision-refusal-category': refusal_reason.category_id,
                'fac-decision-refusal-reason': refusal_reason.uuid,
                'save-transfer': '1',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.fac_refusal_reason, refusal_reason)
        self.assertEqual(self.general_admission.other_fac_refusal_reason, '')
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['extra'],
            {'decision': '1'},
        )

        # A certificate has been generated
        self.assertEqual(self.general_admission.fac_refusal_certificate, [self.file_uuid])

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertEqual(
            history_entry.message_fr,
            'La faculté a informé le SIC de son refus.',
        )

        self.assertEqual(
            history_entry.message_en,
            'The faculty informed the SIC of its refusal.',
        )

        self.assertCountEqual(
            history_entry.tags,
            ['proposition', 'fac-decision', 'refusal-send-to-sic', 'status-changed'],
        )


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class FacultyApprovalDecisionViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name,
            determined_academic_year=self.academic_years[0],
        )
        self.default_checklist = copy.deepcopy(self.general_admission.checklist)
        self.url = resolve_url(
            'admission:general-education:fac-decision-approval',
            uuid=self.general_admission.uuid,
        )
        self.file_uuid = uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')

        self.confirm_remote_upload_patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = str(self.file_uuid)

        self.get_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf"}

        self.get_remote_token_patcher = mock.patch('osis_document.api.utils.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'foobar'

        self.save_raw_content_remotely_patcher = mock.patch('osis_document.utils.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'

        patcher = mock.patch('admission.exports.utils.change_remote_metadata')
        self.change_remote_metadata_patcher = patcher.start()
        self.change_remote_metadata_patcher.return_value = 'a-token'
        self.addCleanup(patcher.stop)

        # Mock weasyprint
        patcher = mock.patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_submit_approval_decision_is_forbidden_with_sic_user(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_submit_approval_decision_is_forbidden_with_fac_user_if_the_admission_is_not_in_specific_statuses(self):
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name
        self.general_admission.save()

        response = self.client.post(self.url, data={'save_transfer': '1'}, **self.default_headers)

        self.assertEqual(response.status_code, 403)

        self.general_admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.general_admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_approval_decision_form_initialization(self):
        self.client.force_login(user=self.fac_manager_user)

        # No approval data
        self.general_admission.with_additional_approval_conditions = None
        self.general_admission.additional_approval_conditions.set([])
        self.general_admission.free_additional_approval_conditions = []
        self.general_admission.other_training_accepted_by_fac = None
        self.general_admission.with_prerequisite_courses = None
        self.general_admission.prerequisite_courses.set([])
        self.general_admission.prerequisite_courses_fac_comment = ''
        self.general_admission.program_planned_years_number = None
        self.general_admission.annual_program_contact_person_name = ''
        self.general_admission.annual_program_contact_person_email = ''
        self.general_admission.join_program_fac_comment = ''
        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']

        self.assertEqual(form.initial.get('another_training'), False)
        self.assertEqual(form.initial.get('other_training_accepted_by_fac'), None)
        self.assertEqual(form.initial.get('with_prerequisite_courses'), None)
        self.assertEqual(form.initial.get('prerequisite_courses'), [])
        self.assertEqual(form.initial.get('prerequisite_courses_fac_comment'), '')
        self.assertEqual(form.initial.get('program_planned_years_number'), None)
        self.assertEqual(form.initial.get('annual_program_contact_person_name'), '')
        self.assertEqual(form.initial.get('annual_program_contact_person_email'), '')
        self.assertEqual(form.initial.get('join_program_fac_comment'), '')
        self.assertEqual(form.initial.get('with_additional_approval_conditions'), None)
        self.assertEqual(form.initial.get('all_additional_approval_conditions'), [])

        # Another training
        self.general_admission.other_training_accepted_by_fac = self.training

        # Prerequisite courses
        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.general_admission.determined_academic_year),
            LearningUnitYearFactory(academic_year=self.general_admission.determined_academic_year),
        ]
        self.general_admission.prerequisite_courses.set(prerequisite_courses)
        self.general_admission.with_prerequisite_courses = True

        # Additional approval conditions
        approval_conditions = [
            AdditionalApprovalConditionFactory(),
            AdditionalApprovalConditionFactory(),
        ]
        self.general_admission.additional_approval_conditions.set(approval_conditions)
        self.general_admission.with_additional_approval_conditions = True
        self.general_admission.free_additional_approval_conditions = [
            'My first free condition',
            'My second free condition',
        ]

        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']

        # Another training
        self.assertEqual(form.initial.get('another_training'), True)
        self.assertEqual(
            form.initial.get('other_training_accepted_by_fac'),
            self.general_admission.other_training_accepted_by_fac.uuid,
        )
        self.assertEqual(
            form.fields['other_training_accepted_by_fac'].queryset[0].uuid,
            self.general_admission.other_training_accepted_by_fac.uuid,
        )

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

        # Additional approval conditions
        self.assertEqual(form.initial.get('with_additional_approval_conditions'), True)
        self.assertCountEqual(
            form.initial.get('all_additional_approval_conditions'),
            [
                approval_conditions[0].uuid,
                approval_conditions[1].uuid,
                self.general_admission.free_additional_approval_conditions[0],
                self.general_admission.free_additional_approval_conditions[1],
            ],
        )
        self.assertCountEqual(
            form.fields['all_additional_approval_conditions'].choices,
            [
                (
                    self.general_admission.free_additional_approval_conditions[0],
                    self.general_admission.free_additional_approval_conditions[0],
                ),
                (
                    self.general_admission.free_additional_approval_conditions[1],
                    self.general_admission.free_additional_approval_conditions[1],
                ),
                (
                    approval_conditions[0].uuid,
                    approval_conditions[0].name_fr,
                ),
                (
                    approval_conditions[1].uuid,
                    approval_conditions[1].name_fr,
                ),
            ],
        )

    def test_approval_decision_form_submitting_with_invalid_data(self):
        self.client.force_login(user=self.fac_manager_user)

        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.general_admission.determined_academic_year),
        ]

        approval_conditions = [
            AdditionalApprovalConditionFactory(),
        ]

        response = self.client.post(
            self.url,
            data={
                "fac-decision-approval-prerequisite_courses": [prerequisite_courses[0].acronym, "UNKNOWN_ACRONYM"],
                'fac-decision-approval-another_training': True,
                'fac-decision-approval-with_prerequisite_courses': 'True',
                'fac-decision-approval-with_additional_approval_conditions': 'True',
                'fac-decision-approval-all_additional_approval_conditions': [
                    approval_conditions[0].uuid,
                    'Free condition',
                ],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']

        self.assertFalse(form.is_valid())

        # Other course
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('other_training_accepted_by_fac', []))

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

        # Additional approval conditions
        self.assertCountEqual(
            form.fields['all_additional_approval_conditions'].choices,
            [
                (approval_conditions[0].uuid, approval_conditions[0].name_fr),
                ('Free condition', 'Free condition'),
            ],
        )

    def test_approval_decision_form_submitting_with_valid_data(self):
        self.client.force_login(user=self.fac_manager_user)

        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.general_admission.determined_academic_year),
        ]

        approval_conditions = [
            AdditionalApprovalConditionFactory(),
        ]

        response = self.client.post(
            self.url,
            data={
                "fac-decision-approval-prerequisite_courses": [
                    prerequisite_courses[0].acronym,
                ],
                'fac-decision-approval-another_training': True,
                'fac-decision-approval-other_training_accepted_by_fac': self.general_admission.training.uuid,
                'fac-decision-approval-with_prerequisite_courses': 'True',
                'fac-decision-approval-with_additional_approval_conditions': 'True',
                'fac-decision-approval-all_additional_approval_conditions': [
                    approval_conditions[0].uuid,
                    'Free condition',
                ],
                'fac-decision-approval-prerequisite_courses_fac_comment': 'Comment about the additional trainings',
                'fac-decision-approval-program_planned_years_number': 5,
                'fac-decision-approval-annual_program_contact_person_name': 'John Doe',
                'fac-decision-approval-annual_program_contact_person_email': 'john.doe@example.be',
                'fac-decision-approval-join_program_fac_comment': 'Comment about the join program',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']

        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.general_admission.fac_approval_certificate, [])
        self.assertEqual(self.general_admission.with_additional_approval_conditions, True)
        approval_conditions = self.general_admission.additional_approval_conditions.all()
        self.assertEqual(len(approval_conditions), 1)
        self.assertEqual(approval_conditions[0], approval_conditions[0])
        self.assertEqual(self.general_admission.free_additional_approval_conditions, ['Free condition'])
        self.assertEqual(self.general_admission.other_training_accepted_by_fac, self.general_admission.training)
        self.assertEqual(self.general_admission.with_prerequisite_courses, True)
        prerequisite_courses = self.general_admission.prerequisite_courses.all()
        self.assertEqual(len(prerequisite_courses), 1)
        self.assertEqual(prerequisite_courses[0], prerequisite_courses[0])
        self.assertEqual(
            self.general_admission.prerequisite_courses_fac_comment,
            'Comment about the additional trainings',
        )
        self.assertEqual(self.general_admission.program_planned_years_number, 5)
        self.assertEqual(self.general_admission.annual_program_contact_person_name, 'John Doe')
        self.assertEqual(self.general_admission.annual_program_contact_person_email, 'john.doe@example.be')
        self.assertEqual(self.general_admission.join_program_fac_comment, 'Comment about the join program')

    def test_approval_decision_form_submitting_with_transfer_to_sic(self):
        self.client.force_login(user=self.fac_manager_user)

        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.general_admission.determined_academic_year),
        ]

        approval_conditions = [
            AdditionalApprovalConditionFactory(),
        ]

        response = self.client.post(
            self.url,
            data={
                "fac-decision-approval-prerequisite_courses": [
                    prerequisite_courses[0].acronym,
                ],
                'fac-decision-approval-another_training': True,
                'fac-decision-approval-other_training_accepted_by_fac': self.general_admission.training.uuid,
                'fac-decision-approval-with_prerequisite_courses': 'True',
                'fac-decision-approval-with_additional_approval_conditions': 'True',
                'fac-decision-approval-all_additional_approval_conditions': [
                    approval_conditions[0].uuid,
                    'Free condition',
                ],
                'fac-decision-approval-prerequisite_courses_fac_comment': 'Comment about the additional trainings',
                'fac-decision-approval-program_planned_years_number': 5,
                'fac-decision-approval-annual_program_contact_person_name': 'John Doe',
                'fac-decision-approval-annual_program_contact_person_email': 'john.doe@example.be',
                'fac-decision-approval-join_program_fac_comment': 'Comment about the join program',
                'save-transfer': '1',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']

        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.general_admission.fac_approval_certificate, [self.file_uuid])
        self.assertEqual(self.general_admission.with_additional_approval_conditions, True)
        approval_conditions = self.general_admission.additional_approval_conditions.all()
        self.assertEqual(len(approval_conditions), 1)
        self.assertEqual(approval_conditions[0], approval_conditions[0])
        self.assertEqual(self.general_admission.free_additional_approval_conditions, ['Free condition'])
        self.assertEqual(self.general_admission.other_training_accepted_by_fac, self.general_admission.training)
        self.assertEqual(self.general_admission.with_prerequisite_courses, True)
        prerequisite_courses = self.general_admission.prerequisite_courses.all()
        self.assertEqual(len(prerequisite_courses), 1)
        self.assertEqual(prerequisite_courses[0], prerequisite_courses[0])
        self.assertEqual(
            self.general_admission.prerequisite_courses_fac_comment,
            'Comment about the additional trainings',
        )
        self.assertEqual(self.general_admission.program_planned_years_number, 5)
        self.assertEqual(self.general_admission.annual_program_contact_person_name, 'John Doe')
        self.assertEqual(self.general_admission.annual_program_contact_person_email, 'john.doe@example.be')
        self.assertEqual(self.general_admission.join_program_fac_comment, 'Comment about the join program')

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertEqual(
            history_entry.message_fr,
            'La faculté a informé le SIC de son acceptation.',
        )

        self.assertEqual(
            history_entry.message_en,
            'The faculty informed the SIC of its approval.',
        )

        self.assertCountEqual(
            history_entry.tags,
            ['proposition', 'fac-decision', 'approval-send-to-sic', 'status-changed'],
        )
