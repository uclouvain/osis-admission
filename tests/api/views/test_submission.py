# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################

import freezegun
from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AffiliationsNonCompleteesException,
    CarteBancaireRemboursementIbanNonCompleteException,
)
from admission.ddd.admission.domain.service.i_elements_confirmation import IElementsConfirmation
from admission.ddd.admission.domain.validator.exceptions import NombrePropositionsSoumisesDepasseException
from admission.ddd.admission.enums import ChoixTypeCompteBancaire
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    EtudesSecondairesNonCompleteesException,
)
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.curriculum import EducationalExperienceFactory, ProfessionalExperienceFactory
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.person import IncompletePersonForBachelorFactory, IncompletePersonForIUFCFactory
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from osis_profile.models import EducationalExperience


@freezegun.freeze_time("1980-03-25")
class GeneralPropositionSubmissionTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        AdmissionAcademicCalendarFactory.produce_all_required()

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
                'justificatifs': IElementsConfirmation.JUSTIFICATIFS,
                'declaration_sur_lhonneur': IElementsConfirmation.DECLARATION_SUR_LHONNEUR,
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
    def setUpTestData(cls):
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
                'justificatifs': IElementsConfirmation.JUSTIFICATIFS,
                'declaration_sur_lhonneur': IElementsConfirmation.DECLARATION_SUR_LHONNEUR,
            },
        }

    def test_continuing_proposition_verification_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        response = self.client.get(self.error_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = response.json()
        self.assertEqual(len(json_content['errors']), 1, "Should have errors")
        self.assertDictEqual(
            json_content['errors'][0],
            {"status_code": "ADMISSION-2", "detail": _("Admission conditions not met.")},
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
        professional_experience = ProfessionalExperienceFactory(person=self.second_candidate_ok)

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

    def test_continuing_proposition_submission_with_accounting(self):
        admission = ContinuingEducationAdmissionFactory()
        url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=admission.uuid)
        self.client.force_authenticate(user=admission.candidate.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        status_codes = [e["status_code"] for e in json_response['errors']]
        self.assertNotIn(AffiliationsNonCompleteesException.status_code, status_codes)
        self.assertNotIn(CarteBancaireRemboursementIbanNonCompleteException.status_code, status_codes)

        admission.accounting.account_number_type = ChoixTypeCompteBancaire.IBAN.name
        admission.accounting.iban_account_number = ''
        admission.accounting.solidarity_student = None
        admission.accounting.save()

        self.client.force_authenticate(user=admission.candidate.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        status_codes = [e["status_code"] for e in json_response['errors']]
        self.assertIn(AffiliationsNonCompleteesException.status_code, status_codes)
        self.assertIn(CarteBancaireRemboursementIbanNonCompleteException.status_code, status_codes)
