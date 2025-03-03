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

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
)
from admission.ddd.admission.domain.model.enums.authentification import (
    EtatAuthentificationParcours,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
)
from admission.models import GeneralEducationAdmission
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
)
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from ddd.logic.shared_kernel.profil.domain.enums import TypeExperience
from osis_profile.models.enums.curriculum import EvaluationSystem, Result


@freezegun.freeze_time('2023-01-01')
class SinglePastExperienceChangeStatusViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.commission,
            academic_year=cls.academic_years[0],
        )

        cls.candidate = CompletePersonFactory(language=settings.LANGUAGE_CODE_FR)
        cls.experiences = cls.candidate.educationalexperience_set.all()

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:general-education:single-past-experience-change-status'

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=self.candidate,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        self.general_admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                'libelle': 'To be processed',
                'extra': {
                    'identifiant': self.experiences[0].uuid,
                },
            }
        ]

        self.general_admission.save(update_fields=['checklist'])

        self.url = (
            resolve_url(
                self.url_name,
                uuid=self.general_admission.uuid,
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
                uuid=self.general_admission.uuid,
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

        self.general_admission.refresh_from_db()

        new_experience_data = next(
            (
                experience
                for experience in self.general_admission.checklist['current']['parcours_anterieur']['enfants']
                if experience['extra']['identifiant'] == unknown_uuid
            ),
            None,
        )

        self.assertIsNotNone(new_experience_data)

        self.assertEqual(new_experience_data['statut'], ChoixStatutChecklist.GEST_BLOCAGE.name)
        self.assertEqual(new_experience_data['extra']['identifiant'], unknown_uuid)

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

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

        self.general_admission.refresh_from_db()

        experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_BLOCAGE.name)

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

    def test_change_the_checklist_status_to_the_validated_status_needs_a_complete_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        # Add an incomplete experience
        experience = EducationalExperienceFactory(
            person=self.candidate,
            obtained_diploma=False,
            country=self.experiences[0].country,
            evaluation_type='',
        )
        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=self.general_admission.training.academic_year,
            result=Result.SUCCESS.name,
            registered_credit_number=10,
            acquired_credit_number=10,
        )

        url = (
            resolve_url(
                self.url_name,
                uuid=self.general_admission.uuid,
            )
            + f'?identifier={experience.uuid}&type={TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name}'
        )

        response = self.client.post(
            url,
            **self.default_headers,
            data={'status': ChoixStatutChecklist.GEST_REUSSITE.name},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(
            "L'expérience académique 'Computer science' est incomplète.",
            [m.message for m in response.context['messages']],
        )

        self.general_admission.refresh_from_db()

        experiences_checklists = self.general_admission.checklist['current']['parcours_anterieur']['enfants']

        self.assertEqual(len(experiences_checklists), 1)

        experience.evaluation_type = EvaluationSystem.NO_CREDIT_SYSTEM.name
        experience.save()

        response = self.client.post(
            url,
            **self.default_headers,
            data={'status': ChoixStatutChecklist.GEST_REUSSITE.name},
        )

        self.assertNotIn(
            "L'expérience académique 'Computer science' est incomplète.",
            [m.message for m in response.context['messages']],
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.general_admission.refresh_from_db()

        experiences_checklists = self.general_admission.checklist['current']['parcours_anterieur']['enfants']

        self.assertEqual(len(experiences_checklists), 2)
        self.assertEqual(experiences_checklists[1]['extra']['identifiant'], str(experience.uuid))
        self.assertEqual(experiences_checklists[1]['statut'], ChoixStatutChecklist.GEST_REUSSITE.name)

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

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

        self.general_admission.refresh_from_db()

        experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_BLOCAGE.name)

        self.assertEqual(experience_checklist['extra'].get('authentification'), '1')

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

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

        self.general_admission.refresh_from_db()

        experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_BLOCAGE.name)

        self.assertEqual(experience_checklist['extra'].get('authentification'), '0')

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())


