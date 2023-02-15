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
from unittest.mock import patch

import freezegun
from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.admission.domain.service.i_elements_confirmation import IElementsConfirmation
from admission.ddd.admission.domain.validator.exceptions import (
    NombrePropositionsSoumisesDepasseException,
    QuestionsSpecifiquesInformationsComplementairesNonCompleteesException,
)
from admission.ddd.admission.enums import CritereItemFormulaireFormation, Onglets
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    EtudesSecondairesNonCompleteesException,
)
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    ProfessionalExperienceFactory,
)
from admission.tests.factories.form_item import AdmissionFormItemInstantiationFactory, TextAdmissionFormItemFactory
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.person import IncompletePersonForBachelorFactory, IncompletePersonForIUFCFactory
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from osis_profile.models import EducationalExperience, ProfessionalExperience


@freezegun.freeze_time("1980-02-25")
class GeneralPropositionSubmissionTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        AdmissionAcademicCalendarFactory.produce_all_required(quantity=6)

        # Validation errors
        cls.candidate_errors = IncompletePersonForBachelorFactory()
        cls.admission = GeneralEducationAdmissionFactory(
            candidate=cls.candidate_errors,
            # force type to have access conditions
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__acronym="FOOBAR",
        )
        cls.error_url = resolve_url("admission_api_v1:submit-general-proposition", uuid=cls.admission.uuid)

        # Validation ok
        cls.admission_ok = GeneralEducationAdmissionFactory(
            training__academic_year__year=1980,
            candidate__country_of_citizenship__european_union=True,
            bachelor_with_access_conditions_met=True,
        )
        cls.second_admission_ok = GeneralEducationAdmissionFactory(
            candidate__country_of_citizenship__european_union=True,
            bachelor_with_access_conditions_met=True,
            training=cls.admission_ok.training,
        )
        cls.third_admission_ok = GeneralEducationAdmissionFactory(
            candidate=cls.second_admission_ok.candidate,
            bachelor_with_access_conditions_met=True,
            training=cls.admission_ok.training,
        )
        cls.candidate_ok = cls.admission_ok.candidate
        cls.second_candidate_ok = cls.second_admission_ok.candidate
        cls.ok_url = resolve_url("admission_api_v1:submit-general-proposition", uuid=cls.admission_ok.uuid)
        cls.second_ok_url = resolve_url(
            "admission_api_v1:submit-general-proposition",
            uuid=cls.second_admission_ok.uuid,
        )
        cls.third_ok_url = resolve_url(
            "admission_api_v1:submit-general-proposition",
            uuid=cls.third_admission_ok.uuid,
        )
        # Ensure we have this training available for the next acad
        GeneralEducationTrainingFactory(
            academic_year__year=1980,
            education_group_type=cls.admission_ok.training.education_group_type,
            acronym=cls.admission_ok.training.acronym,
            partial_acronym=cls.admission_ok.training.partial_acronym,
        )
        cls.data_ok = {
            'pool': AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN.name,
            'annee': 1980,
            'elements_confirmation': {
                'reglement_general': IElementsConfirmation.REGLEMENT_GENERAL,
                'protection_donnees': IElementsConfirmation.PROTECTION_DONNEES,
                'professions_reglementees': IElementsConfirmation.PROFESSIONS_REGLEMENTEES,
                'justificatifs': IElementsConfirmation.JUSTIFICATIFS
                % {'by_service': _("by the UCLouvain Registration Service")},
                'declaration_sur_lhonneur': IElementsConfirmation.DECLARATION_SUR_LHONNEUR
                % {'to_service': _("to the UCLouvain Registration Service")},
            },
        }

    def test_general_proposition_verification_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        response = self.client.get(self.error_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ret = response.json()
        self.assertIn("ADMISSION-2", [e["status_code"] for e in ret['errors']])
        self.assertEqual(ret['access_conditions_url'], 'https://uclouvain.be/prog-1979-FOOBAR-cond_adm')

    def test_general_proposition_submission_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        data = {
            'pool': AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN.name,
            'annee': 1980,
        }
        response = self.client.post(self.error_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_general_proposition_verification_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        response = self.client.get(self.ok_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ret = response.json()
        self.assertEqual(len(ret['errors']), 0)
        self.admission_ok.refresh_from_db()

        response = self.client.get(resolve_url("admission_api_v1:general_propositions", uuid=self.admission_ok.uuid))
        ret = response.json()
        self.assertEqual(ret['pot_calcule'], AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN.name)
        self.assertIsNotNone(ret['date_fin_pot'])

    def test_general_proposition_verification_ok_valuate_experiences(self):
        educational_experience = EducationalExperienceFactory(person=self.second_candidate_ok)
        professional_experience = ProfessionalExperienceFactory(person=self.second_candidate_ok)

        self.client.force_authenticate(user=self.second_candidate_ok.user)

        # First submission
        response = self.client.post(self.second_ok_url, data=self.data_ok)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.second_admission_ok.refresh_from_db()

        # Valuation of the secondary studies
        self.assertEqual(self.second_admission_ok.valuated_secondary_studies_person, self.second_candidate_ok)

        # Valuation of the curriculum experiences
        self.assertEqual(len(self.second_admission_ok.educational_valuated_experiences.all()), 1)
        self.assertEqual(len(self.second_admission_ok.professional_valuated_experiences.all()), 1)
        self.assertEqual(
            self.second_admission_ok.educational_valuated_experiences.first().uuid,
            educational_experience.uuid,
        )
        self.assertEqual(
            self.second_admission_ok.professional_valuated_experiences.first().uuid,
            professional_experience.uuid,
        )

        # Second submission
        response = self.client.post(self.third_ok_url, data=self.data_ok)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.third_admission_ok.refresh_from_db()

        # Valuation of the secondary studies
        self.assertEqual(self.third_admission_ok.valuated_secondary_studies_person, None)

        # Valuation of the curriculum experiences
        self.assertEqual(len(self.third_admission_ok.educational_valuated_experiences.all()), 1)
        self.assertEqual(len(self.third_admission_ok.professional_valuated_experiences.all()), 1)
        self.assertEqual(
            self.third_admission_ok.educational_valuated_experiences.first().uuid,
            educational_experience.uuid,
        )
        self.assertEqual(
            self.third_admission_ok.professional_valuated_experiences.first().uuid,
            professional_experience.uuid,
        )

    def test_general_proposition_verification_contingent_non_ouvert(self):
        admission = GeneralEducationAdmissionFactory(
            is_non_resident=True,
            candidate=IncompletePersonForBachelorFactory(),
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__acronym="VETE1BA",
        )
        url = resolve_url("admission_api_v1:submit-general-proposition", uuid=admission.uuid)
        self.client.force_authenticate(user=admission.candidate.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ret = response.json()
        self.assertIsNotNone(ret['pool_start_date'])
        self.assertIsNotNone(ret['pool_end_date'])

    def test_general_proposition_submission_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        self.assertEqual(self.admission_ok.status, ChoixStatutPropositionGenerale.IN_PROGRESS.name)
        response = self.client.post(self.ok_url, self.data_ok)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.admission_ok.refresh_from_db()
        self.assertEqual(self.admission_ok.status, ChoixStatutPropositionGenerale.SUBMITTED.name)

    @freezegun.freeze_time("1980-11-25")
    def test_general_proposition_submission_ok_hors_delai(self):
        ProfessionalExperienceFactory(
            person=self.candidate_ok,
            start_date=datetime.date(1979, 1, 25),
            end_date=datetime.date(1980, 11, 25),
        )
        training = GeneralEducationTrainingFactory(
            academic_year__year=1981,
            education_group_type=self.admission_ok.training.education_group_type,
            acronym=self.admission_ok.training.acronym,
            partial_acronym=self.admission_ok.training.partial_acronym,
        )
        data_ok = {
            'pool': AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN.name,
            'annee': 1981,
            'elements_confirmation': {
                'hors_delai': IElementsConfirmation.HORS_DELAI % {'year': '1981-1982'},
                'reglement_general': IElementsConfirmation.REGLEMENT_GENERAL,
                'protection_donnees': IElementsConfirmation.PROTECTION_DONNEES,
                'professions_reglementees': IElementsConfirmation.PROFESSIONS_REGLEMENTEES,
                'justificatifs': IElementsConfirmation.JUSTIFICATIFS
                % {'by_service': _("by the UCLouvain Registration Service")},
                'declaration_sur_lhonneur': IElementsConfirmation.DECLARATION_SUR_LHONNEUR
                % {'to_service': _("to the UCLouvain Registration Service")},
            },
        }
        self.client.force_authenticate(user=self.candidate_ok.user)
        self.assertNotEqual(self.admission_ok.training, training)
        response = self.client.post(self.ok_url, data_ok)
        self.admission_ok.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(self.admission_ok.status, ChoixStatutPropositionGenerale.SUBMITTED.name)
        self.assertEqual(self.admission_ok.training, training)

    def test_general_proposition_submission_bad_pool(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        data = {
            'pool': AcademicCalendarTypes.ADMISSION_POOL_HUE5_BELGIUM_RESIDENCY.name,
            'annee': 1980,
        }
        response = self.client.post(self.ok_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_general_proposition_verification_too_much_submitted_propositions(self):
        GeneralEducationAdmissionFactory(
            candidate=self.candidate_ok,
            status=ChoixStatutPropositionGenerale.SUBMITTED.name,
        )
        GeneralEducationAdmissionFactory(
            candidate=self.candidate_ok,
            status=ChoixStatutPropositionGenerale.SUBMITTED.name,
        )
        self.client.force_authenticate(user=self.candidate_ok.user)
        response = self.client.get(self.ok_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ret = response.json()
        self.assertIn(NombrePropositionsSoumisesDepasseException.status_code, [e["status_code"] for e in ret['errors']])


@freezegun.freeze_time('2022-12-10')
class ContinuingPropositionSubmissionTestCase(APITestCase):
    @classmethod
    @patch("osis_document.contrib.fields.FileField._confirm_upload")
    def setUpTestData(cls, confirm_upload):
        confirm_upload.return_value = "550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"
        AdmissionAcademicCalendarFactory.produce_all_required()

        # Validation errors
        cls.candidate_errors = IncompletePersonForIUFCFactory()
        cls.admission = ContinuingEducationAdmissionFactory(
            candidate=cls.candidate_errors,
            # force type to have access conditions
            training__education_group_type__name=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
        )
        cls.error_url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=cls.admission.uuid)

        # Validation ok
        cls.admission_ok = ContinuingEducationAdmissionFactory(with_access_conditions_met=True)
        cls.candidate_ok = cls.admission_ok.candidate
        cls.ok_url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=cls.admission_ok.uuid)

        cls.second_admission_ok = ContinuingEducationAdmissionFactory(
            with_access_conditions_met=True,
            training=cls.admission_ok.training,
        )
        cls.third_admission_ok = ContinuingEducationAdmissionFactory(
            candidate=cls.second_admission_ok.candidate,
            with_access_conditions_met=True,
            training=cls.admission_ok.training,
        )

        cls.second_candidate_ok = cls.second_admission_ok.candidate

        cls.second_ok_url = resolve_url(
            "admission_api_v1:submit-continuing-proposition",
            uuid=cls.second_admission_ok.uuid,
        )
        cls.third_ok_url = resolve_url(
            "admission_api_v1:submit-continuing-proposition",
            uuid=cls.third_admission_ok.uuid,
        )

        cls.submitted_data = {
            'pool': AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name,
            'annee': 2022,
            'elements_confirmation': {
                'reglement_general': IElementsConfirmation.REGLEMENT_GENERAL,
                'protection_donnees': IElementsConfirmation.PROTECTION_DONNEES,
                'professions_reglementees': IElementsConfirmation.PROFESSIONS_REGLEMENTEES,
                'justificatifs': IElementsConfirmation.JUSTIFICATIFS
                % {'by_service': _("by the University Institute of Continuing Education")},
                'declaration_sur_lhonneur': IElementsConfirmation.DECLARATION_SUR_LHONNEUR
                % {'to_service': _("to the University Institute of Continuing Education")},
                'droits_inscription_iufc': IElementsConfirmation.DROITS_INSCRIPTION_IUFC,
            },
        }

    def test_continuing_proposition_verification_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        response = self.client.get(self.error_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = response.json()
        self.assertTrue(len(json_content['errors']) > 0, "Should have errors")
        self.assertCountEqual(
            json_content['errors'],
            [
                {
                    "status_code": "ADMISSION-2",
                    "detail": _("Admission conditions not met."),
                },
                {
                    "status_code": "FORMATION-CONTINUE-3",
                    "detail": _(
                        "Please specify the details of your most recent academic training and your most recent "
                        "non-academic experience."
                    ),
                },
            ],
        )

    def test_continuing_proposition_submission_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        response = self.client.post(self.error_url, self.submitted_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_continuing_proposition_verification_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        response = self.client.get(self.ok_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['errors'], [])

    def test_continuing_proposition_submission_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        self.assertEqual(self.admission_ok.status, ChoixStatutPropositionContinue.IN_PROGRESS.name)
        response = self.client.post(self.ok_url, self.submitted_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.admission_ok.refresh_from_db()
        self.assertEqual(self.admission_ok.status, ChoixStatutPropositionContinue.SUBMITTED.name)

    def test_continuing_proposition_verification_ok_valuate_experiences(self):
        educational_experience = EducationalExperience.objects.filter(person=self.second_candidate_ok).first()
        professional_experience = ProfessionalExperience.objects.filter(person=self.second_candidate_ok).first()

        self.client.force_authenticate(user=self.second_candidate_ok.user)

        # First submission
        response = self.client.post(self.second_ok_url, data=self.submitted_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.second_admission_ok.refresh_from_db()

        # Valuation of the secondary studies
        self.assertEqual(self.second_admission_ok.valuated_secondary_studies_person, self.second_candidate_ok)

        # Valuation of the curriculum experiences
        self.assertEqual(len(self.second_admission_ok.educational_valuated_experiences.all()), 1)
        self.assertEqual(len(self.second_admission_ok.professional_valuated_experiences.all()), 1)
        self.assertEqual(
            self.second_admission_ok.educational_valuated_experiences.first().uuid,
            educational_experience.uuid,
        )
        self.assertEqual(
            self.second_admission_ok.professional_valuated_experiences.first().uuid,
            professional_experience.uuid,
        )

        # Second submission
        response = self.client.post(self.third_ok_url, data=self.submitted_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.third_admission_ok.refresh_from_db()

        # Valuation of the secondary studies
        self.assertEqual(self.third_admission_ok.valuated_secondary_studies_person, None)

        # Valuation of the curriculum experiences
        self.assertEqual(len(self.third_admission_ok.educational_valuated_experiences.all()), 1)
        self.assertEqual(len(self.third_admission_ok.professional_valuated_experiences.all()), 1)
        self.assertEqual(
            self.third_admission_ok.educational_valuated_experiences.first().uuid,
            educational_experience.uuid,
        )
        self.assertEqual(
            self.third_admission_ok.professional_valuated_experiences.first().uuid,
            professional_experience.uuid,
        )

    def test_continuing_proposition_verification_too_much_submitted_propositions(self):
        ContinuingEducationAdmissionFactory(
            candidate=self.candidate_ok,
            status=ChoixStatutPropositionContinue.SUBMITTED.name,
        )
        ContinuingEducationAdmissionFactory(
            candidate=self.candidate_ok,
            status=ChoixStatutPropositionContinue.SUBMITTED.name,
        )
        self.client.force_authenticate(user=self.candidate_ok.user)
        response = self.client.get(self.ok_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ret = response.json()
        self.assertIn(NombrePropositionsSoumisesDepasseException.status_code, [e["status_code"] for e in ret['errors']])

    def test_continuing_proposition_submission_with_secondary_studies(self):
        admission = ContinuingEducationAdmissionFactory(candidate__graduated_from_high_school=GotDiploma.YES.name)
        url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=admission.uuid)
        self.client.force_authenticate(user=admission.candidate.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertIn(
            EtudesSecondairesNonCompleteesException.status_code,
            [e["status_code"] for e in json_response['errors']],
        )

        admission.candidate.graduated_from_high_school_year = self.candidate_ok.graduated_from_high_school_year
        admission.candidate.save()
        self.client.force_authenticate(user=admission.candidate.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertNotIn(
            EtudesSecondairesNonCompleteesException.status_code,
            [e["status_code"] for e in json_response['errors']],
        )

    def test_continuing_proposition_submission_with_specific_questions(self):
        admission = ContinuingEducationAdmissionFactory()
        admission_form_item = TextAdmissionFormItemFactory()
        AdmissionFormItemInstantiationFactory(
            form_item=admission_form_item,
            required=True,
            display_according_education=CritereItemFormulaireFormation.TOUTE_FORMATION.name,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
            academic_year=admission.training.academic_year,
        )
        admission_form_item.refresh_from_db()

        self.client.force_authenticate(user=admission.candidate.user)

        url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=admission.uuid)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        status_codes = [e["status_code"] for e in json_response['errors']]
        self.assertIn(QuestionsSpecifiquesInformationsComplementairesNonCompleteesException.status_code, status_codes)

        admission.specific_question_answers = {str(admission_form_item.uuid): 'My answer'}
        admission.save()
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        status_codes = [e["status_code"] for e in json_response['errors']]
        self.assertNotIn(
            QuestionsSpecifiquesInformationsComplementairesNonCompleteesException.status_code, status_codes
        )
