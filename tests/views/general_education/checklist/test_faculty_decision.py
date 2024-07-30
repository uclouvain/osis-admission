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
from email.policy import default
from typing import List
from unittest import mock
from unittest.mock import patch

import freezegun
from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import TestCase
from django.test import override_settings
from django.utils.translation import gettext
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification

from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.checklist import (
    AdditionalApprovalCondition,
    RefusalReasonCategory,
    FreeAdditionalApprovalCondition,
)
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
    DecisionFacultaireEnum,
    PoursuiteDeCycle,
)
from admission.tests.factories.comment import CommentEntryFactory
from admission.tests.factories.curriculum import (
    AdmissionEducationalValuatedExperiencesFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
)
from admission.tests.factories.faculty_decision import (
    RefusalReasonFactory,
    AdditionalApprovalConditionFactory,
    FreeAdditionalApprovalConditionFactory,
)
from admission.tests.factories.general_education import (
    GeneralEducationTrainingFactory,
    GeneralEducationAdmissionFactory,
)
from admission.tests.factories.history import HistoryEntryFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from admission.tests.factories.secondary_studies import (
    ForeignHighSchoolDiplomaFactory,
    HighSchoolDiplomaAlternativeFactory,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.student import StudentFactory
from epc.models.enums.condition_acces import ConditionAcces
from epc.models.enums.decision_resultat_cycle import DecisionResultatCycle
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.enums.statut_inscription_programme_annuel import StatutInscriptionProgrammAnnuel
from epc.models.enums.type_duree import TypeDuree
from epc.models.enums.type_email_fonction_programme import TypeEmailFonctionProgramme
from epc.tests.factories.email_fonction_programme import EmailFonctionProgrammeFactory
from epc.tests.factories.inscription_programme_annuel import InscriptionProgrammeAnnuelFactory
from epc.tests.factories.inscription_programme_cycle import InscriptionProgrammeCycleFactory
from osis_profile.models import (
    EducationalExperience,
    ProfessionalExperience,
    BelgianHighSchoolDiploma,
    ForeignHighSchoolDiploma,
    HighSchoolDiplomaAlternative,
)


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
                'decision': DecisionFacultaireEnum.EN_DECISION.value,
            },
        )

        # Replace the status and clean the extra data
        url = resolve_url(
            'admission:general-education:fac-decision-change-status',
            uuid=self.general_admission.uuid,
            status=ChoixStatutChecklist.INITIAL_CANDIDAT.name,
        )

        response = self.client.post(url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.INITIAL_CANDIDAT.name,
        )
        self.assertEqual(self.general_admission.checklist['current']['decision_facultaire']['extra'], {})


