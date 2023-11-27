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
import datetime
import uuid

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext
from rest_framework import status

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.base import (
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.domain.model.enums.equivalence import (
    TypeEquivalenceTitreAcces,
    StatutEquivalenceTitreAcces,
    EtatEquivalenceTitreAcces,
)
from admission.ddd.admission.domain.model.enums.condition_acces import (
    TypeTitreAccesSelectionnable,
    recuperer_conditions_acces_par_formation,
)

from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.forms.admission.checklist import PastExperiencesAdmissionAccessTitleForm
from admission.tests.factories.curriculum import ProfessionalExperienceFactory
from admission.tests.factories.general_education import (
    GeneralEducationTrainingFactory,
    GeneralEducationAdmissionFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.forms.utils.choice_field import BLANK_CHOICE
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from epc.models.enums.condition_acces import ConditionAcces


@freezegun.freeze_time('2023-01-01')
class PastExperiencesStatusViewTestCase(TestCase):
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
        cls.experiences.update(obtained_diploma=True)

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:general-education:past-experiences-change-status'

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=self.candidate,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )
        self.url = resolve_url(
            self.url_name,
            uuid=self.general_admission.uuid,
            status=ChoixStatutChecklist.GEST_BLOCAGE.name,
        )

    def test_change_the_checklist_status_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_the_checklist_status_is_forbidden_with_sic_user_if_the_admission_is_in_fac_status(self):
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save()

        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_the_checklist_status_to_blocking(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.general_admission.refresh_from_db()

        self.assertEqual(
            self.general_admission.checklist['current']['parcours_anterieur']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )

    def test_change_the_checklist_status_to_success(self):
        self.client.force_login(user=self.sic_manager_user)

        success_url = resolve_url(
            self.url_name,
            uuid=self.general_admission.uuid,
            status=ChoixStatutChecklist.GEST_REUSSITE.name,
        )

        # The success status requires at least one access title and an admission requirement
        error_message_if_missing_data = gettext(
            "To move to this state, an admission requirement must have been selected and at least one access title "
            "line must be selected in the past experience views.",
        )

        response = self.client.post(success_url, **self.default_headers)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = [m.message for m in response.context['messages']]
        self.assertIn(error_message_if_missing_data, messages)
        self.assertNotIn(gettext('Your data have been saved.'), messages)

        # Check admission
        self.general_admission.refresh_from_db()
        self.assertNotEqual(
            self.general_admission.checklist['current']['parcours_anterieur']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )

        # Specify an admission requirement
        self.general_admission: GeneralEducationAdmission
        self.general_admission.admission_requirement = ConditionAcces.BAC.name
        self.general_admission.admission_requirement_year = self.academic_years[1]
        self.general_admission.save()

        # Specify an access title
        AdmissionEducationalValuatedExperiences.objects.create(
            baseadmission=self.general_admission,
            educationalexperience=self.experiences[0],
            is_access_title=True,
        )

        response = self.client.post(success_url, **self.default_headers)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = [m.message for m in response.context['messages']]
        self.assertNotIn(error_message_if_missing_data, messages)
        self.assertIn(gettext('Your data have been saved.'), messages)

        # Check admission
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.checklist['current']['parcours_anterieur']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )


@freezegun.freeze_time('2023-01-01')
class PastExperiencesAdmissionRequirementViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]

        cls.commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.commission,
            academic_year=cls.academic_years[0],
            education_group_type__name=TrainingType.BACHELOR.name,
        )

        cls.candidate = CompletePersonFactory(language=settings.LANGUAGE_CODE_FR)
        cls.experiences = cls.candidate.educationalexperience_set.all()
        cls.experiences.update(obtained_diploma=True)

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:general-education:past-experiences-admission-requirement'

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=self.candidate,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )
        self.url = resolve_url(self.url_name, uuid=self.general_admission.uuid)

    def test_specify_the_admission_requirement_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_specify_the_admission_requirement_is_forbidden_with_sic_user_if_the_admission_is_in_fac_status(self):
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save()

        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_initialization_of_the_form_with_valid_initial_choices(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['past_experiences_admission_requirement_form']

        bachelor_choices = [
            (ConditionAcces.SECONDAIRE.name, ConditionAcces.SECONDAIRE.label),
            (ConditionAcces.EXAMEN_ADMISSION.name, ConditionAcces.EXAMEN_ADMISSION.label),
            (ConditionAcces.PARCOURS.name, ConditionAcces.PARCOURS.label),
            (ConditionAcces.VAE.name, ConditionAcces.VAE.label),
            (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
            (ConditionAcces.BAC.name, ConditionAcces.BAC.label),
            (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
        ]
        self.assertEqual(form.fields['admission_requirement'].choices, BLANK_CHOICE + bachelor_choices)

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.BACHELOR.name),
            bachelor_choices,
        )

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.MASTER_MC.name),
            [
                (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
                (ConditionAcces.VALORISATION_240_ECTS.name, ConditionAcces.VALORISATION_240_ECTS.label),
                (ConditionAcces.VAE.name, ConditionAcces.VAE.label),
                (ConditionAcces.PARCOURS.name, ConditionAcces.PARCOURS.label),
                (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
            ],
        )

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.MASTER_MA_120.name),
            [
                (ConditionAcces.BAC.name, ConditionAcces.BAC.label),
                (ConditionAcces.BAMA15.name, ConditionAcces.BAMA15.label),
                (ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.name, ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.label),
                (ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.name, ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.label),
                (ConditionAcces.VALORISATION_180_ECTS.name, ConditionAcces.VALORISATION_180_ECTS.label),
                (ConditionAcces.VAE.name, ConditionAcces.VAE.label),
                (ConditionAcces.PARCOURS.name, ConditionAcces.PARCOURS.label),
                (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
                (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
            ],
        )

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.MASTER_MD_120.name),
            [
                (ConditionAcces.BAC.name, ConditionAcces.BAC.label),
                (ConditionAcces.BAMA15.name, ConditionAcces.BAMA15.label),
                (ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.name, ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.label),
                (ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.name, ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.label),
                (ConditionAcces.VALORISATION_180_ECTS.name, ConditionAcces.VALORISATION_180_ECTS.label),
                (ConditionAcces.VAE.name, ConditionAcces.VAE.label),
                (ConditionAcces.PARCOURS.name, ConditionAcces.PARCOURS.label),
                (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
                (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
            ],
        )

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.MASTER_MS_120.name),
            [
                (ConditionAcces.BAC.name, ConditionAcces.BAC.label),
                (ConditionAcces.BAMA15.name, ConditionAcces.BAMA15.label),
                (ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.name, ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.label),
                (ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.name, ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.label),
                (ConditionAcces.VALORISATION_180_ECTS.name, ConditionAcces.VALORISATION_180_ECTS.label),
                (ConditionAcces.VAE.name, ConditionAcces.VAE.label),
                (ConditionAcces.PARCOURS.name, ConditionAcces.PARCOURS.label),
                (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
                (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
            ],
        )

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.MASTER_MS_180_240.name),
            [
                (ConditionAcces.BAC.name, ConditionAcces.BAC.label),
                (ConditionAcces.BAMA15.name, ConditionAcces.BAMA15.label),
                (ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.name, ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.label),
                (ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.name, ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.label),
                (ConditionAcces.VALORISATION_180_ECTS.name, ConditionAcces.VALORISATION_180_ECTS.label),
                (ConditionAcces.VAE.name, ConditionAcces.VAE.label),
                (ConditionAcces.PARCOURS.name, ConditionAcces.PARCOURS.label),
                (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
                (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
            ],
        )

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.MASTER_M1.name),
            [
                (ConditionAcces.BAC.name, ConditionAcces.BAC.label),
                (ConditionAcces.BAMA15.name, ConditionAcces.BAMA15.label),
                (ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.name, ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE.label),
                (ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.name, ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE.label),
                (ConditionAcces.VALORISATION_180_ECTS.name, ConditionAcces.VALORISATION_180_ECTS.label),
                (ConditionAcces.VAE.name, ConditionAcces.VAE.label),
                (ConditionAcces.PARCOURS.name, ConditionAcces.PARCOURS.label),
                (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
                (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
            ],
        )

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.RESEARCH_CERTIFICATE.name),
            [],
        )

        self.assertEqual(recuperer_conditions_acces_par_formation(TrainingType.CERTIFICATE.name), [])

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.AGGREGATION.name),
            [
                (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
                (ConditionAcces.PARCOURS.name, ConditionAcces.PARCOURS.label),
                (ConditionAcces.MASTER_EPM.name, ConditionAcces.MASTER_EPM.label),
                (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
            ],
        )

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.CAPAES.name),
            [
                (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
                (ConditionAcces.PARCOURS.name, ConditionAcces.PARCOURS.label),
                (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
                (ConditionAcces.VALORISATION_180_ECTS.name, ConditionAcces.VALORISATION_180_ECTS.label),
                (ConditionAcces.VAE.name, ConditionAcces.VAE.label),
            ],
        )

        self.assertEqual(
            recuperer_conditions_acces_par_formation(TrainingType.PHD.name),
            [
                (ConditionAcces.MASTER.name, ConditionAcces.MASTER.label),
                (ConditionAcces.UNI_SNU_AUTRE.name, ConditionAcces.UNI_SNU_AUTRE.label),
                (ConditionAcces.VALORISATION_300_ECTS.name, ConditionAcces.VALORISATION_300_ECTS.label),
                (ConditionAcces.PARCOURS.name, ConditionAcces.PARCOURS.label),
            ],
        )

    def test_post_form_with_admission_requirement_without_access_titles(self):
        self.client.force_login(user=self.sic_manager_user)

        # No data
        response = self.client.post(self.url, **self.default_headers, data={})

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the admission
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.admission_requirement, '')
        self.assertEqual(self.general_admission.admission_requirement_year, None)

        # With data
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'admission_requirement': ConditionAcces.BAC.name,
                'admission_requirement_year': self.academic_years[0].pk,
            },
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the admission
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.admission_requirement, ConditionAcces.BAC.name)
        self.assertEqual(self.general_admission.admission_requirement_year, self.academic_years[0])

    def test_post_form_with_admission_requirement_with_access_titles(self):
        self.client.force_login(user=self.sic_manager_user)

        # Specify one access title -> the admission requirement year will be based on it
        AdmissionEducationalValuatedExperiences.objects.create(
            baseadmission=self.general_admission,
            educationalexperience=self.experiences[0],
            is_access_title=True,
        )

        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'admission_requirement': ConditionAcces.BAC.name,
                'admission_requirement_year': self.academic_years[0].pk,
            },
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the admission
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.admission_requirement, ConditionAcces.BAC.name)
        self.assertEqual(self.general_admission.admission_requirement_year, self.academic_years[2])

        # We just change the admission requirement year -> it will be based on the specified year in the form
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'admission_requirement': ConditionAcces.BAC.name,
                'admission_requirement_year': self.academic_years[1].pk,
            },
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the admission
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.admission_requirement, ConditionAcces.BAC.name)
        self.assertEqual(self.general_admission.admission_requirement_year, self.academic_years[1])

        # Specify two access titles -> the admission requirement year will be based on the specified year in the form
        self.general_admission.are_secondary_studies_access_title = True
        self.general_admission.save()

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
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.admission_requirement, ConditionAcces.MASTER.name)
        self.assertEqual(self.general_admission.admission_requirement_year, self.academic_years[0])


