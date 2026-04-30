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
from unittest import mock

import freezegun
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.admission.shared_kernel.domain.model.enums.eligibilite_reinscription import EligibiliteReinscription
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.supervision import PromoterFactory
from base.models.enums.academic_type import AcademicTypes
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_calendar import (
    BasculementDeliberationAcademicCalendarFactory,
    InscriptionEvaluationAcademicCalendarFactory,
)
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.tests.factories.student import StudentFactory
from epc.models.enums.decision_resultat_cycle import DecisionResultatCycle
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.enums.statut_inscription_programme_annuel import StatutInscriptionProgrammAnnuel
from epc.models.inscription_programme_annuel import InscriptionProgrammeAnnuel
from epc.tests.factories.inscription_programme_annuel import InscriptionProgrammeAnnuelFactory


class CandidateUCLEnrolmentsViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = resolve_url('admission_api_v1:candidate_ucl_enrolments')

    def setUp(self):
        super().setUp()

        student = StudentFactory()

        self.candidate = student.person

        self.enrolment = InscriptionProgrammeAnnuelFactory(
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme_cycle__etudiant=student,
            programme_cycle__decision=DecisionResultatCycle.DISTINCTION.name,
            programme__root_group__acronym='MDS1',
            programme__root_group__academic_year__year=2020,
            programme__root_group__education_group_type__name=TrainingType.MASTER_M1.name,
            programme__root_group__main_teaching_campus__name='Mons',
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
            programme__offer__title='Titre 1',
            programme__offer__title_english='Title 1',
        )

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)

        for method in ['delete', 'post', 'patch', 'put']:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_with_no_enrolment(self):
        self.client.force_authenticate(user=self.candidate.user)

        self.enrolment.delete()

        response = self.client.get(self.url)

        enrolments = response.json()

        self.assertEqual(len(enrolments), 0)

    def test_with_one_enrolment(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url)

        enrolments = response.json()

        self.assertEqual(len(enrolments), 1)

        self.assertEqual(enrolments[0]['sigle_formation'], 'MDS1')
        self.assertEqual(enrolments[0]['intitule_formation_fr'], 'Titre 1')
        self.assertEqual(enrolments[0]['intitule_formation_en'], 'Title 1')
        self.assertEqual(enrolments[0]['type_formation'], TrainingType.MASTER_M1.name)
        self.assertEqual(enrolments[0]['lieu_enseignement'], 'Mons')
        self.assertEqual(enrolments[0]['annee'], 2020)
        self.assertEqual(enrolments[0]['est_diplome'], True)

    def test_with_specific_enrolment_status(self):
        self.client.force_authenticate(user=self.candidate.user)

        desired_values = {
            StatutInscriptionProgrammAnnuel.ETUDIANT_UCL,
        }

        for current_value in StatutInscriptionProgrammAnnuel:
            self.enrolment.statut = current_value.name
            self.enrolment.save(update_fields=['statut'])

            response = self.client.get(self.url)

            enrolments = response.json()

            self.assertEqual(len(enrolments), 1 if current_value in desired_values else 0)

    def test_with_specific_enrolment_state(self):
        self.client.force_authenticate(user=self.candidate.user)

        desired_values = {
            EtatInscriptionFormation.INSCRIT_AU_ROLE,
            EtatInscriptionFormation.PROVISOIRE,
            EtatInscriptionFormation.CESSATION,
        }

        for current_value in EtatInscriptionFormation:
            self.enrolment.etat_inscription = current_value.name
            self.enrolment.save(update_fields=['etat_inscription'])

            response = self.client.get(self.url)

            enrolments = response.json()

            self.assertEqual(len(enrolments), 1 if current_value in desired_values else 0)

    def test_with_specific_academic_type(self):
        self.client.force_authenticate(user=self.candidate.user)

        desired_values = {
            AcademicTypes.ACADEMIC,
            AcademicTypes.NON_ACADEMIC_CREF,
        }

        offer = self.enrolment.programme.offer

        for current_value in AcademicTypes:
            offer.academic_type = current_value.name
            offer.save(update_fields=['academic_type'])

            response = self.client.get(self.url)

            enrolments = response.json()

            self.assertEqual(len(enrolments), 1 if current_value in desired_values else 0)


class CandidateReEnrolmentPeriodViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = resolve_url('admission_api_v1:candidate_re_enrolment_period')
        cls.candidate = StudentFactory().person

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)

        for method in ['delete', 'post', 'patch', 'put']:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_re_enrolment_period(self):
        self.client.force_authenticate(user=self.candidate.user)

        with freezegun.freeze_time('2021-01-01'):
            AdmissionAcademicCalendarFactory.produce_all_required(quantity=6)

        deliberation_sessions = {
            (year, session): SessionExamCalendarFactory(
                number_session=session,
                academic_calendar=BasculementDeliberationAcademicCalendarFactory(
                    data_year__year=year,
                ),
            )
            for session in [1, 2, 3]
            for year in [2019, 2020, 2021, 2022]
        }

        with freezegun.freeze_time('2021-10-31'):
            response = self.client.get(self.url)

            self.assertEqual(response.status_code, 200)

            period = response.json()

            self.assertEqual(
                period['date_debut'],
                deliberation_sessions[(2020, 2)].academic_calendar.start_date.isoformat(),
            )
            self.assertEqual(period['date_fin'], datetime.date(2021, 10, 31).isoformat())
            self.assertEqual(period['annee_formation'], 2021)

        with freezegun.freeze_time('2021-11-01'):
            response = self.client.get(self.url)

            self.assertEqual(response.status_code, 200)

            period = response.json()

            self.assertEqual(
                period['date_debut'],
                deliberation_sessions[(2021, 2)].academic_calendar.start_date.isoformat(),
            )
            self.assertEqual(period['date_fin'], datetime.date(2022, 10, 31).isoformat())
            self.assertEqual(period['annee_formation'], 2022)


