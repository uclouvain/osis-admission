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
import uuid
from email import message_from_string
from email.message import Message

import freezegun
from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification
from rest_framework import status

from admission.contrib.models import DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import ChoixStatutChecklist
from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory


@freezegun.freeze_time('2023-01-01')
class SinglePastExperienceChangeStatusViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.commission)

        cls.training = DoctorateFactory(
            management_entity=cls.commission,
            academic_year=cls.academic_years[0],
        )

        cls.candidate = CompletePersonFactory(language=settings.LANGUAGE_CODE_FR)
        cls.experiences = cls.candidate.educationalexperience_set.all()

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:doctorate:single-past-experience-change-status'

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=self.candidate,
            submitted=True,
        )

        self.admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                'libelle': 'To be processed',
                'extra': {
                    'identifiant': self.experiences[0].uuid,
                },
            }
        ]

        self.admission.save(update_fields=['checklist'])

        self.url = (
            resolve_url(
                self.url_name,
                uuid=self.admission.uuid,
            )
            + '?identifier='
            + str(self.experiences[0].uuid)
        )

    def test_change_the_checklist_status_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_unknown_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        unknown_uuid = str(uuid.uuid4())

        response = self.client.post(
            resolve_url(
                self.url_name,
                uuid=self.admission.uuid,
            )
            + '?identifier='
            + str(unknown_uuid),
            **self.default_headers,
            data={
                'status': ChoixStatutChecklist.GEST_BLOCAGE.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotIn(gettext('Experience not found.'), [m.message for m in response.context['messages']])

        self.admission.refresh_from_db()

        new_experience_data = next(
            (
                experience
                for experience in self.admission.checklist['current']['parcours_anterieur']['enfants']
                if experience['extra']['identifiant'] == unknown_uuid
            ),
            None,
        )

        self.assertIsNotNone(new_experience_data)

        self.assertEqual(new_experience_data['statut'], ChoixStatutChecklist.GEST_BLOCAGE.name)
        self.assertEqual(new_experience_data['extra']['identifiant'], unknown_uuid)

        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.today())

    def test_pass_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)

        # No data
        response = self.client.post(self.url, **self.default_headers, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('status', []))

        # Invalid status
        response = self.client.post(self.url, **self.default_headers, data={'status': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

        # Invalid authentication
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'status': ChoixStatutChecklist.GEST_BLOCAGE.name,
                'authentification': 'invalid_auth',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn('authentification', form.errors)

    def test_change_the_checklist_status_to_a_status_without_authentication_info(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'status': ChoixStatutChecklist.GEST_BLOCAGE.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.admission.refresh_from_db()

        experience_checklist = self.admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_BLOCAGE.name)

        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.today())

    def test_change_the_checklist_status_to_a_status_with_authentication(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'status': ChoixStatutChecklist.GEST_BLOCAGE.name,
                'authentification': '1',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.admission.refresh_from_db()

        experience_checklist = self.admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_BLOCAGE.name)

        self.assertEqual(experience_checklist['extra'].get('authentification'), '1')

        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.today())

    def test_change_the_checklist_status_to_a_status_without_authentication(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'status': ChoixStatutChecklist.GEST_BLOCAGE.name,
                'authentification': '0',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.admission.refresh_from_db()

        experience_checklist = self.admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_BLOCAGE.name)

        self.assertEqual(experience_checklist['extra'].get('authentification'), '0')

        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.today())


