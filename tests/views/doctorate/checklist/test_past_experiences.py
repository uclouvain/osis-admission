# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
import json
import uuid
from functools import partial
from unittest.mock import patch
from uuid import UUID

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext
from rest_framework import status

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    OngletsChecklist,
)
from admission.ddd.admission.shared_kernel.domain.model.enums.condition_acces import (
    TypeTitreAccesSelectionnable,
    recuperer_conditions_acces_par_formation,
)
from admission.ddd.admission.shared_kernel.enums.emplacement_document import (
    OngletsDemande,
)
from admission.models import DoctorateAdmission
from admission.models.valuated_epxeriences import (
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
    ProfessionalExperienceFactory,
)
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from admission.tests.factories.secondary_studies import (
    ForeignHighSchoolDiplomaFactory,
    HighSchoolDiplomaAlternativeFactory,
)
from admission.tests.views.doctorate.checklist.sic_decision.base import SicPatchMixin
from base.forms.utils.choice_field import BLANK_CHOICE
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.student import StudentFactory
from epc.models.enums.condition_acces import ConditionAcces
from epc.models.enums.decision_resultat_cycle import DecisionResultatCycle
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.enums.statut_inscription_programme_annuel import (
    StatutInscriptionProgrammAnnuel,
)
from epc.models.enums.type_duree import TypeDuree
from epc.tests.factories.inscription_programme_annuel import (
    InscriptionProgrammeAnnuelFactory,
)
from epc.tests.factories.inscription_programme_cycle import (
    InscriptionProgrammeCycleFactory,
)
from osis_profile.models import Exam
from osis_profile.models.enums.education import ForeignDiplomaTypes
from osis_profile.models.exam import EXAM_TYPE_PREMIER_CYCLE_LABEL_FR
from osis_profile.tests.factories.exam import ExamFactory


