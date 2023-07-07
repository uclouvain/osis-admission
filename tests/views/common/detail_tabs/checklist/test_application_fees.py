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
import json
from typing import List

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification

from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.tests.factories.general_education import (
    GeneralEducationTrainingFactory,
    GeneralEducationAdmissionFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory


class ApplicationFeesViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(
            entity=cls.first_doctoral_commission,
        )

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.second_sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.second_fac_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group
        ).person.user

        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def test_ask_the_payment_of_the_application_fees_to_the_candidate(self):
        self.client.force_login(user=self.sic_manager_user)

        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        url = resolve_url(
            'admission:general-education:application-fees',
            uuid=general_admission.uuid,
            status=ChoixStatutChecklist.GEST_BLOCAGE.name,
        )

        response = self.client.post(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        general_admission.refresh_from_db()

        # Check that the admission has been updated
        self.assertEqual(general_admission.status, ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name)
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['libelle'],
            'Must pay',
        )

        # Check that a notification has been sent
        message_created = EmailNotification.objects.filter(person=general_admission.candidate).exists()
        self.assertTrue(message_created)

        # Check that an entry in the history has been added
        history_item: HistoryEntry = HistoryEntry.objects.filter(object_uuid=general_admission.uuid).first()

        self.assertIsNotNone(history_item)

        self.assertEqual(
            history_item.author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        self.assertCountEqual(
            history_item.tags,
            ['proposition', 'application-fees-payment', 'request', 'status-changed'],
        )

        # Check context
        context = response.context
        self.assertEqual(context['last_request'], history_item)
        self.assertIsNotNone(context.get('checklist_tabs'))
        self.assertIsNotNone(context['request_message_subject'])
        self.assertIsNotNone(context['request_message_body'])
        self.assertFalse(context['fees_already_payed'])

        # Ask again
        response = self.client.post(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        htmx_trigger = json.loads(response['HX-Trigger'])
        self.assertTrue(len(htmx_trigger.get('messages')) > 1)

    def test_remind_the_payment_of_the_application_fees_to_the_candidate(self):
        self.client.force_login(user=self.sic_manager_user)

        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Ask for the first time
        url = resolve_url(
            'admission:general-education:application-fees',
            uuid=general_admission.uuid,
            status=ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        response = self.client.post(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Remind
        url = (
            resolve_url(
                'admission:general-education:application-fees',
                uuid=general_admission.uuid,
                status=ChoixStatutChecklist.GEST_BLOCAGE.name,
            )
            + '?remind=1'
        )
        response = self.client.post(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        general_admission.refresh_from_db()

        # Check that the admission has been updated
        self.assertEqual(general_admission.status, ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name)
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['libelle'],
            'Must pay',
        )

        # Check that two notifications have been sent
        messages_number = EmailNotification.objects.filter(person=general_admission.candidate).count()
        self.assertEqual(messages_number, 2)

        # Check that two entries in the history have been added
        history_items: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=general_admission.uuid)

        self.assertEqual(len(history_items), 2)

        self.assertEqual(
            history_items[0].author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        self.assertEqual(
            history_items[1].author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        self.assertCountEqual(
            history_items[0].tags,
            ['proposition', 'application-fees-payment', 'request'],
        )

        self.assertCountEqual(
            history_items[1].tags,
            ['proposition', 'application-fees-payment', 'request', 'status-changed'],
        )

    def test_cancel_the_request_of_the_payment_of_the_application_fees_initial_for_a_not_concerned_candidate(self):
        self.client.force_login(user=self.sic_manager_user)

        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Ask for the first time
        url = resolve_url(
            'admission:general-education:application-fees',
            uuid=general_admission.uuid,
            status=ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        response = self.client.post(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Cancel
        url = resolve_url(
            'admission:general-education:application-fees',
            uuid=general_admission.uuid,
            status=ChoixStatutChecklist.INITIAL_NON_CONCERNE.name,
        )
        response = self.client.post(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        general_admission.refresh_from_db()

        # Check that the admission has been updated
        self.assertEqual(general_admission.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['statut'],
            ChoixStatutChecklist.INITIAL_NON_CONCERNE.name,
        )
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['libelle'],
            'Not concerned',
        )

        # Check that two entries in the history have been added
        history_items: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=general_admission.uuid)

        self.assertEqual(len(history_items), 2)

        self.assertEqual(
            history_items[0].author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        self.assertEqual(
            history_items[1].author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        self.assertCountEqual(
            history_items[0].tags,
            ['proposition', 'application-fees-payment', 'cancel-request', 'status-changed'],
        )

        self.assertCountEqual(
            history_items[1].tags,
            ['proposition', 'application-fees-payment', 'request', 'status-changed'],
        )

    def test_cancel_the_request_of_the_payment_of_the_application_fees_initial_for_a_not_dispensed_candidate(self):
        self.client.force_login(user=self.sic_manager_user)

        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Ask for the first time
        url = resolve_url(
            'admission:general-education:application-fees',
            uuid=general_admission.uuid,
            status=ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        response = self.client.post(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Cancel
        url = resolve_url(
            'admission:general-education:application-fees',
            uuid=general_admission.uuid,
            status=ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        response = self.client.post(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        general_admission.refresh_from_db()

        # Check that the admission has been updated
        self.assertEqual(general_admission.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['libelle'],
            'Dispensed',
        )

        # Check that two entries in the history have been added
        history_items: List[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=general_admission.uuid)

        self.assertEqual(len(history_items), 2)

        self.assertEqual(
            history_items[0].author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        self.assertEqual(
            history_items[1].author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        self.assertCountEqual(
            history_items[0].tags,
            ['proposition', 'application-fees-payment', 'cancel-request', 'status-changed'],
        )

        self.assertCountEqual(
            history_items[1].tags,
            ['proposition', 'application-fees-payment', 'request', 'status-changed'],
        )

    def test_change_checklist_status_from_not_concerned_to_dispensed(self):
        self.client.force_login(user=self.sic_manager_user)

        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        general_admission.checklist['current']['frais_dossier'][
            'statut'
        ] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        general_admission.checklist['current']['frais_dossier']['libelle'] = 'Not concerned'

        general_admission.save()

        # Change the status
        url = resolve_url(
            'admission:general-education:application-fees',
            uuid=general_admission.uuid,
            status=ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        response = self.client.post(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        general_admission.refresh_from_db()

        # Check that the admission has been updated
        self.assertEqual(general_admission.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['libelle'],
            'Dispensed',
        )

        # Check that no entry in the history has been added
        has_history_items = HistoryEntry.objects.filter(object_uuid=general_admission.uuid).exists()
        self.assertFalse(has_history_items)

    def test_change_checklist_status_from_dispensed_to_not_concerned(self):
        self.client.force_login(user=self.sic_manager_user)

        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        general_admission.checklist['current']['frais_dossier']['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        general_admission.checklist['current']['frais_dossier']['libelle'] = 'Dispensed'

        general_admission.save()

        # Change the status
        url = resolve_url(
            'admission:general-education:application-fees',
            uuid=general_admission.uuid,
            status=ChoixStatutChecklist.INITIAL_NON_CONCERNE.name,
        )
        response = self.client.post(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        general_admission.refresh_from_db()

        # Check that the admission has been updated
        self.assertEqual(general_admission.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['statut'],
            ChoixStatutChecklist.INITIAL_NON_CONCERNE.name,
        )
        self.assertEqual(
            general_admission.checklist['current']['frais_dossier']['libelle'],
            'Not concerned',
        )

        # Check that no entry in the history has been added
        has_history_items = HistoryEntry.objects.filter(object_uuid=general_admission.uuid).exists()
        self.assertFalse(has_history_items)
