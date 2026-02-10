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
from admission.ddd.admission.shared_kernel.domain.model.enums.authentification import (
    EtatAuthentificationParcours,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
)
from admission.models import GeneralEducationAdmission
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    EducationalExperienceYearFactory, ProfessionalExperienceFactory,
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
from base.models.enums.got_diploma import GotDiploma
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.hops import HopsFactory
from ddd.logic.shared_kernel.profil.domain.enums import TypeExperience
from osis_profile.models.enums.curriculum import EvaluationSystem, Result
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience
from osis_profile.tests.factories.exam import ExamFactory, FirstCycleExamFactory
from osis_profile.tests.factories.high_school_diploma import HighSchoolDiplomaFactory
from reference.tests.factories.country import CountryFactory


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
        cls.hops = HopsFactory(
            education_group_year=cls.training,
            ares_graca=1,
        )

        cls.country = CountryFactory(iso_code='BE')

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:general-education:single-past-experience-change-status'

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

    def test_change_the_checklist_status_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(
            resolve_url(
                self.url_name,
                uuid=self.general_admission.uuid,
                experience_type=TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name,
                experience_uuid=uuid.uuid4(),
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @freezegun.freeze_time('2024-01-01')
    def test_change_unknown_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        unknown_uuid = uuid.uuid4()

        response = self.client.post(
            resolve_url(
                self.url_name,
                uuid=self.general_admission.uuid,
                experience_type=TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name,
                experience_uuid=unknown_uuid,
            ),
            **self.default_headers,
            data={
                'status': ChoixStatutValidationExperience.A_COMPLETER.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(gettext('Experience not found.'), [m.message for m in response.context['messages']])

        self.general_admission.refresh_from_db()

        self.assertNotEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertNotEqual(self.general_admission.modified_at, datetime.datetime.now())

    def test_pass_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)

        experience = ProfessionalExperienceFactory(person=self.general_admission.candidate)

        url = resolve_url(
            self.url_name,
            uuid=self.general_admission.uuid,
            experience_type=TypeExperience.ACTIVITE_NON_ACADEMIQUE.name,
            experience_uuid=experience.uuid,
        )

        # No data
        response = self.client.post(url, **self.default_headers, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('status', []))

        # Invalid status
        response = self.client.post(url, **self.default_headers, data={'status': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    @freezegun.freeze_time('2024-01-01')
    def test_change_the_checklist_status_of_an_academic_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        experience = EducationalExperienceFactory(person=self.general_admission.candidate)

        url = resolve_url(
            self.url_name,
            uuid=self.general_admission.uuid,
            experience_type=TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name,
            experience_uuid=experience.uuid,
        )

        response = self.client.post(
            url,
            **self.default_headers,
            data={
                'status': ChoixStatutValidationExperience.A_COMPLETER.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        experience.refresh_from_db()

        self.assertEqual(experience.validation_status, ChoixStatutValidationExperience.A_COMPLETER.name)

    @freezegun.freeze_time('2024-01-01')
    def test_change_the_checklist_status_of_a_non_academic_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        experience = ProfessionalExperienceFactory(person=self.general_admission.candidate)

        url = resolve_url(
            self.url_name,
            uuid=self.general_admission.uuid,
            experience_type=TypeExperience.ACTIVITE_NON_ACADEMIQUE.name,
            experience_uuid=experience.uuid,
        )

        response = self.client.post(
            url,
            **self.default_headers,
            data={
                'status': ChoixStatutValidationExperience.A_COMPLETER.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        experience.refresh_from_db()

        self.assertEqual(experience.validation_status, ChoixStatutValidationExperience.A_COMPLETER.name)

    @freezegun.freeze_time('2024-01-01')
    def test_change_the_checklist_status_of_an_exam(self):
        self.client.force_login(user=self.sic_manager_user)

        exam = ExamFactory(
            person=self.general_admission.candidate,
            type__education_group_years=[self.general_admission.training],
        )

        url = resolve_url(
            self.url_name,
            uuid=self.general_admission.uuid,
            experience_type=TypeExperience.EXAMEN.name,
            experience_uuid=exam.uuid,
        )

        response = self.client.post(
            url,
            **self.default_headers,
            data={
                'status': ChoixStatutValidationExperience.A_COMPLETER.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        exam.refresh_from_db()

        self.assertEqual(exam.validation_status, ChoixStatutValidationExperience.A_COMPLETER.name)

    @freezegun.freeze_time('2024-01-01')
    def test_change_the_checklist_status_of_the_secondary_studies(self):
        self.client.force_login(user=self.sic_manager_user)

        high_school_diploma = HighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            got_diploma=GotDiploma.NO.name,
        )

        url = resolve_url(
            self.url_name,
            uuid=self.general_admission.uuid,
            experience_type=TypeExperience.ETUDES_SECONDAIRES.name,
            experience_uuid=high_school_diploma.uuid,
        )

        response = self.client.post(
            url,
            **self.default_headers,
            data={
                'status': ChoixStatutValidationExperience.A_COMPLETER.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        high_school_diploma.refresh_from_db()
        self.assertEqual(high_school_diploma.validation_status, ChoixStatutValidationExperience.A_COMPLETER.name)

        # Update the related exam if it exists
        exam = FirstCycleExamFactory(
            person=self.general_admission.candidate,
        )

        response = self.client.post(
            url,
            **self.default_headers,
            data={
                'status': ChoixStatutValidationExperience.VALIDEE.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        high_school_diploma.refresh_from_db()
        self.assertEqual(high_school_diploma.validation_status, ChoixStatutValidationExperience.VALIDEE.name)

        exam.refresh_from_db()
        self.assertEqual(exam.validation_status, ChoixStatutValidationExperience.VALIDEE.name)

    def test_change_the_checklist_status_to_the_validated_status_needs_a_complete_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        # Add an incomplete experience
        experience = EducationalExperienceFactory(
            person=self.general_admission.candidate,
            obtained_diploma=False,
            country=self.country,
            evaluation_type='',
            with_fwb_master_fields=True,
            with_complement=None,
        )
        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=self.general_admission.training.academic_year,
            result=Result.SUCCESS.name,
            registered_credit_number=10,
            acquired_credit_number=10,
        )

        url = resolve_url(
            self.url_name,
            uuid=self.general_admission.uuid,
            experience_type=TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name,
            experience_uuid=experience.uuid,
        )

        response = self.client.post(
            url,
            **self.default_headers,
            data={'status': ChoixStatutValidationExperience.VALIDEE.name},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(
            "L'expérience académique 'Computer science' est incomplète.",
            [m.message for m in response.context['messages']],
        )

        experience.refresh_from_db()

        self.assertEqual(experience.validation_status, ChoixStatutValidationExperience.A_TRAITER.name)

        experience.with_complement = False
        experience.save()

        response = self.client.post(
            url,
            **self.default_headers,
            data={'status': ChoixStatutValidationExperience.VALIDEE.name},
        )

        self.assertNotIn(
            "L'expérience académique 'Computer science' est incomplète.",
            [m.message for m in response.context['messages']],
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        experience.refresh_from_db()

        self.assertEqual(experience.validation_status, ChoixStatutValidationExperience.VALIDEE.name)

        # The experience training isn't the same as the admission one so the checking is different
        experience = EducationalExperienceFactory(
            person=self.general_admission.candidate,
            obtained_diploma=False,
            country=self.country,
            evaluation_type='',
            with_fwb_master_fields=True,
            with_complement=None,
        )
        experience.program.code_grade_acad = '2'
        experience.program.save()

        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=self.general_admission.training.academic_year,
            result=Result.SUCCESS.name,
            registered_credit_number=10,
            acquired_credit_number=10,
        )

        url = resolve_url(
            self.url_name,
            uuid=self.general_admission.uuid,
            experience_uuid=experience.uuid,
            experience_type=TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name,
        )

        response = self.client.post(
            url,
            **self.default_headers,
            data={'status': ChoixStatutValidationExperience.VALIDEE.name},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotIn(
            "L'expérience académique 'Computer science' est incomplète.",
            [m.message for m in response.context['messages']],
        )


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

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:general-education:single-past-experience-change-authentication'

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate__language=settings.LANGUAGE_CODE_FR,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

    def test_change_the_authentication_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(
            resolve_url(
                self.url_name,
                uuid=self.general_admission.uuid,
                experience_type=TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name,
                experience_uuid=uuid.uuid4(),
            ), **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_unknown_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            resolve_url(
                self.url_name,
                uuid=self.general_admission.uuid,
                experience_uuid=uuid.uuid4(),
                experience_type=TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name,
            ),
            **self.default_headers,
            data={
                'status': ChoixStatutValidationExperience.A_COMPLETER.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(gettext('Experience not found.'), [m.message for m in response.context['messages']])

    def test_form_initialization_if_the_checklist_status_is_not_related_to_the_authentication(self):
        self.client.force_login(user=self.sic_manager_user)

        experience = ProfessionalExperienceFactory(
            person=self.general_admission.candidate,
            validation_status=ChoixStatutValidationExperience.AVIS_EXPERT.name,
            authentication_status=EtatAuthentificationParcours.VRAI.name,
        )

        url = resolve_url(
            self.url_name,
            uuid=self.general_admission.uuid,
            experience_uuid=experience.uuid,
            experience_type=TypeExperience.ACTIVITE_NON_ACADEMIQUE.name,
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form.initial['state'], EtatAuthentificationParcours.VRAI.name)

        self.assertTrue(form.fields['state'].disabled)

    def test_form_initialization_if_the_checklist_status_is_related_to_the_authentication(self):
        self.client.force_login(user=self.sic_manager_user)

        experience = ProfessionalExperienceFactory(
            person=self.general_admission.candidate,
            validation_status=ChoixStatutValidationExperience.AUTHENTIFICATION.name,
            authentication_status=EtatAuthentificationParcours.VRAI.name,
        )

        url = resolve_url(
            self.url_name,
            uuid=self.general_admission.uuid,
            experience_uuid=experience.uuid,
            experience_type=TypeExperience.ACTIVITE_NON_ACADEMIQUE.name,
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form.initial['state'], EtatAuthentificationParcours.VRAI.name)

        self.assertFalse(form.fields['state'].disabled)
