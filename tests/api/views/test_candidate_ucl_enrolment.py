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

import freezegun
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from base.models.enums.academic_type import AcademicTypes
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_calendar import (
    BasculementDeliberationAcademicCalendarFactory,
    DiffusionDesNotesAcademicCalendarFactory,
    InscriptionEvaluationAcademicCalendarFactory,
)
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.tests.factories.student import StudentFactory
from ddd.logic.deliberation.propositions.domain.model._decision import Decision
from ddd.logic.inscription_aux_evaluations.shared_kernel.domain.model._type_inscription import TypeInscription
from deliberation.models.deliberation_actee import DeliberationActee
from deliberation.tests.factories.deliberation_actee import DeliberationActeeFactory
from epc.models.enums.decision_resultat_cycle import DecisionResultatCycle
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.enums.statut_inscription_programme_annuel import StatutInscriptionProgrammAnnuel
from epc.models.inscription_programme_annuel import InscriptionProgrammeAnnuel
from epc.tests.factories.inscription_programme_annuel import InscriptionProgrammeAnnuelFactory
from inscription_evaluation.models.formulaire_inscription import FormulaireInscription
from inscription_evaluation.tests.factories.formulaire_inscription import FormulaireInscriptionFactory


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
class CandidateDeliberationViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = resolve_url('admission_api_v1:candidate_deliberation')
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

    def _build_acted_deliberation(self, cycle_result='', annual_result='', year=2024) -> DeliberationActee:
        acted_deliberation = DeliberationActeeFactory(
            sigle_formation=self.enrolment.programme.offer.acronym,
            noma=self.student.registration_id,
            mention_de_cycle=cycle_result,
        )
        acted_deliberation.deliberations_programmes_annuels[0]['annee'] = year
        acted_deliberation.deliberations_programmes_annuels[0]['numero_session'] = 1
        acted_deliberation.deliberations_programmes_annuels[0]['decision'] = annual_result
        acted_deliberation.etats_cycles_annualises[0]['annee'] = year
        acted_deliberation.etats_cycles_annualises[0]['numero_session'] = 1
        acted_deliberation.save()

        return acted_deliberation

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)

        for method in ['delete', 'post', 'patch', 'put']:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def _test_is_deliberated(self, value: bool):
        response = self.client.get(self.url)
        deliberation = response.json()
        self.assertEqual(deliberation['est_delibere'], value)

    def test_candidate_deliberation_depends_on_enrolment_status(self):
        self.client.force_authenticate(user=self.candidate.user)

        desired_values = {
            StatutInscriptionProgrammAnnuel.ETUDIANT_UCL,
        }

        for current_value in StatutInscriptionProgrammAnnuel:
            self.enrolment.statut = current_value.name
            self.enrolment.save(update_fields=['statut'])
            self._test_is_deliberated(current_value not in desired_values)

    def test_candidate_deliberation_depends_on_enrolment_state(self):
        self.client.force_authenticate(user=self.candidate.user)

        desired_values = {
            EtatInscriptionFormation.INSCRIT_AU_ROLE,
            EtatInscriptionFormation.PROVISOIRE,
        }

        for current_value in EtatInscriptionFormation:
            self.enrolment.etat_inscription = current_value.name
            self.enrolment.save(update_fields=['etat_inscription'])
            self._test_is_deliberated(current_value not in desired_values)

    def test_candidate_deliberation_depends_on_academic_type(self):
        self.client.force_authenticate(user=self.candidate.user)

        desired_values = {
            AcademicTypes.ACADEMIC,
            AcademicTypes.NON_ACADEMIC_CREF,
        }

        offer = self.enrolment.programme.offer

        for current_value in AcademicTypes:
            offer.academic_type = current_value.name
            offer.save(update_fields=['academic_type'])
            self._test_is_deliberated(current_value not in desired_values)

    def test_candidate_deliberation_depends_on_training_type(self):
        self.client.force_authenticate(user=self.candidate.user)

        training_types = [
            TrainingType.PHD,
            TrainingType.FORMATION_PHD,
        ]

        for training_type in training_types:
            self.enrolment.programme.offer.education_group_type.name = training_type.name
            self.enrolment.programme.offer.education_group_type.save()
            self._test_is_deliberated(True)

    def test_candidate_deliberation_depends_on_cycle_mention(self):
        self.client.force_authenticate(user=self.candidate.user)

        acted_deliberation = self._build_acted_deliberation(cycle_result=DecisionResultatCycle.DISTINCTION.name)

        self._test_is_deliberated(True)

        acted_deliberation.mention_de_cycle = ''
        acted_deliberation.save()

        self._test_is_deliberated(False)

    def test_candidate_deliberation_depends_on_annual_result(self):
        self.client.force_authenticate(user=self.candidate.user)

        acted_deliberation = self._build_acted_deliberation(annual_result=Decision.REUSSITE.name)

        self._test_is_deliberated(True)

        acted_deliberation.deliberations_programmes_annuels[0]['decision'] = Decision.NON_REUSSITE.name
        acted_deliberation.save()

        self._test_is_deliberated(False)

    def test_candidate_deliberation_depends_on_last_exam_session_enrolment_date(self):
        self.client.force_authenticate(user=self.candidate.user)

        self._build_acted_deliberation()

        with freezegun.freeze_time('2025-07-15'):
            self._test_is_deliberated(False)

        with freezegun.freeze_time('2025-07-16'):
            self._test_is_deliberated(True)

    @freezegun.freeze_time('2025-07-16')
    def test_candidate_deliberation_depends_on_last_exam_session_enrolment(self):
        self.client.force_authenticate(user=self.candidate.user)

        # The student is not enrolled to the last exam session > deliberated
        # > (no form)
        acted_deliberation = self._build_acted_deliberation()

        self._test_is_deliberated(True)

        # > (a form but without enrolment)
        form = FormulaireInscriptionFactory(
            noma=self.student.registration_id,
            session=3,
            sigle_formation=self.enrolment.programme.offer.acronym,
            annee=2024,
        )

        self._test_is_deliberated(True)

        # The student is enrolled to the last exam session
        # > but the result is not announced (no result and no published mark)
        form.delete()
        forms = [
            FormulaireInscriptionFactory.avec_inscriptions(
                codes_ue={('LDROI1001', TypeInscription.PREMIERE_INSCRIPTION)},
                noma=self.student.registration_id,
                session=session,
                sigle_formation=self.enrolment.programme.offer.acronym,
                annee=2024,
            )
            for session in (1, 2, 3)
        ]

        for form in forms:
            form.formulaire['codes_ue_inscriptibles'] = {}

        FormulaireInscription.objects.bulk_update(objs=forms, fields=['formulaire'])

        self._test_is_deliberated(False)

        # > but the result is not announced (result but no published mark (no configured date))
        third_session_annual_result = acted_deliberation.deliberations_programmes_annuels[0].copy()
        third_session_annual_result['numero_session'] = 3
        third_session_annual_result['decision'] = Decision.NON_REUSSITE.name
        acted_deliberation.deliberations_programmes_annuels.append(third_session_annual_result)

        third_session_cycle_result = acted_deliberation.etats_cycles_annualises[0].copy()
        third_session_cycle_result['numero_session'] = 3
        acted_deliberation.etats_cycles_annualises.append(third_session_cycle_result)

        acted_deliberation.save()

        self._test_is_deliberated(False)

        # > but the result is not announced (result but no published mark (future date)
        last_session_diffusion_score_calendar = SessionExamCalendarFactory(
            number_session=3,
            academic_calendar=DiffusionDesNotesAcademicCalendarFactory(
                data_year__year=2024,
                start_date=datetime.date(2025, 7, 20),
                end_date=datetime.date(2025, 7, 31),
            ),
        )
        OfferYearCalendarFactory(
            academic_calendar=last_session_diffusion_score_calendar.academic_calendar,
            education_group_year=self.enrolment.programme.offer,
            start_date=last_session_diffusion_score_calendar.academic_calendar.start_date,
            end_date=last_session_diffusion_score_calendar.academic_calendar.end_date,
        )

        self._test_is_deliberated(False)

        # > but the result is announced (result and published mark (current date)
        with freezegun.freeze_time('2025-07-20'):
            self._test_is_deliberated(True)

        # > but the result is announced (result and published mark (past date)
        with freezegun.freeze_time('2025-07-21'):
            self._test_is_deliberated(True)

        # > but the result is not announced (no result but published mark)
        with freezegun.freeze_time('2025-07-20'):
            third_session_annual_result['decision'] = Decision.PAS_DE_DECISION.name
            acted_deliberation.save()

            self._test_is_deliberated(False)