@freezegun.freeze_time('2023-01-01')
class PastExperiencesStatusViewTestCase(SicPatchMixin):
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
        cls.experiences.update(obtained_diploma=True)

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:doctorate:past-experiences-change-status'

    def setUp(self) -> None:
        super().setUp()
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=self.candidate,
            submitted=True,
        )
        self.url = resolve_url(
            self.url_name,
            uuid=self.admission.uuid,
            status=ChoixStatutChecklist.GEST_BLOCAGE.name,
        )

    def test_change_the_checklist_status_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_the_checklist_status_is_forbidden_with_sic_user_if_the_admission_is_in_fac_status(self):
        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.save()

        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_the_checklist_status_to_blocking(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.admission.refresh_from_db()

        self.assertEqual(
            self.admission.checklist['current']['parcours_anterieur']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())

        htmx_info = json.loads(response.headers['HX-Trigger'])
        self.assertTrue(htmx_info.get('formValidation', {}).get('select_access_title_perm'))

    def test_change_the_checklist_status_to_success(self):
        self.client.force_login(user=self.sic_manager_user)

        success_url = resolve_url(
            self.url_name,
            uuid=self.admission.uuid,
            status=ChoixStatutChecklist.GEST_REUSSITE.name,
        )

        self.admission.checklist['current'][OngletsChecklist.parcours_anterieur.name] = {
            'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
            'enfants': [
                {
                    'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
                    'extra': {
                        'identifiant': 'UNKNOWN',
                    },
                },
            ],
        }

        self.admission.save()

        # The success status requires at least one access title and an admission requirement
        error_message_if_missing_data = gettext("Some errors have been encountered.")

        response = self.client.post(success_url, **self.default_headers)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = [m.message for m in response.context['messages']]
        self.assertIn(error_message_if_missing_data, messages)
        self.assertNotIn(gettext('Your data have been saved.'), messages)

        # Check admission
        self.admission.refresh_from_db()
        self.assertNotEqual(
            self.admission.checklist['current']['parcours_anterieur']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )

        # Specify an admission requirement
        self.admission: DoctorateAdmission
        self.admission.admission_requirement = ConditionAcces.MASTER.name
        self.admission.admission_requirement_year = self.academic_years[1]
        self.admission.save()

        # Specify an access title
        AdmissionEducationalValuatedExperiences.objects.create(
            baseadmission=self.admission,
            educationalexperience=self.experiences[0],
            is_access_title=True,
        )

        response = self.client.post(success_url, **self.default_headers)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = [m.message for m in response.context['messages']]
        self.assertIn(error_message_if_missing_data, messages)
        self.assertNotIn(gettext('Your data have been saved.'), messages)

        # Check admission
        self.admission.refresh_from_db()
        self.assertNotEqual(
            self.admission.checklist['current']['parcours_anterieur']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )

        # Add checklist data for the valuated experience
        self.admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]['enfants'].append(
            {
                'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
                'extra': {
                    'identifiant': self.experiences[0].uuid,
                },
            }
        )
        self.admission.save()

        response = self.client.post(success_url, **self.default_headers)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = [m.message for m in response.context['messages']]
        self.assertIn(error_message_if_missing_data, messages)
        self.assertNotIn(gettext('Your data have been saved.'), messages)

        # Check admission
        self.admission.refresh_from_db()
        self.assertNotEqual(
            self.admission.checklist['current']['parcours_anterieur']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )

        # Change the status of the experience checklist
        self.admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]['enfants'][-1]['statut'] = (
            ChoixStatutChecklist.GEST_REUSSITE.name
        )
        self.admission.save()

        response = self.client.post(success_url, **self.default_headers)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = [m.message for m in response.context['messages']]
        self.assertNotIn(error_message_if_missing_data, messages)
        self.assertIn(gettext('Your data have been saved.'), messages)
        htmx_info = json.loads(response.headers['HX-Trigger'])
        self.assertFalse(htmx_info.get('formValidation', {}).get('select_access_title_perm'))
        self.assertEqual(
            htmx_info.get('formValidation', {}).get('select_access_title_tooltip'),
            gettext(
                'Changes for the access title are not available when the state of the Previous experience '
                'is "Sufficient".'
            ),
        )

        # Check admission
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.checklist['current']['parcours_anterieur']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())