@freezegun.freeze_time('2023-01-01')
class PastExperiencesAccessTitleEquivalencyViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.commission,
            academic_year=cls.academic_years[0],
            education_group_type__name=TrainingType.BACHELOR.name,
        )

        cls.candidate = CompletePersonFactory(language=settings.LANGUAGE_CODE_FR)

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:general-education:past-experiences-access-title-equivalency'
        cls.default_data = {
            'foreign_access_title_equivalency_type': TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
            'foreign_access_title_equivalency_status': StatutEquivalenceTitreAcces.COMPLETE.name,
            'foreign_access_title_equivalency_state': EtatEquivalenceTitreAcces.DEFINITIVE.name,
            'foreign_access_title_equivalency_effective_date': datetime.date(2023, 1, 1),
        }

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=self.candidate,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )
        self.url = resolve_url(self.url_name, uuid=self.general_admission.uuid)

    def test_specify_the_title_equivalency_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_specify_the_title_equivalency_is_forbidden_with_sic_user_if_the_admission_is_in_fac_status(self):
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save()

        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_form_initialization(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['past_experiences_admission_access_title_equivalency_form']

        self.assertIsInstance(form, PastExperiencesAdmissionAccessTitleForm)

    def test_submit_form_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)

        # The equivalency type is missing
        response = self.client.post(
            self.url,
            **self.default_headers,
            data={
                'foreign_access_title_equivalency_type': '',
            },
        )

        # Check the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['past_experiences_admission_access_title_equivalency_form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('foreign_access_title_equivalency_type', []))

        # The equivalency status is missing
        for equivalency_type in [
            TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
            TypeEquivalenceTitreAcces.EQUIVALENCE_GRADE_ACADEMIQUE_FWB.name,
            TypeEquivalenceTitreAcces.EQUIVALENCE_DE_NIVEAU.name,
        ]:
            response = self.client.post(
                self.url,
                **self.default_headers,
                data={
                    'foreign_access_title_equivalency_type': equivalency_type,
                    'foreign_access_title_equivalency_status': '',
                },
            )

            # Check the response
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            form = response.context['past_experiences_admission_access_title_equivalency_form']

            self.assertFalse(form.is_valid())
            self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('foreign_access_title_equivalency_status', []))

        # The equivalency state is missing
        for equivalency_status in [
            StatutEquivalenceTitreAcces.COMPLETE.name,
            StatutEquivalenceTitreAcces.RESTRICTIVE.name,
        ]:
            response = self.client.post(
                self.url,
                **self.default_headers,
                data={
                    'foreign_access_title_equivalency_type': TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
                    'foreign_access_title_equivalency_status': equivalency_status,
                    'foreign_access_title_equivalency_state': '',
                },
            )

            # Check the response
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            form = response.context['past_experiences_admission_access_title_equivalency_form']

            self.assertFalse(form.is_valid())
            self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('foreign_access_title_equivalency_state', []))

        # The equivalency date is missing
        for equivalency_state in [
            EtatEquivalenceTitreAcces.PROVISOIRE.name,
            EtatEquivalenceTitreAcces.DEFINITIVE.name,
        ]:
            response = self.client.post(
                self.url,
                **self.default_headers,
                data={
                    'foreign_access_title_equivalency_type': TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
                    'foreign_access_title_equivalency_status': StatutEquivalenceTitreAcces.COMPLETE.name,
                    'foreign_access_title_equivalency_state': equivalency_state,
                    'foreign_access_title_equivalency_effective_date': '',
                },
            )

            # Check the response
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            form = response.context['past_experiences_admission_access_title_equivalency_form']

            self.assertFalse(form.is_valid())
            self.assertIn(
                FIELD_REQUIRED_MESSAGE, form.errors.get('foreign_access_title_equivalency_effective_date', [])
            )

    def test_submit_form_with_valid_equivalency_type(self):
        self.client.force_login(user=self.sic_manager_user)

        # Check the equivalency type
        for equivalency_type in [
            TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
            TypeEquivalenceTitreAcces.EQUIVALENCE_GRADE_ACADEMIQUE_FWB.name,
            TypeEquivalenceTitreAcces.EQUIVALENCE_DE_NIVEAU.name,
        ]:
            response = self.client.post(
                self.url,
                **self.default_headers,
                data={
                    'foreign_access_title_equivalency_type': equivalency_type,
                    'foreign_access_title_equivalency_status': StatutEquivalenceTitreAcces.EN_ATTENTE.name,
                    'foreign_access_title_equivalency_state': EtatEquivalenceTitreAcces.DEFINITIVE.name,
                    'foreign_access_title_equivalency_effective_date': datetime.date(2023, 1, 1),
                },
            )

            # Check the response
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            form = response.context['past_experiences_admission_access_title_equivalency_form']

            self.assertTrue(form.is_valid())

            # Check the admission
            self.general_admission.refresh_from_db()
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_type, equivalency_type)
            self.assertEqual(
                self.general_admission.foreign_access_title_equivalency_status,
                StatutEquivalenceTitreAcces.EN_ATTENTE.name,
            )
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_state, '')
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_effective_date, None)

        for equivalency_type in [
            TypeEquivalenceTitreAcces.NON_CONCERNE.name,
            TypeEquivalenceTitreAcces.NON_RENSEIGNE.name,
        ]:
            response = self.client.post(
                self.url,
                **self.default_headers,
                data={
                    'foreign_access_title_equivalency_type': equivalency_type,
                    'foreign_access_title_equivalency_status': StatutEquivalenceTitreAcces.EN_ATTENTE.name,
                    'foreign_access_title_equivalency_state': EtatEquivalenceTitreAcces.DEFINITIVE.name,
                    'foreign_access_title_equivalency_effective_date': datetime.date(2023, 1, 1),
                },
            )

            # Check the response
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            form = response.context['past_experiences_admission_access_title_equivalency_form']

            self.assertTrue(form.is_valid())

            # Check the admission
            self.general_admission.refresh_from_db()
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_type, equivalency_type)
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_status, '')
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_state, '')
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_effective_date, None)

    def test_submit_form_with_valid_equivalency_status(self):
        self.client.force_login(user=self.sic_manager_user)

        # Check the equivalency type
        for equivalency_status in [
            StatutEquivalenceTitreAcces.COMPLETE.name,
            StatutEquivalenceTitreAcces.RESTRICTIVE.name,
        ]:
            response = self.client.post(
                self.url,
                **self.default_headers,
                data={
                    'foreign_access_title_equivalency_type': TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
                    'foreign_access_title_equivalency_status': equivalency_status,
                    'foreign_access_title_equivalency_state': EtatEquivalenceTitreAcces.DEFINITIVE.name,
                    'foreign_access_title_equivalency_effective_date': datetime.date(2023, 1, 1),
                },
            )

            # Check the response
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            form = response.context['past_experiences_admission_access_title_equivalency_form']

            self.assertTrue(form.is_valid())

            # Check the admission
            self.general_admission.refresh_from_db()
            self.assertEqual(
                self.general_admission.foreign_access_title_equivalency_type,
                TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
            )
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_status, equivalency_status)
            self.assertEqual(
                self.general_admission.foreign_access_title_equivalency_state, EtatEquivalenceTitreAcces.DEFINITIVE.name
            )
            self.assertEqual(
                self.general_admission.foreign_access_title_equivalency_effective_date, datetime.date(2023, 1, 1)
            )

        for equivalency_status in [
            StatutEquivalenceTitreAcces.EN_ATTENTE.name,
            StatutEquivalenceTitreAcces.NON_RENSEIGNE.name,
        ]:
            response = self.client.post(
                self.url,
                **self.default_headers,
                data={
                    'foreign_access_title_equivalency_type': TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
                    'foreign_access_title_equivalency_status': equivalency_status,
                    'foreign_access_title_equivalency_state': EtatEquivalenceTitreAcces.DEFINITIVE.name,
                    'foreign_access_title_equivalency_effective_date': datetime.date(2023, 1, 1),
                },
            )

            # Check the response
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            form = response.context['past_experiences_admission_access_title_equivalency_form']

            self.assertTrue(form.is_valid())

            # Check the admission
            self.general_admission.refresh_from_db()
            self.assertEqual(
                self.general_admission.foreign_access_title_equivalency_type,
                TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
            )
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_status, equivalency_status)
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_state, '')
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_effective_date, None)

    def test_submit_form_with_valid_equivalency_state(self):
        self.client.force_login(user=self.sic_manager_user)

        # Check the equivalency type
        for equivalency_state in [
            EtatEquivalenceTitreAcces.DEFINITIVE.name,
            EtatEquivalenceTitreAcces.PROVISOIRE.name,
        ]:
            response = self.client.post(
                self.url,
                **self.default_headers,
                data={
                    'foreign_access_title_equivalency_type': TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
                    'foreign_access_title_equivalency_status': StatutEquivalenceTitreAcces.COMPLETE.name,
                    'foreign_access_title_equivalency_state': equivalency_state,
                    'foreign_access_title_equivalency_effective_date': datetime.date(2023, 1, 1),
                },
            )

            # Check the response
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            form = response.context['past_experiences_admission_access_title_equivalency_form']

            self.assertTrue(form.is_valid())

            # Check the admission
            self.general_admission.refresh_from_db()
            self.assertEqual(
                self.general_admission.foreign_access_title_equivalency_type,
                TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
            )
            self.assertEqual(
                self.general_admission.foreign_access_title_equivalency_status,
                StatutEquivalenceTitreAcces.COMPLETE.name,
            )
            self.assertEqual(self.general_admission.foreign_access_title_equivalency_state, equivalency_state)
            self.assertEqual(
                self.general_admission.foreign_access_title_equivalency_effective_date, datetime.date(2023, 1, 1)
            )