@freezegun.freeze_time('2023-01-01')
class SinglePastExperienceChangeAuthenticationViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.commission,
            academic_year=cls.academic_years[0],
        )

        cls.candidate = CompletePersonFactory(language=settings.LANGUAGE_CODE_FR)
        cls.experiences = cls.candidate.educationalexperience_set.all()
        cls.first_experience_uuid = str(cls.experiences[0].uuid)

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:general-education:single-past-experience-change-authentication'

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=self.candidate,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        self.general_admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                'libelle': 'To be processed',
                'extra': {
                    'identifiant': self.first_experience_uuid,
                },
            }
        ]

        self.general_admission.save(update_fields=['checklist'])

        self.url = (
            resolve_url(
                self.url_name,
                uuid=self.general_admission.uuid,
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
                uuid=self.general_admission.uuid,
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

        experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][0]
        experience_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        experience_checklist['extra']['authentification'] = '0'
        experience_checklist['extra']['etat_authentification'] = EtatAuthentificationParcours.VRAI.name

        self.general_admission.save(update_fields=['checklist'])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form.initial['state'], EtatAuthentificationParcours.VRAI.name)

        self.assertTrue(form.fields['state'].disabled)

    def test_form_initialization_if_the_checklist_status_is_related_to_the_authentication(self):
        self.client.force_login(user=self.sic_manager_user)

        experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][0]
        experience_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        experience_checklist['extra']['authentification'] = '1'
        experience_checklist['extra']['etat_authentification'] = EtatAuthentificationParcours.VRAI.name

        self.general_admission.save(update_fields=['checklist'])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form.initial['state'], EtatAuthentificationParcours.VRAI.name)

        self.assertFalse(form.fields['state'].disabled)

    @freezegun.freeze_time('2023-01-10')
    def test_change_the_authentication_data(self):
        self.client.force_login(user=self.sic_manager_user)

        experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][0]
        experience_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        experience_checklist['extra']['authentification'] = '1'
        experience_checklist['extra']['etat_authentification'] = EtatAuthentificationParcours.VRAI.name

        self.general_admission.save(update_fields=['checklist'])

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

        self.general_admission.refresh_from_db()

        experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_EN_COURS.name)
        self.assertEqual(experience_checklist['extra']['authentification'], '1')
        self.assertEqual(experience_checklist['extra']['etat_authentification'], EtatAuthentificationParcours.FAUX.name)

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        # Check that no history entry has been created
        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid).count(), 0)

        # Check that no notification has been created
        self.assertEqual(EmailNotification.objects.filter(created_at=datetime.datetime.now()).count(), 0)

    @freezegun.freeze_time('2023-01-11')
    def test_change_the_authentication_data_by_informing_the_checkers(self):
        self.client.force_login(user=self.sic_manager_user)

        experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][0]
        experience_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        experience_checklist['extra']['authentification'] = '1'
        experience_checklist['extra']['etat_authentification'] = EtatAuthentificationParcours.VRAI.name

        self.general_admission.save(update_fields=['checklist'])

        # Valid data
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                self.first_experience_uuid + '-state': EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.general_admission.refresh_from_db()

        experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_EN_COURS.name)
        self.assertEqual(experience_checklist['extra']['authentification'], '1')
        self.assertEqual(
            experience_checklist['extra']['etat_authentification'],
            EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name,
        )

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        # Check that the history entry has been created
        history_items: QuerySet[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

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
            created_at=datetime.datetime.now(),
        )

        self.assertEqual(len(email_notifications), 1)
        self.assertEqual(email_notifications[0].person, None)

        email_object: Message = message_from_string(email_notifications[0].payload)
        self.assertEqual(email_object['To'], 'verificationcursus@uclouvain.be')

    @freezegun.freeze_time('2023-01-11')
    def test_change_the_authentication_data_by_informing_the_candidate(self):
        self.client.force_login(user=self.sic_manager_user)

        experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][0]
        experience_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        experience_checklist['extra']['authentification'] = '1'
        experience_checklist['extra']['etat_authentification'] = EtatAuthentificationParcours.VRAI.name

        self.general_admission.save(update_fields=['checklist'])

        # Valid data
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                self.first_experience_uuid + '-state': EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.general_admission.refresh_from_db()

        experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][0]

        self.assertEqual(experience_checklist['statut'], ChoixStatutChecklist.GEST_EN_COURS.name)
        self.assertEqual(experience_checklist['extra']['authentification'], '1')
        self.assertEqual(
            experience_checklist['extra']['etat_authentification'],
            EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name,
        )

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        # Check that the history entry has been created
        history_items: QuerySet[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid)

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
        email_notifications = EmailNotification.objects.filter(created_at=datetime.datetime.now())

        self.assertEqual(len(email_notifications), 1)
        self.assertEqual(email_notifications[0].person, self.general_admission.candidate)

        email_object: Message = message_from_string(email_notifications[0].payload)
        self.assertEqual(email_object['To'], self.general_admission.candidate.private_email)