@override_settings(ADMISSION_BACKEND_LINK_PREFIX='https//example.com')
class FacultyDecisionSendToFacultyViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            education_group_type__name=TrainingType.BACHELOR.name,
            academic_year=cls.academic_years[0],
            enrollment_campus__sic_enrollment_email='mons@campus.be',
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            cycle_pursuit=PoursuiteDeCycle.NO.name,
            determined_academic_year=self.academic_years[0],
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

        invalid_statuses = ChoixStatutPropositionGenerale.get_names_except(
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC,
            ChoixStatutPropositionGenerale.CONFIRMEE,
            ChoixStatutPropositionGenerale.RETOUR_DE_FAC,
        )

        for status in invalid_statuses:
            self.general_admission.status = status
            self.general_admission.save()

            response = self.client.post(self.url, **self.default_headers)

            self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2022-01-01')
    def test_send_to_faculty_with_sic_user_in_valid_sic_statuses(self):
        self.client.force_login(user=self.sic_manager_user)

        program_email = EmailFonctionProgrammeFactory(
            programme=self.general_admission.training.education_group,
            type=TypeEmailFonctionProgramme.DESTINATAIRE_ADMISSION.name,
            premiere_annee=True,
        )

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())

        # Check that a notification has been planned
        email_notifications = EmailNotification.objects.all()

        self.assertEqual(len(email_notifications), 1)

        email_object = message_from_string(email_notifications[0].payload, policy=default)

        self.assertEqual(email_object['To'], program_email.email)

        content = email_object.as_string()

        self.assertIn(
            f'{self.general_admission.candidate.last_name}, {self.general_admission.candidate.first_name}',
            content,
        )

        self.assertIn('mons@campus.be', content)

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.message_fr,
            f'Un mail informant de la soumission du dossier en faculté a été envoyé à '
            f'"{program_email.email}" le 1 Janvier 2022 00:00.',
        )

        self.assertEqual(
            history_entry.message_en,
            f'An e-mail notifying that the dossier has been submitted to the faculty was sent to '
            f'"{program_email.email}" on 1 Janvier 2022 00:00.',
        )

        self.assertEqual(
            history_entry.author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
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

    @freezegun.freeze_time('2022-01-01')
    def test_send_to_faculty_with_sic_user_in_valid_sic_statuses_but_without_specified_recipient(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())

        # Check that no notification has been planned
        email_notifications = EmailNotification.objects.all()

        self.assertEqual(len(email_notifications), 0)

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.message_fr,
            'Le dossier a été soumis en faculté le 1 Janvier 2022 00:00.',
        )

        self.assertEqual(
            history_entry.message_en,
            'The dossier has been submitted to the faculty on 1 Janvier 2022 00:00.',
        )

        self.assertEqual(
            history_entry.author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
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

    @freezegun.freeze_time('2022-01-01')
    def test_send_to_faculty_with_sic_user_in_valid_sic_statuses_but_with_invalid_recipient(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        program_email = EmailFonctionProgrammeFactory(
            programme=self.general_admission.training.education_group,
            type=TypeEmailFonctionProgramme.DESTINATAIRE_ADMISSION.name,
            premiere_annee=False,
        )

        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())

        # Check that no notification has been planned
        email_notifications = EmailNotification.objects.all()

        self.assertEqual(len(email_notifications), 0)

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.message_fr,
            'Le dossier a été soumis en faculté le 1 Janvier 2022 00:00.',
        )

        self.assertEqual(
            history_entry.message_en,
            'The dossier has been submitted to the faculty on 1 Janvier 2022 00:00.',
        )

        self.assertEqual(
            history_entry.author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
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
@freezegun.freeze_time('2022-01-01')
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

        self.general_admission.status = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name
        self.general_admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_send_to_sic_is_forbidden_with_sic_user_if_the_admission_is_not_in_specific_statuses(self):
        self.client.force_login(user=self.sic_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name
        self.general_admission.save()

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_send_to_sic_with_fac_user_in_specific_statuses_to_refuse(self, frozen_time):
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.refusal_reasons.all().delete()
        self.general_admission.other_refusal_reasons = []
        self.general_admission.fac_refusal_certificate = []
        self.general_admission.save()

        # Simulate a transfer from the SIC to the FAC
        history_entry = HistoryEntryFactory(
            object_uuid=self.general_admission.uuid,
            tags=['proposition', 'fac-decision', 'send-to-fac'],
        )

        # Simulate a comment from the FAC
        comment_entry = CommentEntryFactory(
            object_uuid=self.general_admission.uuid,
            tags=['decision_facultaire', 'FAC'],
            content='The comment from the FAC to the SIC',
        )

        # Invalid request -> We need to specify a reason
        response = self.client.post(self.url + '?refusal=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            gettext('When refusing a proposition, the reason must be specified.'),
            [m.message for m in response.context['messages']],
        )

        self.general_admission.other_refusal_reasons = ['test']
        self.general_admission.save()

        frozen_time.move_to('2022-01-03')

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
                'decision': DecisionFacultaireEnum.EN_DECISION.value,
            },
        )
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())

        # A certificate has been generated
        self.assertEqual(self.general_admission.fac_refusal_certificate, [self.file_uuid])

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('proposition', pdf_context)
        self.assertEqual(pdf_context['proposition'].uuid, self.general_admission.uuid)

        self.assertIn('fac_decision_comment', pdf_context)
        self.assertEqual(pdf_context['fac_decision_comment'], comment_entry)

        self.assertIn('sic_to_fac_history_entry', pdf_context)
        self.assertEqual(pdf_context['sic_to_fac_history_entry'], history_entry)

        self.assertIn('manager', pdf_context)
        self.assertEqual(pdf_context['manager'].matricule, self.fac_manager_user.person.global_id)

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(
            object_uuid=self.general_admission.uuid
        ).order_by('-id')

        self.assertEqual(len(history_entries), 2)

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

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_send_to_sic_with_fac_user_in_specific_statuses_to_approve(self, frozen_time):
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.with_additional_approval_conditions = None
        self.general_admission.with_prerequisite_courses = None
        self.general_admission.program_planned_years_number = None
        self.general_admission.are_secondary_studies_access_title = True
        self.general_admission.save()

        # Simulate a transfer from the SIC to the FAC
        history_entry = HistoryEntryFactory(
            object_uuid=self.general_admission.uuid,
            tags=['proposition', 'fac-decision', 'send-to-fac'],
        )

        # Simulate a comment from the FAC
        comment_entry = CommentEntryFactory(
            object_uuid=self.general_admission.uuid,
            tags=['decision_facultaire', 'FAC'],
            content='The comment from the FAC to the SIC',
        )

        # Invalid request -> We need to specify the missing data
        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            gettext(
                'When accepting a proposition, all the required information in the approval form must be specified.'
            ),
            [m.message for m in response.context['messages']],
        )

        self.general_admission.with_additional_approval_conditions = False
        self.general_admission.with_prerequisite_courses = False
        self.general_admission.program_planned_years_number = 5
        self.general_admission.are_secondary_studies_access_title = False
        self.general_admission.save()

        # Invalid request -> We need to choose an access title
        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            gettext(
                'Please select in the previous experience, the diploma(s), or non-academic activity(ies) giving '
                'access to the chosen program.'
            ),
            [m.message for m in response.context['messages']],
        )

        # Check that the admission has not been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)

        frozen_time.move_to('2022-01-03')

        # Valid request
        self.general_admission.are_secondary_studies_access_title = True
        self.general_admission.save(update_fields=['are_secondary_studies_access_title'])

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
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())

        # A certificate has been generated
        self.assertEqual(self.general_admission.fac_approval_certificate, [self.file_uuid])

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('proposition', pdf_context)
        self.assertEqual(pdf_context['proposition'].uuid, self.general_admission.uuid)

        self.assertIn('fac_decision_comment', pdf_context)
        self.assertEqual(pdf_context['fac_decision_comment'], comment_entry)

        self.assertIn('sic_to_fac_history_entry', pdf_context)
        self.assertEqual(pdf_context['sic_to_fac_history_entry'], history_entry)

        self.assertIn('manager', pdf_context)
        self.assertEqual(pdf_context['manager'].matricule, self.fac_manager_user.person.global_id)

        self.assertIn('access_titles_names', pdf_context)
        belgian_diploma_year = self.general_admission.candidate.graduated_from_high_school_year.year
        self.assertEqual(
            pdf_context['access_titles_names'],
            [
                f'{belgian_diploma_year}-{belgian_diploma_year + 1} : Études secondaires ou alternative',
            ],
        )

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(
            object_uuid=self.general_admission.uuid
        ).order_by('-id')

        self.assertEqual(len(history_entries), 2)
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

    @freezegun.freeze_time('2022-01-01')
    @patch("osis_document.contrib.fields.FileField._confirm_multiple_upload")
    def test_send_to_sic_with_fac_user_in_specific_statuses_to_approve_with_secondary_studies_as_access_title(
        self,
        confirm_multiple_upload,
    ):
        confirm_multiple_upload.side_effect = (
            lambda _, value, __: ["550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"] if value else []
        )
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.are_secondary_studies_access_title = True
        self.general_admission.with_additional_approval_conditions = False
        self.general_admission.with_prerequisite_courses = False
        self.general_admission.program_planned_years_number = 1
        self.general_admission.save()

        secondary_studies_base_title = gettext('Secondary school or alternative')

        # > Belgian diploma
        candidate = self.general_admission.candidate

        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('access_titles_names', pdf_context)
        self.assertEqual(len(pdf_context['access_titles_names']), 1)
        self.assertEqual(
            pdf_context['access_titles_names'][0],
            f'{candidate.graduated_from_high_school_year.year}-{candidate.graduated_from_high_school_year.year + 1} : '
            f'{secondary_studies_base_title}',
        )

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save()

        # > Foreign diploma
        self.get_pdf_from_template_patcher.reset_mock()
        candidate.belgianhighschooldiploma.delete()
        ForeignHighSchoolDiplomaFactory(person=candidate)

        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('access_titles_names', pdf_context)
        self.assertEqual(len(pdf_context['access_titles_names']), 1)
        self.assertEqual(
            pdf_context['access_titles_names'][0],
            f'{candidate.graduated_from_high_school_year.year}-{candidate.graduated_from_high_school_year.year + 1} : '
            f'{secondary_studies_base_title}',
        )

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save()

        # > High school diploma alternative
        BelgianHighSchoolDiploma.objects.filter(person=candidate).delete()
        ForeignHighSchoolDiploma.objects.filter(person=candidate).delete()
        HighSchoolDiplomaAlternative.objects.filter(person=candidate).delete()
        diploma_alternative = HighSchoolDiplomaAlternativeFactory(person=candidate)

        candidate.graduated_from_high_school = GotDiploma.NO.name
        candidate.graduated_from_high_school_year = None
        candidate.save()

        self.get_pdf_from_template_patcher.reset_mock()

        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)

        # Check that the admission has not been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)

        diploma_alternative.first_cycle_admission_exam = ['token.pdf']
        diploma_alternative.save()

        self.get_pdf_from_template_patcher.reset_mock()

        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('access_titles_names', pdf_context)
        self.assertEqual(len(pdf_context['access_titles_names']), 1)
        self.assertEqual(pdf_context['access_titles_names'][0], secondary_studies_base_title)

        # The candidate specified that he has no secondary education but without more information
        diploma_alternative.delete()

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save()

        self.get_pdf_from_template_patcher.reset_mock()

        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)

        # Check that the admission has not been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)

        # The candidate specified that he has secondary education but without more information
        candidate.graduated_from_high_school = GotDiploma.YES.name
        candidate.graduated_from_high_school_year = self.general_admission.training.academic_year
        candidate.save()

        self.get_pdf_from_template_patcher.reset_mock()

        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('access_titles_names', pdf_context)
        self.assertEqual(len(pdf_context['access_titles_names']), 1)
        self.assertEqual(
            pdf_context['access_titles_names'][0],
            f'{candidate.graduated_from_high_school_year.year}-{candidate.graduated_from_high_school_year.year + 1} : '
            f'{secondary_studies_base_title}',
        )

    @freezegun.freeze_time('2022-01-01')
    def test_send_to_sic_with_fac_user_in_specific_statuses_to_approve_with_a_cv_academic_experience_as_title(self):
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.with_additional_approval_conditions = False
        self.general_admission.with_prerequisite_courses = False
        self.general_admission.program_planned_years_number = 1
        self.general_admission.save()

        academic_experience = EducationalExperience.objects.filter(
            person=self.general_admission.candidate,
        ).first()

        academic_experience.obtained_diploma = True
        academic_experience.save()

        admission_educational_valuated_experience = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.general_admission,
            educationalexperience=academic_experience,
            is_access_title=True,
        )

        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('access_titles_names', pdf_context)
        self.assertEqual(len(pdf_context['access_titles_names']), 1)
        self.assertEqual(
            pdf_context['access_titles_names'][0],
            '2020-2022 : Computer science',
        )

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save()
        admission_educational_valuated_experience.is_access_title = False
        admission_educational_valuated_experience.save()
        self.get_pdf_from_template_patcher.reset_mock()

        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)

        # Check that the admission has not been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)

    @freezegun.freeze_time('2022-01-01')
    def test_send_to_sic_with_fac_user_in_specific_statuses_to_approve_with_a_cv_non_academic_experience_as_title(self):
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.with_additional_approval_conditions = False
        self.general_admission.with_prerequisite_courses = False
        self.general_admission.program_planned_years_number = 1
        self.general_admission.save()

        non_academic_experience = ProfessionalExperience.objects.filter(
            person=self.general_admission.candidate,
        ).first()

        admission_non_educational_valuated_experience = AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=self.general_admission,
            professionalexperience=non_academic_experience,
            is_access_title=True,
        )

        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('access_titles_names', pdf_context)
        self.assertEqual(len(pdf_context['access_titles_names']), 1)
        self.assertEqual(
            pdf_context['access_titles_names'][0],
            '01/2020-03/2020 : Travail',
        )

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save()
        admission_non_educational_valuated_experience.is_access_title = False
        admission_non_educational_valuated_experience.save()
        self.get_pdf_from_template_patcher.reset_mock()

        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)

        # Check that the admission has not been updated
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)

    @freezegun.freeze_time('2022-01-01')
    def test_send_to_sic_with_fac_user_to_approve_with_internal_experience_as_access_title(self):
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.with_additional_approval_conditions = False
        self.general_admission.with_prerequisite_courses = False
        self.general_admission.program_planned_years_number = 1
        self.general_admission.save()

        student = StudentFactory(person=self.general_admission.candidate)

        pce_a = InscriptionProgrammeCycleFactory(
            etudiant=student,
            decision=DecisionResultatCycle.DISTINCTION.name,
            sigle_formation="SF1",
        )
        pce_a_uuid = str(uuid.UUID(int=pce_a.pk))
        pce_a_pae_a = InscriptionProgrammeAnnuelFactory(
            programme_cycle=pce_a,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__root_group__academic_year=self.academic_years[0],
            type_duree=TypeDuree.NORMAL.name,
        )

        self.general_admission.internal_access_titles.add(pce_a)

        candidate = self.general_admission.candidate

        response = self.client.post(self.url + '?approval=1', **self.default_headers)
        self.assertEqual(response.status_code, 200)

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('access_titles_names', pdf_context)
        self.assertEqual(len(pdf_context['access_titles_names']), 1)
        self.assertEqual(
            pdf_context['access_titles_names'][0],
            f'2021-2022 : {pce_a_pae_a.programme.offer.title}',
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_send_to_sic_with_fac_user_in_specific_statuses_without_approving_or_refusing(self, frozen_time):
        self.client.force_login(user=self.fac_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.checklist['current']['decision_facultaire'][
            'statut'
        ] = ChoixStatutChecklist.GEST_REUSSITE.name
        self.general_admission.save()

        # Invalid request -> We need to be in the right status
        response = self.client.post(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            gettext('The proposition must be managed by FAC to realized this action.'),
            [m.message for m in response.context['messages']],
        )

        frozen_time.move_to('2022-01-02')

        # Valid request
        self.general_admission.checklist['current']['decision_facultaire'][
            'statut'
        ] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        self.general_admission.save()

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name)
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

        self.assertEqual(len(history_entries), 1)
        history_entry = history_entries[0]

        self.assertEqual(
            history_entry.author,
            f'{self.fac_manager_user.person.first_name} {self.fac_manager_user.person.last_name}',
        )

        self.assertEqual(history_entry.message_fr, 'Le dossier a été soumis au SIC par la faculté.')

        self.assertEqual(history_entry.message_en, 'The dossier has been submitted to the SIC by the faculty.')

        self.assertCountEqual(
            history_entry.tags,
            ['proposition', 'fac-decision', 'send-to-sic', 'status-changed'],
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_send_to_sic_with_sic_user_in_specific_statuses_without_approving_or_refusing(self, frozen_time):
        self.client.force_login(user=self.sic_manager_user)

        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.checklist['current']['decision_facultaire'][
            'statut'
        ] = ChoixStatutChecklist.GEST_REUSSITE.name
        self.general_admission.save()

        frozen_time.move_to('2022-01-02')

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name)
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

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
            ['proposition', 'fac-decision', 'send-to-sic', 'status-changed'],
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

        RefusalReasonCategory.objects.all().delete()

        third_refusal_reason = RefusalReasonFactory(category__order=2, order=1)
        first_refusal_reason = RefusalReasonFactory(category__order=1, order=1)
        second_refusal_reason = RefusalReasonFactory(category=first_refusal_reason.category, order=2)

        # No reason
        self.general_admission.refusal_reasons.all().delete()
        self.general_admission.other_refusal_reasons = []

        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']

        self.assertEqual(form.initial.get('reasons'), [])

        choices = form.fields['reasons'].choices

        # The choices are sorted by category order and then by reason order
        self.assertEqual(choices[0][0], first_refusal_reason.category.name)
        self.assertEqual(choices[0][1][0], [first_refusal_reason.uuid, first_refusal_reason.name])
        self.assertEqual(choices[0][1][1], [second_refusal_reason.uuid, second_refusal_reason.name])
        self.assertEqual(choices[1][0], third_refusal_reason.category.name)
        self.assertEqual(choices[1][1][0], [third_refusal_reason.uuid, third_refusal_reason.name])

        # One existing reason is selected
        self.general_admission.refusal_reasons.add(first_refusal_reason)
        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']

        self.assertEqual(form.initial.get('reasons'), [first_refusal_reason.uuid])

        # One other reason is selected
        self.general_admission.refusal_reasons.all().delete()
        self.general_admission.other_refusal_reasons = ['Other reason']
        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']

        self.assertEqual(form.initial.get('reasons'), ['Other reason'])

    def test_refusal_decision_form_submitting_with_invalid_data(self):
        self.client.force_login(user=self.fac_manager_user)

        # Check form submitting
        self.general_admission.refusal_reasons.all().delete()
        self.general_admission.other_refusal_reasons = []
        self.general_admission.save()

        # No chosen reason
        response = self.client.post(
            self.url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('reasons', []))

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_refusal_decision_form_submitting_with_valid_data(self, frozen_time):
        self.client.force_login(user=self.fac_manager_user)

        refusal_reason = RefusalReasonFactory()

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'fac-decision-refusal-reasons': [refusal_reason.uuid],
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        refusal_reasons = self.general_admission.refusal_reasons.all()
        self.assertEqual(len(refusal_reasons), 1)
        self.assertEqual(refusal_reasons[0], refusal_reason)
        self.assertEqual(self.general_admission.other_refusal_reasons, [])
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['extra'],
            {'decision': DecisionFacultaireEnum.EN_DECISION.value},
        )
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())

        frozen_time.move_to('2022-01-02')

        # Choose another reason
        response = self.client.post(
            self.url,
            data={
                'fac-decision-refusal-reasons': ['My other reason'],
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_refusal_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertFalse(self.general_admission.refusal_reasons.exists())
        self.assertEqual(self.general_admission.other_refusal_reasons, ['My other reason'])
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())

    @freezegun.freeze_time('2022-01-01')
    def test_refusal_decision_form_submitting_with_transfer_to_sic(self):
        self.client.force_login(user=self.fac_manager_user)

        refusal_reason = RefusalReasonFactory()

        # Simulate a transfer from the SIC to the FAC
        history_entry = HistoryEntryFactory(
            object_uuid=self.general_admission.uuid,
            tags=['proposition', 'fac-decision', 'send-to-fac'],
        )

        # Simulate a comment from the FAC
        comment_entry = CommentEntryFactory(
            object_uuid=self.general_admission.uuid,
            tags=['decision_facultaire', 'FAC'],
            content='The comment from the FAC to the SIC',
        )

        # Chosen reason and transfer to SIC
        response = self.client.post(
            self.url,
            data={
                'fac-decision-refusal-reasons': [refusal_reason.uuid],
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

        refusal_reasons = self.general_admission.refusal_reasons.all()
        self.assertEqual(len(refusal_reasons), 1)
        self.assertEqual(refusal_reasons[0], refusal_reason)
        self.assertEqual(self.general_admission.other_refusal_reasons, [])
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['extra'],
            {'decision': DecisionFacultaireEnum.EN_DECISION.value},
        )
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())

        # A certificate has been generated
        self.assertEqual(self.general_admission.fac_refusal_certificate, [self.file_uuid])

        # Check the template context
        self.get_pdf_from_template_patcher.assert_called_once()
        pdf_context = self.get_pdf_from_template_patcher.call_args_list[0][0][2]

        self.assertIn('proposition', pdf_context)
        self.assertEqual(pdf_context['proposition'].uuid, self.general_admission.uuid)

        self.assertIn('fac_decision_comment', pdf_context)
        self.assertEqual(pdf_context['fac_decision_comment'], comment_entry)

        self.assertIn('sic_to_fac_history_entry', pdf_context)
        self.assertEqual(pdf_context['sic_to_fac_history_entry'], history_entry)

        self.assertIn('manager', pdf_context)
        self.assertEqual(pdf_context['manager'].matricule, self.fac_manager_user.person.global_id)

        # Check that an entry in the history has been created
        history_entries: List[HistoryEntry] = HistoryEntry.objects.filter(
            object_uuid=self.general_admission.uuid
        ).order_by('-id')

        self.assertEqual(len(history_entries), 2)
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
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name,
            determined_academic_year=self.academic_years[0],
        )
        self.experience_uuid = str(self.general_admission.candidate.educationalexperience_set.first().uuid)
        self.default_checklist = copy.deepcopy(self.general_admission.checklist)
        self.url = resolve_url(
            'admission:general-education:fac-decision-approval',
            uuid=self.general_admission.uuid,
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
        self.general_admission.freeadditionalapprovalcondition_set.all().delete()
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

        formset = response.context['fac_decision_free_approval_condition_formset']
        self.assertEqual(len(formset.forms), 0)

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

        free_approval_conditions = [
            FreeAdditionalApprovalConditionFactory(
                name_fr='Première condition libre',
                name_en='First free condition',
                admission=self.general_admission,
            ),
            FreeAdditionalApprovalConditionFactory(
                name_fr='Deuxième condition libre',
                name_en='Second free condition',
                admission=self.general_admission,
                related_experience=self.general_admission.candidate.educationalexperience_set.first(),
            ),
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
                free_approval_conditions[1].related_experience_id,
            ],
        )
        self.assertCountEqual(
            form.fields['all_additional_approval_conditions'].choices,
            [
                (
                    str(free_approval_conditions[1].related_experience_id),
                    gettext('Graduation of {program_name}').format(program_name='Computer science'),
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

        formset = response.context['fac_decision_free_approval_condition_formset']
        self.assertEqual(len(formset.forms), 1)
        self.assertEqual(
            formset.forms[0].initial,
            {
                'name_fr': free_approval_conditions[0].name_fr,
                'name_en': free_approval_conditions[0].name_en,
            },
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
                "fac-decision-approval-prerequisite_courses": [],
                'fac-decision-approval-another_training': True,
                'fac-decision-approval-with_prerequisite_courses': 'True',
                'fac-decision-approval-with_additional_approval_conditions': 'True',
                'fac-decision-approval-all_additional_approval_conditions': [],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']

        self.assertFalse(form.is_valid())

        # Missing fields
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('other_training_accepted_by_fac', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('program_planned_years_number', []))
        self.assertNotIn(FIELD_REQUIRED_MESSAGE, form.errors.get('prerequisite_courses', []))

        response = self.client.post(
            self.url,
            data={
                'fac-decision-approval-another_training': False,
                'fac-decision-approval-with_prerequisite_courses': 'False',
                'fac-decision-approval-with_additional_approval_conditions': 'False',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']

        self.assertFalse(form.is_valid())

        # Missing fields
        self.assertNotIn(FIELD_REQUIRED_MESSAGE, form.errors.get('other_training_accepted_by_fac', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('program_planned_years_number', []))
        self.assertNotIn(FIELD_REQUIRED_MESSAGE, form.errors.get('prerequisite_courses', []))

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
                (
                    self.experience_uuid,
                    gettext('Graduation of {program_name}').format(program_name='Computer science'),
                ),
            ],
        )

        # Invalid free condition
        response = self.client.post(
            self.url,
            data={
                'fac-decision-approval-another_training': False,
                'fac-decision-approval-with_prerequisite_courses': 'False',
                'fac-decision-approval-with_additional_approval_conditions': 'True',
                'fac-decision-approval-program_planned_years_number': 1,
                'fac-decision-TOTAL_FORMS': '2',
                'fac-decision-INITIAL_FORMS': '0',
                'fac-decision-MIN_NUM_FORMS': '0',
                'fac-decision-MAX_NUM_FORMS': '1000',
                'fac-decision-0-name_fr': '',
                'fac-decision-0-name_en': '',
                'fac-decision-1-name_fr': 'Ma condition en français 2',
                'fac-decision-1-name_en': '',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']
        formset = response.context['fac_decision_free_approval_condition_formset']

        self.assertEqual(form.is_valid(), True)
        self.assertEqual(formset.is_valid(), False)
        self.assertEqual(formset.forms[0].is_valid(), False)
        self.assertIn(FIELD_REQUIRED_MESSAGE, formset.forms[0].errors.get('name_fr', []))
        self.assertEqual(formset.forms[1].is_valid(), True)

        self.general_admission.candidate.language = settings.LANGUAGE_CODE_EN
        self.general_admission.candidate.save(update_fields=['language'])

        response = self.client.post(
            self.url,
            data={
                'fac-decision-approval-another_training': False,
                'fac-decision-approval-with_prerequisite_courses': 'False',
                'fac-decision-approval-with_additional_approval_conditions': 'True',
                'fac-decision-approval-program_planned_years_number': 1,
                'fac-decision-TOTAL_FORMS': '2',
                'fac-decision-INITIAL_FORMS': '0',
                'fac-decision-MIN_NUM_FORMS': '0',
                'fac-decision-MAX_NUM_FORMS': '1000',
                'fac-decision-0-name_fr': '',
                'fac-decision-0-name_en': '',
                'fac-decision-1-name_fr': 'Ma condition en français 2',
                'fac-decision-1-name_en': '',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']
        formset = response.context['fac_decision_free_approval_condition_formset']

        self.assertEqual(form.is_valid(), True)
        self.assertEqual(formset.is_valid(), False)
        self.assertEqual(formset.forms[0].is_valid(), False)
        self.assertIn(FIELD_REQUIRED_MESSAGE, formset.forms[0].errors.get('name_fr', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, formset.forms[0].errors.get('name_en', []))
        self.assertEqual(formset.forms[1].is_valid(), False)
        self.assertIn(FIELD_REQUIRED_MESSAGE, formset.forms[1].errors.get('name_en', []))

        response = self.client.post(
            self.url,
            data={
                'fac-decision-approval-another_training': False,
                'fac-decision-approval-with_prerequisite_courses': 'False',
                'fac-decision-approval-with_additional_approval_conditions': 'True',
                'fac-decision-approval-program_planned_years_number': 1,
                'fac-decision-TOTAL_FORMS': '0',
                'fac-decision-INITIAL_FORMS': '0',
                'fac-decision-MIN_NUM_FORMS': '0',
                'fac-decision-MAX_NUM_FORMS': '1000',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']
        formset = response.context['fac_decision_free_approval_condition_formset']

        self.assertEqual(form.is_valid(), False)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('all_additional_approval_conditions', []))
        self.assertEqual(formset.is_valid(), True)

    @freezegun.freeze_time('2022-01-01')
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
                    self.experience_uuid,
                ],
                'fac-decision-approval-prerequisite_courses_fac_comment': 'Comment about the additional trainings',
                'fac-decision-approval-program_planned_years_number': 5,
                'fac-decision-approval-annual_program_contact_person_name': 'John Doe',
                'fac-decision-approval-annual_program_contact_person_email': 'john.doe@example.be',
                'fac-decision-approval-join_program_fac_comment': 'Comment about the join program',
                'fac-decision-TOTAL_FORMS': '2',
                'fac-decision-INITIAL_FORMS': '0',
                'fac-decision-MIN_NUM_FORMS': '0',
                'fac-decision-MAX_NUM_FORMS': '1000',
                'fac-decision-0-name_fr': 'Ma première condition',
                'fac-decision-0-name_en': '',
                'fac-decision-1-name_fr': 'Ma seconde condition',
                'fac-decision-1-name_en': 'My second condition',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']
        formset = response.context['fac_decision_free_approval_condition_formset']

        self.assertTrue(form.is_valid())
        self.assertTrue(formset.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())
        self.assertEqual(self.general_admission.fac_approval_certificate, [])
        self.assertEqual(self.general_admission.with_additional_approval_conditions, True)
        approval_conditions = self.general_admission.additional_approval_conditions.all()
        self.assertEqual(len(approval_conditions), 1)
        self.assertEqual(approval_conditions[0], approval_conditions[0])
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

        # Check the creation of the free additional conditions
        conditions: QuerySet[FreeAdditionalApprovalCondition] = FreeAdditionalApprovalCondition.objects.filter(
            admission=self.general_admission
        ).order_by('name_fr')
        self.assertEqual(len(conditions), 3)
        self.assertEqual(conditions[0].name_fr, 'L\'obtention de votre diplôme de Computer science')
        self.assertEqual(conditions[0].name_en, 'Graduation of Computer science')
        self.assertEqual(str(conditions[0].related_experience_id), self.experience_uuid)
        self.assertEqual(conditions[1].name_fr, 'Ma première condition')
        self.assertEqual(conditions[1].name_en, '')
        self.assertIsNone(conditions[1].related_experience)
        self.assertEqual(conditions[2].name_fr, 'Ma seconde condition')
        self.assertEqual(conditions[2].name_en, 'My second condition')
        self.assertIsNone(conditions[2].related_experience)

        # Without additional condition
        response = self.client.post(
            self.url,
            data={
                'fac-decision-approval-another_training': False,
                'fac-decision-approval-with_prerequisite_courses': 'False',
                'fac-decision-approval-with_additional_approval_conditions': 'False',
                'fac-decision-approval-all_additional_approval_conditions': [
                    approval_conditions[0].uuid,
                    self.experience_uuid,
                ],
                'fac-decision-approval-program_planned_years_number': 5,
                'fac-decision-TOTAL_FORMS': '1',
                'fac-decision-INITIAL_FORMS': '0',
                'fac-decision-MIN_NUM_FORMS': '0',
                'fac-decision-MAX_NUM_FORMS': '1000',
                'fac-decision-0-name_fr': '',
                'fac-decision-0-name_en': '',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.with_additional_approval_conditions, False)
        self.assertFalse(self.general_admission.additional_approval_conditions.exists())
        self.assertFalse(self.general_admission.freeadditionalapprovalcondition_set.exists())

    @freezegun.freeze_time('2022-01-01')
    def test_approval_decision_form_submitting_with_transfer_to_sic(self):
        self.client.force_login(user=self.fac_manager_user)

        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.general_admission.determined_academic_year),
        ]

        approval_conditions = [
            AdditionalApprovalConditionFactory(),
        ]

        data = {
            "fac-decision-approval-prerequisite_courses": [
                prerequisite_courses[0].acronym,
            ],
            'fac-decision-approval-another_training': True,
            'fac-decision-approval-other_training_accepted_by_fac': self.general_admission.training.uuid,
            'fac-decision-approval-with_prerequisite_courses': 'True',
            'fac-decision-approval-with_additional_approval_conditions': 'True',
            'fac-decision-approval-all_additional_approval_conditions': [
                approval_conditions[0].uuid,
                self.experience_uuid,
            ],
            'fac-decision-TOTAL_FORMS': '1',
            'fac-decision-INITIAL_FORMS': '0',
            'fac-decision-MIN_NUM_FORMS': '0',
            'fac-decision-MAX_NUM_FORMS': '1000',
            'fac-decision-0-name_fr': 'Ma première condition',
            'fac-decision-0-name_en': 'My first condition',
            'fac-decision-approval-prerequisite_courses_fac_comment': 'Comment about the additional trainings',
            'fac-decision-approval-program_planned_years_number': 5,
            'fac-decision-approval-annual_program_contact_person_name': 'John Doe',
            'fac-decision-approval-annual_program_contact_person_email': 'john.doe@example.be',
            'fac-decision-approval-join_program_fac_comment': 'Comment about the join program',
            'save-transfer': '1',
        }

        response = self.client.post(self.url, data=data, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['fac_decision_approval_form']

        self.assertTrue(form.is_valid())

        self.assertDjangoMessage(
            response=response,
            message=gettext(
                'Please select in the previous experience, the diploma(s), or non-academic activity(ies) giving '
                'access to the chosen program.'
            ),
        )

        # Check that the admission has not been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)

        # Add the access title
        self.general_admission.are_secondary_studies_access_title = True
        self.general_admission.save(update_fields=['are_secondary_studies_access_title'])

        response = self.client.post(self.url, data=data, **self.default_headers)

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
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())
        self.assertEqual(self.general_admission.fac_approval_certificate, [self.file_uuid])
        self.assertEqual(self.general_admission.with_additional_approval_conditions, True)
        approval_conditions = self.general_admission.additional_approval_conditions.all()
        self.assertEqual(len(approval_conditions), 1)
        self.assertEqual(approval_conditions[0], approval_conditions[0])
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

        # Check the creation of the free additional conditions
        conditions: QuerySet[FreeAdditionalApprovalCondition] = FreeAdditionalApprovalCondition.objects.filter(
            admission=self.general_admission
        ).order_by('name_fr')
        self.assertEqual(len(conditions), 2)
        self.assertEqual(conditions[0].name_fr, 'L\'obtention de votre diplôme de Computer science')
        self.assertEqual(conditions[0].name_en, 'Graduation of Computer science')
        self.assertEqual(str(conditions[0].related_experience_id), self.experience_uuid)
        self.assertEqual(conditions[1].name_fr, 'Ma première condition')
        self.assertEqual(conditions[1].name_en, 'My first condition')
        self.assertIsNone(conditions[1].related_experience)

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
class LateFacultyApprovalDecisionViewTestCase(TestCase):
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
        cls.fac_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group,
            person__language=settings.LANGUAGE_CODE_FR,
        ).person.user

        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def assertDjangoMessage(self, response, message):
        messages = [m.message for m in response.context['messages']]
        self.assertIn(message, messages)

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name,
            determined_academic_year=self.academic_years[0],
            late_enrollment=True,
            admission_requirement=ConditionAcces.BAC.name,
        )

        self.experience = self.general_admission.candidate.educationalexperience_set.first()

        self.experience.obtained_diploma = True
        self.experience.save(update_fields=['obtained_diploma'])

        self.valuated_experience = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.general_admission,
            educationalexperience=self.experience,
            is_access_title=True,
        )

        self.experience_uuid = str(self.experience.uuid)
        self.default_checklist = copy.deepcopy(self.general_admission.checklist)
        self.url = resolve_url(
            'admission:general-education:late-fac-decision-approval',
            uuid=self.general_admission.uuid,
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

    def test_submit_late_approval_decision_is_forbidden_with_sic_user(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_submit_late_approval_decision_is_forbidden_with_fac_user_if_the_admission_is_not_in_specific_statuses(
        self,
    ):
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
        response = self.client.get(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)

    def test_approval_decision_form_submitting_with_invalid_context(self):
        self.client.force_login(user=self.fac_manager_user)

        # No admission requirement
        self.general_admission.admission_requirement = ''
        self.general_admission.save()

        response = self.client.post(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)

        self.assertDjangoMessage(
            response=response,
            message=gettext('The proposition must be a late enrollment with a defined access condition.'),
        )

        # No late enrollment
        self.general_admission.late_enrollment = False
        self.general_admission.admission_requirement = ConditionAcces.BAC.name
        self.general_admission.save()

        response = self.client.post(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)

        self.assertDjangoMessage(
            response=response,
            message=gettext('The proposition must be a late enrollment with a defined access condition.'),
        )

        # No selected access title
        self.general_admission.late_enrollment = True
        self.general_admission.save()

        self.valuated_experience.is_access_title = False
        self.valuated_experience.save()

        response = self.client.post(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)

        self.assertDjangoMessage(
            response=response,
            message=gettext(
                'Please select in the previous experience, the diploma(s), or non-academic activity(ies) giving '
                'access to the chosen program.',
            ),
        )

    @freezegun.freeze_time('2022-01-01')
    def test_approval_decision_form_submitting_with_valid_context(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_facultaire']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())

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