@freezegun.freeze_time('2023-01-01')
class PastExperiencesAccessTitleViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.commission,
            academic_year=cls.academic_years[0],
            education_group_type__name=TrainingType.BACHELOR.name,
        )

        cls.candidate = CompletePersonFactory(language=settings.LANGUAGE_CODE_FR)

        cls.educational_experiences = cls.candidate.educationalexperience_set.all()
        cls.educational_experiences.update(obtained_diploma=True)
        cls.non_educational_experience = ProfessionalExperienceFactory(person=cls.candidate)

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.url_name = 'admission:general-education:past-experiences-access-title'

    def setUp(self) -> None:
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=self.candidate,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )
        self.url = resolve_url(self.url_name, uuid=self.general_admission.uuid)

    def test_specify_an_experience_as_access_title_is_forbidden_with_fac_user_if_the_admission_is_in_sic_status(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_specify_an_experience_as_access_title_is_forbidden_with_sic_user_if_the_admission_is_in_fac_status(self):
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save()

        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.url, **self.default_headers)

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
        response = self.client.post(
            f'{self.url}?experience_uuid={self.educational_experiences[0].uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name}',
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
                baseadmission=self.general_admission,
                educationalexperience=self.educational_experiences[0],
            )
        )

        # Select a known and valuated experience
        response = self.client.post(
            f'{self.url}?experience_uuid={valuated_experience.educationalexperience_id}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name}',
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
            f'{self.url}?experience_uuid={valuated_experience.educationalexperience_id}'
            f'&experience_type={TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name}',
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
                baseadmission=self.general_admission,
                professionalexperience=self.non_educational_experience,
            )
        )

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

    def test_specify_the_higher_education_experience_as_access_title(self):
        self.client.force_login(user=self.sic_manager_user)

        # Select a known experience
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

        self.general_admission.refresh_from_db()
        self.assertTrue(self.general_admission.are_secondary_studies_access_title)

        # Unselect a known experience
        response = self.client.post(
            f'{self.url}?experience_uuid={self.candidate.belgianhighschooldiploma.uuid}'
            f'&experience_type={TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name}',
            **self.default_headers,
            data={},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDjangoMessage(response, gettext('Your data have been saved.'))

        self.general_admission.refresh_from_db()
        self.assertFalse(self.general_admission.are_secondary_studies_access_title)