@freezegun.freeze_time('2023-01-01')
class PastExperiencesAdmissionRequirementViewTestCase(SicPatchMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]

        cls.commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.commission)

        cls.training = DoctorateFactory(
            management_entity=cls.commission,
            academic_year=cls.academic_years[0],
            education_group_type__name=TrainingType.PHD.name,
        )

        cls.candidate = CompletePersonFactory(language=settings.LANGUAGE_CODE_FR)
        cls.experiences = cls.candidate.educationalexperience_set.all()
        cls.experiences.update(obtained_diploma=True)

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:doctorate:past-experiences-admission-requirement'

    def setUp(self) -> None:
        super().setUp()

        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=self.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )
        self.url = resolve_url(self.url_name, uuid=self.admission.uuid)

    def test_specify_the_admission_requirement_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_specify_the_admission_requirement_is_forbidden_with_sic_user_if_the_admission_is_in_fac_status(self):
        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.save()

        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_initialization_of_the_form(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['past_experiences_admission_requirement_form']

        admission_choices = [
            (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
            (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
            (ConditionAcces.VALORISATION_300_ECTS.name, ConditionAcces.VALORISATION_300_ECTS.label),
        ]
        self.assertEqual(form.fields['admission_requirement'].choices, BLANK_CHOICE + admission_choices)
        self.assertFalse(form.fields['admission_requirement'].disabled)
        self.assertFalse(form.fields['admission_requirement_year'].disabled)

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.PHD.name),
            [
                (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
                (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
                (ConditionAcces.VALORISATION_300_ECTS.name, ConditionAcces.VALORISATION_300_ECTS.label),
                (ConditionAcces.PARCOURS.name, ConditionAcces.PARCOURS.label),
            ],
        )

        self.admission.checklist['current']['parcours_anterieur']['statut'] = 'GEST_REUSSITE'
        self.admission.save(update_fields=['checklist'])

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['past_experiences_admission_requirement_form']

        self.assertTrue(form.fields['admission_requirement'].disabled)
        self.assertTrue(form.fields['admission_requirement_year'].disabled)

    def test_post_form_with_admission_requirement_without_access_titles(self):
        self.client.force_login(user=self.sic_manager_user)

        # No data
        response = self.client.post(self.url, **self.default_headers, data={})

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the admission
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.admission_requirement, '')
        self.assertEqual(self.admission.admission_requirement_year, None)

        # With data
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'admission_requirement': ConditionAcces.MASTER.name,
                'admission_requirement_year': self.academic_years[0].pk,
            },
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the admission
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.admission_requirement, ConditionAcces.MASTER.name)
        self.assertEqual(self.admission.admission_requirement_year, self.academic_years[0])

    def test_post_form_with_admission_requirement_with_access_titles(self):
        self.client.force_login(user=self.sic_manager_user)

        # Specify one access title -> the admission requirement year will be based on it
        AdmissionEducationalValuatedExperiences.objects.create(
            baseadmission=self.admission,
            educationalexperience=self.experiences[0],
            is_access_title=True,
        )

        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'admission_requirement': ConditionAcces.MASTER.name,
                'admission_requirement_year': self.academic_years[0].pk,
            },
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the admission
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.admission_requirement, ConditionAcces.MASTER.name)
        self.assertEqual(self.admission.admission_requirement_year, self.academic_years[2])

        # We just change the admission requirement year -> it will be based on the specified year in the form
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'admission_requirement': ConditionAcces.MASTER.name,
                'admission_requirement_year': self.academic_years[1].pk,
            },
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the admission
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.admission_requirement, ConditionAcces.MASTER.name)
        self.assertEqual(self.admission.admission_requirement_year, self.academic_years[1])

        # Specify two access titles -> the admission requirement year will be based on the specified year in the form
        self.admission.are_secondary_studies_access_title = True
        self.admission.save()

        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'admission_requirement': ConditionAcces.MASTER.name,
                'admission_requirement_year': self.academic_years[0].pk,
            },
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the admission
        self.admission.refresh_from_db()

        self.assertEqual(self.admission.admission_requirement, ConditionAcces.MASTER.name)
        self.assertEqual(self.admission.admission_requirement_year, self.academic_years[0])