@freezegun.freeze_time('2025-01-01')
class CandidateReEnrolmentEligibilityViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = resolve_url('admission_api_v1:candidate_re_enrolment_eligibility')
        cls.student = StudentFactory()
        cls.candidate = cls.student.person
        AdmissionAcademicCalendarFactory.produce_all_required()
        cls.last_exam_enrolment_session_calendars = {
            year: SessionExamCalendarFactory(
                number_session=3,
                academic_calendar=InscriptionEvaluationAcademicCalendarFactory(
                    data_year__year=year,
                    start_date=datetime.date(year + 1, 6, 15),
                    end_date=datetime.date(year + 1, 7, 15),
                ),
            )
            for year in range(2024, 2026)
        }

    def setUp(self):
        super().setUp()

        self.enrolment: InscriptionProgrammeAnnuel = InscriptionProgrammeAnnuelFactory(
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme_cycle__etudiant=self.student,
            programme__root_group__acronym='MDS1',
            programme__root_group__academic_year__year=2024,
            programme__root_group__education_group_type__name=TrainingType.MASTER_M1.name,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
        )

        self.mock_finalized_deliberations_patcher = mock.patch(
            'admission.infrastructure.admission.handlers.DeliberationTranslator.recuperer_sessions_avec_deliberations_finalisees',
            return_value={},
        )
        self.mock_finalized_deliberations = self.mock_finalized_deliberations_patcher.start()
        self.addCleanup(self.mock_finalized_deliberations_patcher.stop)

        self.mock_potential_progression_session_3_patcher = mock.patch(
            'admission.infrastructure.admission.handlers.DeliberationTranslator.recuperer_progressions_potentielles_troisieme_session',
            return_value={},
        )
        self.mock_potential_progression_session_3 = self.mock_potential_progression_session_3_patcher.start()
        self.addCleanup(self.mock_potential_progression_session_3_patcher.stop)

        self.mock_authorization_patcher = mock.patch(
            'admission.infrastructure.admission.handlers.DiffusionNotesTranslator.recuperer_sessions_avec_autorisation_diffusion_resultats',
            return_value={},
        )
        self.mock_authorization = self.mock_authorization_patcher.start()
        self.addCleanup(self.mock_authorization_patcher.stop)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)

        for method in ['delete', 'post', 'patch', 'put']:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def _test_is_eligible(self, value: str, check_detail_message: str = ''):
        response = self.client.get(self.url)

        eligibility = response.json()

        self.assertEqual(eligibility['decision'], value)

        if check_detail_message:
            self.assertEqual(eligibility['raison_non_eligibilite'], check_detail_message)

    def test_candidate_eligibility_depends_on_enrolment_status(self):
        self.client.force_authenticate(user=self.candidate.user)

        desired_values = {
            StatutInscriptionProgrammAnnuel.ETUDIANT_UCL,
        }

        for current_value in StatutInscriptionProgrammAnnuel:
            self.enrolment.statut = current_value.name
            self.enrolment.save(update_fields=['statut'])
            self._test_is_eligible(
                EligibiliteReinscription.EST_ELIGIBLE.name
                if current_value not in desired_values
                else EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name,
            )

    def test_candidate_eligibility_depends_on_enrolment_state(self):
        self.client.force_authenticate(user=self.candidate.user)

        desired_values = {
            EtatInscriptionFormation.INSCRIT_AU_ROLE,
            EtatInscriptionFormation.PROVISOIRE,
        }

        for current_value in EtatInscriptionFormation:
            self.enrolment.etat_inscription = current_value.name
            self.enrolment.save(update_fields=['etat_inscription'])
            self._test_is_eligible(
                EligibiliteReinscription.EST_ELIGIBLE.name
                if current_value not in desired_values
                else EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name,
            )

    def test_candidate_eligibility_depends_on_academic_type(self):
        self.client.force_authenticate(user=self.candidate.user)

        desired_values = {
            AcademicTypes.ACADEMIC,
            AcademicTypes.NON_ACADEMIC_CREF,
        }

        offer = self.enrolment.programme.offer

        for current_value in AcademicTypes:
            offer.academic_type = current_value.name
            offer.save(update_fields=['academic_type'])
            self._test_is_eligible(
                EligibiliteReinscription.EST_ELIGIBLE.name
                if current_value not in desired_values
                else EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name,
            )

    def test_candidate_eligibility_depends_on_training_type(self):
        self.client.force_authenticate(user=self.candidate.user)

        training_types = [
            TrainingType.PHD,
            TrainingType.FORMATION_PHD,
        ]

        for training_type in training_types:
            self.enrolment.programme.offer.education_group_type.name = training_type.name
            self.enrolment.programme.offer.education_group_type.save()
            self._test_is_eligible(EligibiliteReinscription.EST_ELIGIBLE.name)

    def test_candidate_eligibility_depends_on_finalized_deliberations_with_published_results(self):
        self.client.force_authenticate(user=self.candidate.user)

        # No finalized deliberation and no authorization
        self.mock_finalized_deliberations.return_value = set()
        self.mock_authorization.return_value = set()
        self._test_is_eligible(EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name)

        # One finalized deliberation but no authorization
        self.mock_finalized_deliberations.return_value = {1}
        self.mock_authorization.return_value = set()
        self._test_is_eligible(EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_FIN_INSCRIPTION_EXAMENS_SESSION_3.name)

        # One finalized deliberation with authorization to another session
        self.mock_finalized_deliberations.return_value = {1}
        self.mock_authorization.return_value = {2}

        self._test_is_eligible(EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_FIN_INSCRIPTION_EXAMENS_SESSION_3.name)

        # One finalized deliberation with authorization
        self.mock_finalized_deliberations.return_value = {2}
        self.mock_authorization.return_value = {2}

        self._test_is_eligible(EligibiliteReinscription.EST_ELIGIBLE.name)

    @freezegun.freeze_time('2025-07-16')
    def test_candidate_eligibility_after_last_exam_session_enrolment_period(self):
        self.client.force_authenticate(user=self.candidate.user)

        # Potential progression in september -> no eligible
        self.mock_potential_progression_session_3.return_value = {3}
        self.mock_finalized_deliberations.return_value = set()
        self.mock_authorization.return_value = set()

        self._test_is_eligible(EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name)

        # No potential progression in september and:
        self.mock_potential_progression_session_3.return_value = set()

        # > no finalized deliberation and no authorization -> no eligible
        self.mock_finalized_deliberations.return_value = set()
        self.mock_authorization.return_value = set()

        self._test_is_eligible(EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name)

        # > the session 2 has finalized deliberation but no authorization -> no eligible
        self.mock_finalized_deliberations.return_value = {2}
        self.mock_authorization.return_value = set()

        self._test_is_eligible(EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name)

        self.mock_finalized_deliberations.return_value = {1, 2}
        self.mock_authorization.return_value = {1}

        self._test_is_eligible(EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name)

        # > the session 2 has finalized deliberation and authorization -> eligible
        self.mock_authorization.return_value = {2}
        self.mock_finalized_deliberations.return_value = {2}

        self._test_is_eligible(EligibiliteReinscription.EST_ELIGIBLE.name)

        self.mock_authorization.return_value = {1, 2}
        self.mock_finalized_deliberations.return_value = {1, 2}

        self._test_is_eligible(EligibiliteReinscription.EST_ELIGIBLE.name)

        # > the session 1 has finalized deliberation but no authorization -> no eligible
        self.mock_finalized_deliberations.return_value = {1}
        self.mock_authorization.return_value = set()

        self._test_is_eligible(EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name)

        # > the session 1 has finalized deliberation and authorization -> eligible
        self.mock_authorization.return_value = {1}
        self.mock_finalized_deliberations.return_value = {1}

        self._test_is_eligible(EligibiliteReinscription.EST_ELIGIBLE.name)

    @freezegun.freeze_time('2025-07-15')
    def test_candidate_eligibility_before_end_of_the_last_exam_session_enrolment_period(self):
        self.client.force_authenticate(user=self.candidate.user)

        # One finalized deliberation -> no eligible
        self.mock_finalized_deliberations.return_value = {3}

        self._test_is_eligible(
            value=EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_FIN_INSCRIPTION_EXAMENS_SESSION_3.name,
            check_detail_message="La réinscription sera accessible à partir du 16 juillet 2025.",
        )

        # No finalized deliberation -> no eligible
        self.mock_finalized_deliberations.return_value = set()

        self._test_is_eligible(
            value=EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name,
            check_detail_message="En attente de l'ensemble de vos résultats pour l'année académique 2024-2025.",
        )


