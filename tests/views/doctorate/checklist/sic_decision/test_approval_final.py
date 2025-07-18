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
import datetime
from email import message_from_string, policy

import freezegun
import mock
from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import TestCase
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification

from admission.constants import ORDERED_CAMPUSES_UUIDS
from admission.ddd.admission.doctorat.events import (
    InscriptionDoctoraleApprouveeParSicEvent,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    EnvoyerEmailApprobationInscriptionAuCandidatCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    DispenseOuDroitsMajores,
    DroitsInscriptionMontant,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.infrastructure.admission.formation_generale.domain.service.pdf_generation import (
    ENTITY_SIC,
    ENTITY_SICB,
)
from admission.mail_templates import (
    EMAIL_TEMPLATE_ENROLLMENT_GENERATED_NOMA_DOCTORATE_TOKEN,
    EMAIL_TEMPLATE_ENROLLMENT_GENERATED_NOMA_TOKEN,
)
from admission.models import DoctorateAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.faculty_decision import DoctorateRefusalReasonFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from admission.tests.views.doctorate.checklist.sic_decision.base import SicPatchMixin
from base.models.enums.mandate_type import MandateTypes
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.mandatary import MandataryFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from infrastructure.messages_bus import message_bus_instance


@freezegun.freeze_time('2022-01-01')
class SicApprovalFinalDecisionViewTestCase(SicPatchMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.louvain_training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
            enrollment_campus__uuid=ORDERED_CAMPUSES_UUIDS['LOUVAIN_LA_NEUVE_UUID'],
        )
        cls.saint_louis_training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
            enrollment_campus__uuid=ORDERED_CAMPUSES_UUIDS['BRUXELLES_SAINT_LOUIS_UUID'],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(
            education_group=cls.louvain_training.education_group,
        ).person.user

        cls.sic_entity = EntityWithVersionFactory(version__acronym=ENTITY_SIC)
        cls.sic_b_entity = EntityWithVersionFactory(version__acronym=ENTITY_SICB)

        today = datetime.datetime.now()

        cls.sic_director_mandate = MandataryFactory(
            mandate__entity=cls.sic_entity,
            mandate__education_group=None,
            mandate__function=MandateTypes.DIRECTOR.name,
            start_date=today,
            end_date=today + datetime.timedelta(days=1),
            person__last_name='Foe',
            person__first_name='Jane',
        )

        cls.sic_b_director_mandate = MandataryFactory(
            mandate__entity=cls.sic_b_entity,
            mandate__education_group=None,
            mandate__function=MandateTypes.DIRECTOR.name,
            start_date=today,
            end_date=today + datetime.timedelta(days=1),
            person__last_name='Doe',
            person__first_name='John',
        )

        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        super().setUp()

        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.louvain_training,
            submitted=True,
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
                country_of_citizenship__european_union=True,
                graduated_from_high_school_year=AcademicYearFactory(current=True),
                private_email='foo@bar',
            ),
            status=ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION.name,
            with_prerequisite_courses=False,
            annual_program_contact_person_name='foo',
            annual_program_contact_person_email='bar@example.org',
            tuition_fees_amount=DroitsInscriptionMontant.INSCRIPTION_REGULIERE.name,
            tuition_fees_dispensation=DispenseOuDroitsMajores.NON_CONCERNE.name,
            must_report_to_sic=False,
            communication_to_the_candidate='',
        )
        self.admission.checklist['current']['parcours_anterieur']['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        self.admission.checklist['current']['donnees_personnelles']['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        self.admission.checklist['current']['financabilite']['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        self.admission.checklist['current']['financabilite']['extra'] = {'reussite': 'financable'}
        self.admission.save(update_fields=['checklist'])
        self.admission.refusal_reasons.add(DoctorateRefusalReasonFactory())
        self.url = resolve_url(
            'admission:doctorate:sic-decision-approval-final',
            uuid=self.admission.uuid,
        )

        # Mock publish
        patcher = mock.patch(
            'infrastructure.utils.MessageBus.publish',
        )
        self.mock_publish = patcher.start()
        self.addCleanup(patcher.stop)

        # Mock recuperer_matricule_etudiant (used inside mail)
        patcher_matricule_etudiant = mock.patch(
            'ddd.logic.gestion_des_comptes.use_case.read.recuperer_matricule_etudiant_assigne_service',
            return_value='12654879'
        )
        self.mock_recuperer_matricule_etudiant = patcher_matricule_etudiant.start()
        self.addCleanup(patcher_matricule_etudiant.stop)


    def test_submit_approval_final_decision_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_approval_final_decision_form_initialization(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

    def test_approval_final_decision_form_submitting_ue5_candidate(self):
        self.client.force_login(user=self.sic_manager_user)

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'sic-decision-approval-final-subject': 'subject',
                'sic-decision-approval-final-body': 'body',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get('HX-Refresh'))

        form = response.context['sic_decision_approval_final_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name)
        self.assertEqual(
            self.admission.checklist['current']['decision_sic']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())
        self.assertEqual(len(self.admission.sic_approval_certificate), 1)
        self.assertEqual(len(self.admission.sic_annexe_approval_certificate), 0)

        # Check that history entries are created
        entries: QuerySet[HistoryEntry] = HistoryEntry.objects.filter(
            object_uuid=self.admission.uuid,
        )

        self.assertEqual(len(entries), 2)

        status_change_entry = next((entry for entry in entries if 'status-changed' in entry.tags), None)
        message_entry = next((entry for entry in entries if 'message' in entry.tags), None)

        self.assertIsNotNone(status_change_entry)
        self.assertIsNotNone(message_entry)

        self.assertCountEqual(
            ['proposition', 'sic-decision', 'approval', 'status-changed'],
            status_change_entry.tags,
        )

        self.assertEqual(
            status_change_entry.author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        # Check that the approval certificate contains the right data
        self.get_pdf_from_template_patcher.assert_called_once()

        call_args = self.get_pdf_from_template_patcher.call_args_list[0]
        self.assertIn('director', call_args[0][2])

        director = call_args[0][2]['director']
        self.assertEqual(director, self.sic_director_mandate.person)

    def test_approval_final_decision_form_submitting_for_a_saint_louis_training(self):
        self.client.force_login(user=self.sic_manager_user)

        self.admission.training = self.saint_louis_training
        self.admission.save(update_fields=['training'])

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'sic-decision-approval-final-subject': 'subject',
                'sic-decision-approval-final-body': 'body',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the approval certificate contains the right data
        self.get_pdf_from_template_patcher.assert_called_once()

        call_args = self.get_pdf_from_template_patcher.call_args_list[0]
        self.assertIn('director', call_args[0][2])

        director = call_args[0][2]['director']
        self.assertEqual(director, self.sic_b_director_mandate.person)

    def test_approval_final_decision_form_submitting_not_ue5_candidate(self):
        self.client.force_login(user=self.sic_manager_user)

        self.admission.candidate.country_of_citizenship.european_union = False
        self.admission.candidate.country_of_citizenship.save(update_fields=['european_union'])

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'sic-decision-approval-final-subject': 'subject',
                'sic-decision-approval-final-body': 'body',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_approval_final_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name)
        self.assertEqual(
            self.admission.checklist['current']['decision_sic']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())
        self.assertEqual(len(self.admission.sic_approval_certificate), 1)
        self.assertEqual(len(self.admission.sic_annexe_approval_certificate), 1)

        # Check that history entries are created
        entries: QuerySet[HistoryEntry] = HistoryEntry.objects.filter(
            object_uuid=self.admission.uuid,
        )

        self.assertEqual(len(entries), 2)

        status_change_entry = next((entry for entry in entries if 'status-changed' in entry.tags), None)
        message_entry = next((entry for entry in entries if 'message' in entry.tags), None)

        self.assertIsNotNone(status_change_entry)
        self.assertIsNotNone(message_entry)

        self.assertCountEqual(
            ['proposition', 'sic-decision', 'approval', 'status-changed'],
            status_change_entry.tags,
        )

        self.assertEqual(
            status_change_entry.author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

    def _initialize_admission_for_enrolment_approval(self):
        self.admission.checklist['current']['decision_sic']['statut'] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        self.admission.type_demande = TypeDemande.INSCRIPTION.name
        self.admission.save()

    def test_approval_final_decision_form_submitting_inscription(self):
        self.client.force_login(user=self.sic_manager_user)

        self._initialize_admission_for_enrolment_approval()

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'sic-decision-approval-final-subject': 'subject',
                'sic-decision-approval-final-body': 'body',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get('HX-Refresh'))

        form = response.context['sic_decision_approval_final_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name)
        self.assertEqual(
            self.admission.checklist['current']['decision_sic']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        event = self.mock_publish.call_args[0][0]
        self.assertIsInstance(event, InscriptionDoctoraleApprouveeParSicEvent)
        self.assertEqual(event.entity_id.uuid, str(self.admission.uuid))
        self.assertEqual(event.matricule, self.admission.candidate.global_id)
        self.assertEqual(event.auteur, self.sic_manager_user.person.global_id)
        self.assertEqual(event.objet_message, 'subject')
        self.assertEqual(event.corps_message, 'body')

    def test_approval_final_decision_inscription_with_notification_sent(self):
        # The following command is triggered when the InscriptionApprouveeParSicEvent event is published
        message_bus_instance.invoke(
            EnvoyerEmailApprobationInscriptionAuCandidatCommand(
                uuid_proposition=self.admission.uuid,
                objet_message='subject',
                corps_message='body',
                auteur=self.sic_manager_user.person.global_id,
            )
        )

        email_notification = EmailNotification.objects.filter(person=self.admission.candidate).first()
        self.assertIsNotNone(email_notification)

        email_object = message_from_string(email_notification.payload, policy=policy.default)
        self.assertEqual(email_object['To'], 'foo@bar')
        self.assertIn('subject', email_object['Subject'])
        self.assertIn('body', email_object.get_body(('plain',)).get_content())

        history_entry: HistoryEntry = HistoryEntry.objects.filter(
            object_uuid=self.admission.uuid,
        ).first()

        self.assertIsNotNone(history_entry)

        email_notification.delete()

        # Check that the noma variable is replaced by the noma of the candidate

        # When there is no noma -> default value
        message_bus_instance.invoke(
            EnvoyerEmailApprobationInscriptionAuCandidatCommand(
                uuid_proposition=self.admission.uuid,
                objet_message='subject',
                corps_message=f'noma:{EMAIL_TEMPLATE_ENROLLMENT_GENERATED_NOMA_TOKEN}',
                auteur=self.sic_manager_user.person.global_id,
            )
        )

        email_notification = EmailNotification.objects.filter(person=self.admission.candidate).first()
        self.assertIsNotNone(email_notification)

        email_object = message_from_string(email_notification.payload, policy=policy.default)
        self.assertIn('noma:NOMA non trouvé', email_object.get_body(('plain',)).get_content())

        email_notification.delete()

        # From the Student model
        student = StudentFactory(
            person=self.admission.candidate,
            registration_id='123456789',
        )

        message_bus_instance.invoke(
            EnvoyerEmailApprobationInscriptionAuCandidatCommand(
                uuid_proposition=self.admission.uuid,
                objet_message='subject',
                corps_message=f'noma:{EMAIL_TEMPLATE_ENROLLMENT_GENERATED_NOMA_TOKEN}',
                auteur=self.sic_manager_user.person.global_id,
            )
        )

        email_notification = EmailNotification.objects.filter(person=self.admission.candidate).first()
        self.assertIsNotNone(email_notification)

        email_object = message_from_string(email_notification.payload, policy=policy.default)
        self.assertIn('noma:123456789', email_object.get_body(('plain',)).get_content())

        email_notification.delete()

        # From the merge proposal person model
        merge_proposal = PersonMergeProposal(
            status=PersonMergeStatus.MERGED.name,
            original_person=self.admission.candidate,
            proposal_merge_person=PersonFactory(),
            last_similarity_result_update=datetime.datetime.now(),
            registration_id_sent_to_digit='987654321',
        )

        merge_proposal.save()

        message_bus_instance.invoke(
            EnvoyerEmailApprobationInscriptionAuCandidatCommand(
                uuid_proposition=self.admission.uuid,
                objet_message='subject',
                corps_message=f'noma:{EMAIL_TEMPLATE_ENROLLMENT_GENERATED_NOMA_DOCTORATE_TOKEN}',
                auteur=self.sic_manager_user.person.global_id,
            )
        )

        email_notification = EmailNotification.objects.filter(person=self.admission.candidate).first()
        self.assertIsNotNone(email_notification)

        email_object = message_from_string(email_notification.payload, policy=policy.default)
        self.assertIn('noma:987654321', email_object.get_body(('plain',)).get_content())
