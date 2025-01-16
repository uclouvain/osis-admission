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
import datetime

import freezegun
from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import TestCase
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification

from admission.constants import ORDERED_CAMPUSES_UUIDS
from admission.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import ENTITY_CDE
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
    TypeDeRefus,
)
from admission.infrastructure.admission.formation_generale.domain.service.pdf_generation import ENTITY_SIC, ENTITY_SICB
from admission.templatetags.admission import SAINT_LOUIS, MONS
from admission.tests.factories.faculty_decision import RefusalReasonFactory
from admission.tests.factories.general_education import (
    GeneralEducationTrainingFactory,
    GeneralEducationAdmissionFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from admission.tests.views.general_education.checklist.sic_decision.base import SicPatchMixin
from base.models.campus import Campus, LOUVAIN_LA_NEUVE_CAMPUS_NAME
from base.models.enums.mandate_type import MandateTypes
from base.models.enums.organization_type import MAIN
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.mandatary import MandataryFactory
from osis_profile import BE_ISO_CODE
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2022-01-01')
class SicRefusalFinalDecisionViewTestCase(SicPatchMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        country = CountryFactory(iso_code=BE_ISO_CODE)

        cls.louvain_training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
            enrollment_campus=CampusFactory(
                name=LOUVAIN_LA_NEUVE_CAMPUS_NAME,
                location="Place 1",
                postal_code="1348",
                city="Louvain-la-Neuve",
                country=country,
                street="University street",
                postal_box="1",
                street_number="2",
                sic_enrollment_email="louvain@test.be",
                uuid=ORDERED_CAMPUSES_UUIDS['LOUVAIN_LA_NEUVE_UUID'],
                organization__type=MAIN,
            ),
        )
        cls.saint_louis_training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
            enrollment_campus=CampusFactory(
                name=SAINT_LOUIS,
                location="Place 2",
                postal_code="1000",
                city="Bruxelles",
                country=country,
                street="University road",
                postal_box="3",
                street_number="4",
                sic_enrollment_email="saint_louis@test.be",
                uuid=ORDERED_CAMPUSES_UUIDS['BRUXELLES_SAINT_LOUIS_UUID'],
                organization__type=MAIN,
            ),
        )
        cls.mons_training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
            enrollment_campus=CampusFactory(
                name=MONS,
                location="Place 3",
                postal_code="7000",
                city="Mons",
                country=country,
                street="University place",
                postal_box="5",
                street_number="6",
                sic_enrollment_email="mons@test.be",
                uuid=ORDERED_CAMPUSES_UUIDS['MONS_UUID'],
                organization__type=MAIN,
            ),
        )

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

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(
            education_group=cls.louvain_training.education_group,
        ).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=cls.louvain_training,
            admitted=True,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name,
            refusal_type=TypeDeRefus.REFUS_AGREGATION.name,
        )
        cls.general_admission.refusal_reasons.add(RefusalReasonFactory())
        cls.url = resolve_url(
            'admission:general-education:sic-decision-refusal-final',
            uuid=cls.general_admission.uuid,
        )

    def test_submit_refusal_final_decision_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_refusal_final_decision_form_initialization(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

    def test_refusal_final_decision_form_submitting(self):
        self.client.force_login(user=self.sic_manager_user)

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'sic-decision-refusal-final-subject': 'subject',
                'sic-decision-refusal-final-body': 'body',
                'sic-decision-refusal-final-submitted': '',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get('HX-Refresh'))

        form = response.context['sic_decision_refusal_final_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.INSCRIPTION_REFUSEE.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['extra'],
            {'blocage': 'refusal'},
        )
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        # Check the mail is sent
        self.assertTrue(
            EmailNotification.objects.filter(
                person=self.general_admission.candidate, payload__contains='subject'
            ).exists()
        )

        # Check that history entries are created
        entries: QuerySet[HistoryEntry] = HistoryEntry.objects.filter(
            object_uuid=self.general_admission.uuid,
        )

        self.assertEqual(len(entries), 2)

        status_change_entry = next((entry for entry in entries if 'status-changed' in entry.tags), None)
        message_entry = next((entry for entry in entries if 'message' in entry.tags), None)

        self.assertIsNotNone(status_change_entry)
        self.assertIsNotNone(message_entry)

        self.assertCountEqual(
            ['proposition', 'sic-decision', 'refusal', 'status-changed'],
            status_change_entry.tags,
        )

        self.assertEqual(
            status_change_entry.author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        # Check that the refusal certificate contains the right data
        self.get_pdf_from_template_patcher.assert_called_once()

        call_args = self.get_pdf_from_template_patcher.call_args_list[0]
        self.assertIn('director', call_args[0][2])

        director = call_args[0][2]['director']
        self.assertEqual(director, self.sic_director_mandate.person)

        footer_campus = call_args[0][2]['footer_campus']
        training_campus: Campus = self.louvain_training.enrollment_campus

        self.assertEqual(footer_campus.uuid, training_campus.uuid)

    def test_refusal_final_decision_form_submitting_for_a_saint_louis_training(self):
        self.client.force_login(user=self.sic_manager_user)

        self.general_admission.training = self.saint_louis_training
        self.general_admission.save(update_fields=['training'])

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'sic-decision-refusal-final-subject': 'subject',
                'sic-decision-refusal-final-body': 'body',
                'sic-decision-refusal-final-submitted': '',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the refusal certificate contains the right data
        self.get_pdf_from_template_patcher.assert_called_once()

        call_args = self.get_pdf_from_template_patcher.call_args_list[0]
        self.assertIn('director', call_args[0][2])

        director = call_args[0][2]['director']
        self.assertEqual(director, self.sic_b_director_mandate.person)

        footer_campus = call_args[0][2]['footer_campus']
        training_campus: Campus = self.saint_louis_training.enrollment_campus

        self.assertEqual(footer_campus.uuid, training_campus.uuid)

    def test_refusal_final_decision_form_submitting_for_a_mons_training(self):
        self.client.force_login(user=self.sic_manager_user)

        self.general_admission.training = self.mons_training
        self.general_admission.save(update_fields=['training'])

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'sic-decision-refusal-final-subject': 'subject',
                'sic-decision-refusal-final-body': 'body',
                'sic-decision-refusal-final-submitted': '',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the refusal certificate contains the right data
        self.get_pdf_from_template_patcher.assert_called_once()

        call_args = self.get_pdf_from_template_patcher.call_args_list[0]
        self.assertIn('director', call_args[0][2])

        director = call_args[0][2]['director']
        self.assertEqual(director, self.sic_director_mandate.person)

        footer_campus = call_args[0][2]['footer_campus']
        training_campus: Campus = self.louvain_training.enrollment_campus

        self.assertEqual(footer_campus.uuid, training_campus.uuid)

    def test_refusal_final_decision_form_submitting_inscription(self):
        self.client.force_login(user=self.sic_manager_user)
        self.general_admission.type_demande = TypeDemande.INSCRIPTION.name
        self.general_admission.save()

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'sic-decision-refusal-final-subject': 'subject',
                'sic-decision-refusal-final-body': 'body',
                'sic-decision-refusal-final-submitted': '',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get('HX-Refresh'))

        form = response.context['sic_decision_refusal_final_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.INSCRIPTION_REFUSEE.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['extra'],
            {'blocage': 'refusal'},
        )
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        # Check that the refusal certificate contains the right data
        self.get_pdf_from_template_patcher.assert_called_once()

        call_args = self.get_pdf_from_template_patcher.call_args_list[0]
        self.assertIn('director', call_args[0][2])

        director = call_args[0][2]['director']
        self.assertEqual(director, self.sic_director_mandate.person)

        footer_campus = call_args[0][2]['footer_campus']
        training_campus: Campus = self.louvain_training.enrollment_campus

        self.assertEqual(footer_campus.uuid, training_campus.uuid)

    def test_refusal_final_decision_form_submitting_inscription_for_a_saint_louis_training(self):
        self.client.force_login(user=self.sic_manager_user)
        self.general_admission.type_demande = TypeDemande.INSCRIPTION.name
        self.general_admission.training = self.saint_louis_training
        self.general_admission.save()

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'sic-decision-refusal-final-subject': 'subject',
                'sic-decision-refusal-final-body': 'body',
                'sic-decision-refusal-final-submitted': '',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the refusal certificate contains the right data
        self.get_pdf_from_template_patcher.assert_called_once()

        call_args = self.get_pdf_from_template_patcher.call_args_list[0]
        self.assertIn('director', call_args[0][2])

        director = call_args[0][2]['director']
        self.assertEqual(director, self.sic_b_director_mandate.person)

        footer_campus = call_args[0][2]['footer_campus']
        training_campus: Campus = self.saint_louis_training.enrollment_campus

        self.assertEqual(footer_campus.uuid, training_campus.uuid)

    def test_refusal_final_decision_form_submitting_inscription_for_a_mons_training(self):
        self.client.force_login(user=self.sic_manager_user)
        self.general_admission.type_demande = TypeDemande.INSCRIPTION.name
        self.general_admission.training = self.mons_training
        self.general_admission.save()

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'sic-decision-refusal-final-subject': 'subject',
                'sic-decision-refusal-final-body': 'body',
                'sic-decision-refusal-final-submitted': '',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check that the refusal certificate contains the right data
        self.get_pdf_from_template_patcher.assert_called_once()

        call_args = self.get_pdf_from_template_patcher.call_args_list[0]
        self.assertIn('director', call_args[0][2])

        director = call_args[0][2]['director']
        self.assertEqual(director, self.sic_director_mandate.person)

        footer_campus = call_args[0][2]['footer_campus']
        training_campus: Campus = self.louvain_training.enrollment_campus

        self.assertEqual(footer_campus.uuid, training_campus.uuid)

    def test_refusal_final_decision_form_submitting_without_email(self):
        self.client.force_login(user=self.sic_manager_user)

        self.general_admission.refusal_type = TypeDeRefus.REFUS_LIBRE.name
        self.general_admission.save(update_fields=['refusal_type'])

        # Choose an existing reason
        response = self.client.post(
            self.url,
            data={
                'sic-decision-refusal-final-subject': '',
                'sic-decision-refusal-final-body': '',
                'sic-decision-refusal-final-submitted': '',
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get('HX-Refresh'))

        form = response.context['sic_decision_refusal_final_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.INSCRIPTION_REFUSEE.name)
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['extra'],
            {'blocage': 'refusal'},
        )
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        # Check the mail is not sent
        self.assertFalse(
            EmailNotification.objects.filter(
                person=self.general_admission.candidate, payload__contains='subject'
            ).exists()
        )

        # Check that history entries are created
        entries: QuerySet[HistoryEntry] = HistoryEntry.objects.filter(
            object_uuid=self.general_admission.uuid,
        )

        self.assertEqual(len(entries), 1)

        status_change_entry = next((entry for entry in entries if 'status-changed' in entry.tags), None)
        message_entry = next((entry for entry in entries if 'message' in entry.tags), None)

        self.assertIsNotNone(status_change_entry)
        self.assertIsNone(message_entry)

        self.assertCountEqual(
            ['proposition', 'sic-decision', 'refusal', 'status-changed'],
            status_change_entry.tags,
        )

        self.assertEqual(
            status_change_entry.author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        # Check that the pdf is not generated
        self.get_pdf_from_template_patcher.assert_not_called()