@freezegun.freeze_time('2025-01-01')
class CandidateEnrolmentInformationViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = resolve_url('admission_api_v1:candidate_enrolment_information')
        cls.student = StudentFactory()
        cls.candidate = cls.student.person
        AdmissionAcademicCalendarFactory.produce_all_required()

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)

        for method in ['delete', 'post', 'patch', 'put']:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_with_a_recent_enrolment(self):
        self.client.force_authenticate(user=self.candidate.user)
        self.enrolment: InscriptionProgrammeAnnuel = InscriptionProgrammeAnnuelFactory(
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme_cycle__etudiant=self.student,
            programme__root_group__acronym='MDS1',
            programme__root_group__academic_year__year=2024,
            programme__root_group__education_group_type__name=TrainingType.MASTER_M1.name,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
        )

        response = self.client.get(self.url)

        enrolment_information = response.json()

        self.assertTrue(enrolment_information['est_inscrit_recemment'])

    def test_with_no_enrolment(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url)

        enrolment_information = response.json()

        self.assertFalse(enrolment_information['est_inscrit_recemment'])

    def test_with_endpoint_related_to_general_admission(self):
        admission = GeneralEducationAdmissionFactory()

        admission_url = resolve_url('admission_api_v1:general_candidate_enrolment_information', uuid=admission.uuid)

        self.client.force_authenticate(user=admission.candidate.user)

        response = self.client.get(admission_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrolment_information = response.json()
        self.assertFalse(enrolment_information['est_inscrit_recemment'])

    def test_with_endpoint_related_to_continuing_admission(self):
        admission = ContinuingEducationAdmissionFactory()

        admission_url = resolve_url('admission_api_v1:continuing_candidate_enrolment_information', uuid=admission.uuid)

        self.client.force_authenticate(user=admission.candidate.user)

        response = self.client.get(admission_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrolment_information = response.json()
        self.assertFalse(enrolment_information['est_inscrit_recemment'])

    def test_with_endpoint_related_to_doctorate_admission(self):
        promoter = PromoterFactory()

        admission = DoctorateAdmissionFactory(
            supervision_group=promoter.process,
        )

        admission_url = resolve_url('admission_api_v1:candidate_enrolment_information', uuid=admission.uuid)

        InscriptionProgrammeAnnuelFactory(
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme_cycle__etudiant__person=admission.candidate,
            programme__root_group__academic_year__year=2024,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
        )

        self.client.force_authenticate(user=admission.candidate.user)

        # The candidate retrieves its enrolment information
        response = self.client.get(admission_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrolment_information = response.json()
        self.assertTrue(enrolment_information['est_inscrit_recemment'])

        # The promoter retrieves the candidate enrolment information
        self.client.force_authenticate(user=promoter.person.user)

        response = self.client.get(admission_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrolment_information = response.json()
        self.assertTrue(enrolment_information['est_inscrit_recemment'])

        # The promoter retrieves its enrolment information
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrolment_information = response.json()
        self.assertFalse(enrolment_information['est_inscrit_recemment'])