@freezegun.freeze_time('2023-01-01')
class PastExperiencesAccessTitleViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.commission)

        cls.training = DoctorateFactory(
            management_entity=cls.commission,
            academic_year=cls.academic_years[0],
            education_group_type__name=TrainingType.PHD.name,
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:doctorate:past-experiences-access-title'

    def setUp(self) -> None:
        self.candidate = CompletePersonFactory(language=settings.LANGUAGE_CODE_FR)

        self.exam = ExamFactory(
            person=self.candidate,
            year=self.academic_years[1],
            type__education_group_years=[self.training],
        )

        self.educational_experiences = self.candidate.educationalexperience_set.all()
        self.educational_experiences.update(obtained_diploma=True)
        self.non_educational_experience = ProfessionalExperienceFactory(person=self.candidate)

        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=self.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )
        self.url = resolve_url(self.url_name, uuid=self.admission.uuid)

    def test_specify_an_experience_as_access_title_is_sometimes_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        # If the admission is in fac status
        self.admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the past experience checklist tab status is 'Sufficient'
        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.checklist['current']['parcours_anterieur']['statut'] = 'GEST_REUSSITE'
        self.admission.save(update_fields=['checklist', 'status'])

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_specify_an_experience_as_access_title_is_sometimes_forbidden_with_sic_user(self):
        # If the admission is in fac status
        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.save()

        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the past experience checklist tab status is 'Sufficient'
        self.admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        self.admission.checklist['current']['parcours_anterieur']['statut'] = 'GEST_REUSSITE'
        self.admission.save(update_fields=['checklist', 'status'])

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def assertDjangoMessage(self, response, message):
        messages = [m.message for m in response.context['messages']]
        self.assertIn(message, messages)

    def test_specify_a_cv_educational_experience_as_access_title(self):
        self.client.force_login(user=self.sic_manager_user)

        # Select an unknown experience
        response = self.client.post(
            f'{self.url}?experience_uuid={uuid.uuid4()}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Experience not found.'))

        # Select a known experience but not valuated
        valid_url = (
            f'{self.url}?experience_uuid={self.educational_experiences[0].uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name}'
        )

        response = self.client.post(
            valid_url,
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Experience not found.'))

        # Valuate the experience
        valuated_experience: AdmissionEducationalValuatedExperiences = (
            AdmissionEducationalValuatedExperiences.objects.create(
                baseadmission=self.admission,
                educationalexperience=self.educational_experiences[0],
            )
        )

        # Select a known and valuated experience (with custom institute and program)
        response = self.client.post(
            valid_url,
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        valuated_experience.refresh_from_db()
        self.assertEqual(valuated_experience.is_access_title, True)

        # Unselect a known and valuated experience
        response = self.client.post(
            valid_url,
            **self.default_headers,
            data={},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        valuated_experience.refresh_from_db()
        self.assertEqual(valuated_experience.is_access_title, False)

    def test_specify_a_cv_non_educational_experience_as_access_title(self):
        self.client.force_login(user=self.sic_manager_user)

        # Select an unknown experience
        response = self.client.post(
            f'{self.url}?experience_uuid={uuid.uuid4()}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Experience not found.'))

        # Select a known experience but not valuated
        response = self.client.post(
            f'{self.url}?experience_uuid={self.non_educational_experience.uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Experience not found.'))

        # Valuate the experience
        valuated_experience: AdmissionProfessionalValuatedExperiences = (
            AdmissionProfessionalValuatedExperiences.objects.create(
                baseadmission=self.admission,
                professionalexperience=self.non_educational_experience,
            )
        )

        self.non_educational_experience.start_date = datetime.date(2022, 1, 1)
        self.non_educational_experience.end_date = datetime.date(2023, 12, 31)
        self.non_educational_experience.save(update_fields=['start_date', 'end_date'])

        # Select a known and valuated experience
        response = self.client.post(
            f'{self.url}?experience_uuid={valuated_experience.professionalexperience_id}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        valuated_experience.refresh_from_db()
        self.assertEqual(valuated_experience.is_access_title, True)

        # Select another known and valuated experience
        other_experience = ProfessionalExperienceFactory(person=self.candidate)
        other_experience_valuation = AdmissionProfessionalValuatedExperiences.objects.create(
            baseadmission=self.admission,
            professionalexperience=other_experience,
        )
        response = self.client.post(
            f'{self.url}?experience_uuid={other_experience_valuation.professionalexperience_id}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        other_experience_valuation.refresh_from_db()
        self.assertEqual(other_experience_valuation.is_access_title, True)

        # Unselect a known and valuated experience
        response = self.client.post(
            f'{self.url}?experience_uuid={valuated_experience.professionalexperience_id}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE.name}',
            **self.default_headers,
            data={},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        valuated_experience.refresh_from_db()
        self.assertEqual(valuated_experience.is_access_title, False)

    @patch("osis_document_components.fields.FileField._confirm_multiple_upload")
    def test_specify_the_higher_education_experience_as_access_title(self, confirm_multiple_upload):
        confirm_multiple_upload.side_effect = lambda _, value, __: (
            ["550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"] if value else []
        )

        self.client.force_login(user=self.sic_manager_user)

        # Select a known experience (be diploma)
        response = self.client.post(
            f'{self.url}?experience_uuid={self.candidate.belgianhighschooldiploma.uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        self.admission.refresh_from_db()
        self.assertTrue(self.admission.are_secondary_studies_access_title)

        # Unselect a known experience (be diploma)
        response = self.client.post(
            f'{self.url}?experience_uuid={self.candidate.belgianhighschooldiploma.uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name}',
            **self.default_headers,
            data={},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        self.admission.refresh_from_db()
        self.assertFalse(self.admission.are_secondary_studies_access_title)

        # Select a known experience (foreign diploma)
        self.candidate.belgianhighschooldiploma.delete()

        foreign_high_school_diploma = ForeignHighSchoolDiplomaFactory(
            country__name='France',
            person=self.candidate,
            foreign_diploma_type=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
        )

        response = self.client.post(
            f'{self.url}?experience_uuid={foreign_high_school_diploma.uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        self.admission.refresh_from_db()
        self.assertTrue(self.admission.are_secondary_studies_access_title)

        # Select a known experience (alternative diploma)
        # self.candidate.foreignhighschooldiploma.delete()
        self.admission.are_secondary_studies_access_title = False
        self.admission.save()

        self.candidate.graduated_from_high_school = GotDiploma.NO.name
        self.candidate.graduated_from_high_school_year = None
        self.candidate.save()

        high_school_diploma_alternative = HighSchoolDiplomaAlternativeFactory(
            person=self.candidate,
            certificate=['token.pdf'],
        )

        response = self.client.post(
            f'{self.url}?experience_uuid={high_school_diploma_alternative.uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.admission.refresh_from_db()
        self.assertTrue(self.admission.are_secondary_studies_access_title)

        # The candidate specified that he has secondary education but without more information
        Exam.objects.filter(person=self.candidate, type__label_fr=EXAM_TYPE_PREMIER_CYCLE_LABEL_FR).delete()

        self.admission.are_secondary_studies_access_title = False
        self.admission.save()

        self.candidate.graduated_from_high_school = GotDiploma.YES.name
        self.candidate.graduated_from_high_school_year = self.admission.training.academic_year
        self.candidate.save()

        response = self.client.post(
            f'{self.url}?experience_uuid={OngletsDemande.ETUDES_SECONDAIRES.name}'
            f'&experience_type={TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.admission.refresh_from_db()
        self.assertTrue(self.admission.are_secondary_studies_access_title)

    def test_specify_the_exam_as_access_title(self):
        self.client.force_login(user=self.sic_manager_user)

        # Select a known experience (be diploma)
        response = self.client.post(
            f'{self.url}?experience_uuid={self.exam.uuid}&experience_type={TypeTitreAccesSelectionnable.EXAMENS.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        self.admission.refresh_from_db()
        self.assertTrue(self.admission.is_exam_access_title)

        # Unselect a known experience (be diploma)
        response = self.client.post(
            f'{self.url}?experience_uuid={self.exam.uuid}&experience_type={TypeTitreAccesSelectionnable.EXAMENS.name}',
            **self.default_headers,
            data={},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        self.admission.refresh_from_db()
        self.assertFalse(self.admission.is_exam_access_title)

    def test_specify_an_internal_experience_as_access_title(self):
        self.client.force_login(user=self.sic_manager_user)

        self.admission.internal_access_titles.clear()

        student = StudentFactory(person=self.admission.candidate)

        pce_a = InscriptionProgrammeCycleFactory(
            etudiant=student,
            decision=DecisionResultatCycle.DISTINCTION.name,
            sigle_formation="SF1",
        )
        pce_a_uuid = str(UUID(int=pce_a.pk))
        InscriptionProgrammeAnnuelFactory(
            programme_cycle=pce_a,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__root_group__academic_year=self.academic_years[0],
            type_duree=TypeDuree.NORMAL.name,
        )

        # Select a known experience as access title
        response = self.client.post(
            f'{self.url}?experience_uuid={pce_a_uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_PARCOURS_INTERNE.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        internal_access_titles = self.admission.internal_access_titles.all()

        self.assertEqual(len(internal_access_titles), 1)
        self.assertEqual(internal_access_titles[0].pk, pce_a.pk)

        # Unselect the experience
        response = self.client.post(
            f'{self.url}?experience_uuid={pce_a_uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_PARCOURS_INTERNE.name}',
            **self.default_headers,
            data={},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        self.assertFalse(self.admission.internal_access_titles.exists())

    def test_choose_an_access_title_depends_on_previously_selected_access_titles(self):
        self.client.force_login(user=self.sic_manager_user)

        error_message = gettext(
            'The access titles can either be a single academic course or one or several non-academic activities.'
        )

        post_request = partial(
            self.client.post,
            **self.default_headers,
            data={'access-title': 'on'},
        )

        other_experience = EducationalExperienceFactory(person=self.candidate, obtained_diploma=True)
        EducationalExperienceYearFactory(educational_experience=other_experience, academic_year=self.academic_years[0])

        cv_academic_experiences_urls = [
            f'{self.url}?experience_uuid={experience.uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name}'
            for experience in self.educational_experiences
        ]

        cv_academic_experiences_valuations = [
            AdmissionEducationalValuatedExperiences.objects.create(
                baseadmission=self.admission,
                educationalexperience=experience,
            )
            for experience in self.educational_experiences
        ]

        # Select a first curriculum academic experience
        response = post_request(path=cv_academic_experiences_urls[0])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        cv_academic_experiences_valuations[0].refresh_from_db()
        self.assertEqual(cv_academic_experiences_valuations[0].is_access_title, True)

        # Select a second curriculum academic experience
        response = post_request(path=cv_academic_experiences_urls[1])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, error_message)

        cv_academic_experiences_valuations[1].refresh_from_db()
        self.assertEqual(cv_academic_experiences_valuations[1].is_access_title, False)

        # Select the secondary studies
        response = post_request(
            path=f'{self.url}?experience_uuid={self.candidate.belgianhighschooldiploma.uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, error_message)

        self.admission.refresh_from_db()
        self.assertFalse(self.admission.are_secondary_studies_access_title)

        # Select an exam
        exam = ExamFactory(
            person=self.admission.candidate,
            year=self.academic_years[1],
            type__education_group_years=[self.admission.training],
        )

        response = post_request(
            path=f'{self.url}?experience_uuid={exam.uuid}&experience_type={TypeTitreAccesSelectionnable.EXAMENS.name}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, error_message)

        self.admission.refresh_from_db()
        self.assertIsNone(self.admission.is_exam_access_title)

        # Select an internal experience
        student = StudentFactory(person=self.admission.candidate)

        pce_a = InscriptionProgrammeCycleFactory(
            etudiant=student,
            decision=DecisionResultatCycle.DISTINCTION.name,
            sigle_formation="SF1",
        )
        pce_a_uuid = str(UUID(int=pce_a.pk))
        InscriptionProgrammeAnnuelFactory(
            programme_cycle=pce_a,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__root_group__academic_year=self.academic_years[0],
            type_duree=TypeDuree.NORMAL.name,
        )

        response = self.client.post(
            f'{self.url}?experience_uuid={pce_a_uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_PARCOURS_INTERNE.name}',
            **self.default_headers,
            data={
                'access-title': 'on',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, error_message)

        internal_access_titles = self.admission.internal_access_titles.all()

        self.assertEqual(len(internal_access_titles), 0)

        # Select a curriculum non-academic experience
        valuated_experience: AdmissionProfessionalValuatedExperiences = (
            AdmissionProfessionalValuatedExperiences.objects.create(
                baseadmission=self.admission,
                professionalexperience=self.non_educational_experience,
            )
        )

        response = post_request(
            path=f'{self.url}?experience_uuid={self.non_educational_experience.uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE.name}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, error_message)

        valuated_experience.refresh_from_db()
        self.assertFalse(valuated_experience.is_access_title)