@freezegun.freeze_time('2023-01-01')
class SinglePastExperienceChangeAuthenticationViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.commission)

        cls.training = DoctorateFactory(
            management_entity=cls.commission,
            academic_year=cls.academic_years[0],
        )

        cls.candidate = CompletePersonFactory(language=settings.LANGUAGE_CODE_FR)
        cls.experiences = cls.candidate.educationalexperience_set.all()
        cls.first_experience_uuid = str(cls.experiences[0].uuid)

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:doctorate:single-past-experience-change-authentication'

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=self.candidate,
            submitted=True,
        )

        self.admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                'libelle': 'To be processed',
                'extra': {
                    'identifiant': self.first_experience_uuid,
                },
            }
        ]

        self.admission.save(update_fields=['checklist'])

        self.url = (
            resolve_url(
                self.url_name,
                uuid=self.admission.uuid,
            )
            + '?identifier='
            + str(self.experiences[0].uuid)
        )

    def test_change_the_authentication_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_unknown_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            resolve_url(
                self.url_name,
                uuid=self.admission.uuid,
            )
            + '?identifier='
            + str(uuid.uuid4()),
            **self.default_headers,
            data={
                'status': ChoixStatutChecklist.GEST_BLOCAGE.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(gettext('Experience not found.'), [m.message for m in response.context['messages']])

    def test_form_initialization_if_the_checklist_status_is_not_related_to_the_authentication(self):
        self.client.force_login(user=self.sic_manager_user)

        experience_checklist = self.admission.checklist['current']['parcours_anterieur']['enfants'][0]
        experience_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        experience_checklist['extra']['authentification'] = '0'
        experience_checklist['extra']['etat_authentification'] = EtatAuthentificationParcours.VRAI.name

        self.admission.save(update_fields=['checklist'])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form.initial['state'], EtatAuthentificationParcours.VRAI.name)

        self.assertTrue(form.fields['state'].disabled)

    def test_form_initialization_if_the_checklist_status_is_related_to_the_authentication(self):
        self.client.force_login(user=self.sic_manager_user)

        experience_checklist = self.admission.checklist['current']['parcours_anterieur']['enfants'][0]
        experience_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        experience_checklist['extra']['authentification'] = '1'
        experience_checklist['extra']['etat_authentification'] = EtatAuthentificationParcours.VRAI.name

        self.admission.save(update_fields=['checklist'])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form.initial['state'], EtatAuthentificationParcours.VRAI.name)

        self.assertFalse(form.fields['state'].disabled)

    @freezegun.freeze_time('2023-01-10')
    def test_change_the_authentication_data(self):
        self.client.force_login(user=self.sic_manager_user)

        experience_checklist = self.admission.checklist['current']['parcours_anterieur']['enfants'][0]
        experience_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        experience_checklist['extra']['authentification'] = '1'
        experience_checklist['extra']['etat_authentification'] = EtatAuthentificationParcours.VRAI.name

        self.admission.save(update_fields=['checklist'])

        # Invalid state
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                self.first_experience_uuid + '-state': 'invalid',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn('state', form.errors)

        # Valid data
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                self.first_experience_uuid + '-state': EtatAuthentificationParcours.FAUX.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.admission.refresh_from_db()

        experience_checklist = self.admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_EN_COURS.name)
        self.assertEqual(experience_checklist['extra']['authentification'], '1')
        self.assertEqual(experience_checklist['extra']['etat_authentification'], EtatAuthentificationParcours.FAUX.name)

        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.today())

        # Check that no history entry has been created
        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.admission.uuid).count(), 0)

        # Check that no notification has been created
        self.assertEqual(EmailNotification.objects.filter(created_at=datetime.datetime.today()).count(), 0)

    @freezegun.freeze_time('2023-01-11')
    def test_change_the_authentication_data_by_informing_the_checkers(self):
        self.client.force_login(user=self.sic_manager_user)

        experience_checklist = self.admission.checklist['current']['parcours_anterieur']['enfants'][0]
        experience_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        experience_checklist['extra']['authentification'] = '1'
        experience_checklist['extra']['etat_authentification'] = EtatAuthentificationParcours.VRAI.name

        self.admission.save(update_fields=['checklist'])

        # Valid data
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                self.first_experience_uuid + '-state': EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.admission.refresh_from_db()

        experience_checklist = self.admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_EN_COURS.name)
        self.assertEqual(experience_checklist['extra']['authentification'], '1')
        self.assertEqual(
            experience_checklist['extra']['etat_authentification'],
            EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name,
        )

        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.today())

        # Check that the history entry has been created
        history_items: QuerySet[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.admission.uuid)

        self.assertEqual(len(history_items), 1)

        self.assertEqual(
            history_items[0].author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        self.assertCountEqual(
            history_items[0].tags,
            ['proposition', 'experience-authentication', 'authentication-request', 'message'],
        )

        # Check that the email has been sent
        email_notifications = EmailNotification.objects.filter(
            created_at=datetime.datetime.today(),
        )

        self.assertEqual(len(email_notifications), 1)
        self.assertEqual(email_notifications[0].person, None)

        email_object: Message = message_from_string(email_notifications[0].payload)
        self.assertEqual(email_object['To'], 'verificationcursus@uclouvain.be')

    @freezegun.freeze_time('2023-01-11')
    def test_change_the_authentication_data_by_informing_the_candidate(self):
        self.client.force_login(user=self.sic_manager_user)

        experience_checklist = self.admission.checklist['current']['parcours_anterieur']['enfants'][0]
        experience_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        experience_checklist['extra']['authentification'] = '1'
        experience_checklist['extra']['etat_authentification'] = EtatAuthentificationParcours.VRAI.name

        self.admission.save(update_fields=['checklist'])

        # Valid data
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                self.first_experience_uuid + '-state': EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.admission.refresh_from_db()

        experience_checklist = self.admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_EN_COURS.name)
        self.assertEqual(experience_checklist['extra']['authentification'], '1')
        self.assertEqual(
            experience_checklist['extra']['etat_authentification'],
            EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name,
        )

        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.today())

        # Check that the history entry has been created
        history_items: QuerySet[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.admission.uuid)

        self.assertEqual(len(history_items), 1)

        self.assertEqual(
            history_items[0].author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        self.assertCountEqual(
            history_items[0].tags,
            ['proposition', 'experience-authentication', 'institute-contact', 'message'],
        )

        # Check that the email has been sent to the candidate
        email_notifications = EmailNotification.objects.filter(created_at=datetime.datetime.today())

        self.assertEqual(len(email_notifications), 1)
        self.assertEqual(email_notifications[0].person, self.admission.candidate)

        email_object: Message = message_from_string(email_notifications[0].payload)
        self.assertEqual(email_object['To'], self.admission.candidate.private_email)
