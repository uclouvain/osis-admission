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
from functools import partial
from unittest.mock import MagicMock

from django.test import TestCase

from admission.ddd.admission.formation_generale.domain.model.enums import PoursuiteDeCycle
from admission.ddd.admission.shared_kernel.domain.service.inscriptions_ucl_candidat import (
    InscriptionsUCLCandidatService,
)
from admission.infrastructure.admission.shared_kernel.domain.service.deliberation_translator import (
    DeliberationTranslator,
)
from admission.infrastructure.admission.shared_kernel.domain.service.noma_translator import NomasTranslator
from base.models.enums.academic_type import AcademicTypes
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from deliberation.tests.factories.deliberation_actee import DeliberationActeeFactory
from epc.models.enums.decision_resultat_cycle import DecisionResultatCycle
from epc.models.enums.etat_concours_attestation import EtatConcoursAttestation
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.enums.reussite_bloc1 import ReussiteBloc1
from epc.models.enums.statut_inscription_programme_annuel import StatutInscriptionProgrammAnnuel
from epc.tests.factories.inscription_programme_annuel import InscriptionProgrammeAnnuelFactory


class TestIsGraduated(TestCase):
    is_graduated = partial(
        InscriptionsUCLCandidatService.est_diplome,
        deliberation_translator=DeliberationTranslator(),
        nomas_translator=NomasTranslator(),
    )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.academic_years = {year: AcademicYearFactory(year=year) for year in [2023, 2024, 2025, 2026]}

    def setUp(self):
        super().setUp()

        self.enrolment = InscriptionProgrammeAnnuelFactory(
            programme_cycle__decision=DecisionResultatCycle.DISTINCTION.name,
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme__root_group__academic_year=self.academic_years[2023],
        )

        self.student = self.enrolment.programme_cycle.etudiant.person

        self.training = self.enrolment.programme.offer

    def test_return_true_is_the_person_is_graduated_of_the_training(self):
        result = self.is_graduated(matricule_candidat=self.student.global_id, sigle_formation=self.training.acronym)

        self.assertTrue(result)

        self.enrolment.programme_cycle.decision = DecisionResultatCycle.DIPLOMABLE.name
        self.enrolment.programme_cycle.save()

        result = self.is_graduated(matricule_candidat=self.student.global_id, sigle_formation=self.training.acronym)
        self.assertFalse(result)

    def test_depends_on_candidate(self):
        result = self.is_graduated(matricule_candidat='UNKNOWN', sigle_formation=self.training.acronym)

        self.assertFalse(result)

    def test_depends_on_training(self):
        result = self.is_graduated(matricule_candidat=self.student.global_id, sigle_formation='UNKNOWN')

        self.assertFalse(result)


class TestIsInBachelorCyclePursuit(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.deliberation_translator = DeliberationTranslator()

    def test_for_master(self):
        is_in_pursuit = InscriptionsUCLCandidatService.est_en_poursuite_cycle_bachelier(
            inscriptions_ucl_candidat=[],
            formation_id=MagicMock(sigle='ABC', annee=2020),
            type_formation=TrainingType.MASTER_M1,
            deliberation_translator=self.deliberation_translator,
        )

        self.assertEqual(is_in_pursuit, PoursuiteDeCycle.TO_BE_DETERMINED)

    def test_without_enrolment(self):
        is_in_pursuit = InscriptionsUCLCandidatService.est_en_poursuite_cycle_bachelier(
            inscriptions_ucl_candidat=[],
            formation_id=MagicMock(sigle='ABC', annee=2020),
            type_formation=TrainingType.BACHELOR,
            deliberation_translator=self.deliberation_translator,
        )

        self.assertEqual(is_in_pursuit, PoursuiteDeCycle.NO)

    def test_with_enrolments_and_for_another_training(self):
        is_in_pursuit = InscriptionsUCLCandidatService.est_en_poursuite_cycle_bachelier(
            inscriptions_ucl_candidat=[
                MagicMock(
                    sigle_formation='DEF',
                    annee=2019,
                    est_premiere_annee_bachelier=False,
                    noma='15150011',
                    etat_concours_attestation=EtatConcoursAttestation.NON_CONCERNE.name,
                )
            ],
            formation_id=MagicMock(sigle='ABC', annee=2020),
            type_formation=TrainingType.BACHELOR,
            deliberation_translator=self.deliberation_translator,
        )

        self.assertEqual(is_in_pursuit, PoursuiteDeCycle.NO)

    def test_with_enrolments_for_the_current_year(self):
        is_in_pursuit = InscriptionsUCLCandidatService.est_en_poursuite_cycle_bachelier(
            inscriptions_ucl_candidat=[
                MagicMock(
                    sigle_formation='ABC',
                    annee=2020,
                    est_premiere_annee_bachelier=False,
                    noma='15150011',
                    etat_concours_attestation=EtatConcoursAttestation.NON_CONCERNE.name,
                )
            ],
            formation_id=MagicMock(sigle='ABC', annee=2020),
            type_formation=TrainingType.BACHELOR,
            deliberation_translator=self.deliberation_translator,
        )

        self.assertEqual(is_in_pursuit, PoursuiteDeCycle.NO)

    def test_with_enrolments_for_the_future_year(self):
        is_in_pursuit = InscriptionsUCLCandidatService.est_en_poursuite_cycle_bachelier(
            inscriptions_ucl_candidat=[
                MagicMock(
                    sigle_formation='ABC',
                    annee=2021,
                    est_premiere_annee_bachelier=False,
                    noma='15150011',
                    etat_concours_attestation=EtatConcoursAttestation.NON_CONCERNE.name,
                )
            ],
            formation_id=MagicMock(sigle='ABC', annee=2020),
            type_formation=TrainingType.BACHELOR,
            deliberation_translator=self.deliberation_translator,
        )

        self.assertEqual(is_in_pursuit, PoursuiteDeCycle.NO)

    def test_with_enrolments_for_the_past_year_with_pursuit(self):
        is_in_pursuit = InscriptionsUCLCandidatService.est_en_poursuite_cycle_bachelier(
            inscriptions_ucl_candidat=[
                MagicMock(
                    sigle_formation='DEF',
                    annee=2019,
                    est_premiere_annee_bachelier=False,
                    noma='15150011',
                    etat_concours_attestation=EtatConcoursAttestation.NON_CONCERNE.name,
                ),
                MagicMock(
                    sigle_formation='ABC',
                    annee=2018,
                    est_premiere_annee_bachelier=True,
                    noma='15150011',
                    etat_concours_attestation=EtatConcoursAttestation.NON_CONCERNE.name,
                ),
                MagicMock(
                    sigle_formation='ABC',
                    annee=2019,
                    est_premiere_annee_bachelier=False,
                    noma='15150011',
                    etat_concours_attestation=EtatConcoursAttestation.NON_CONCERNE.name,
                ),
            ],
            formation_id=MagicMock(sigle='ABC', annee=2020),
            type_formation=TrainingType.BACHELOR,
            deliberation_translator=self.deliberation_translator,
        )

        self.assertEqual(is_in_pursuit, PoursuiteDeCycle.YES)

    def test_with_enrolments_for_the_past_year_without_pursuit_and_without_successful_block_1(self):
        is_in_pursuit = InscriptionsUCLCandidatService.est_en_poursuite_cycle_bachelier(
            inscriptions_ucl_candidat=[
                MagicMock(
                    sigle_formation='ABC',
                    annee=2019,
                    est_premiere_annee_bachelier=True,
                    noma='15150011',
                    etat_concours_attestation=EtatConcoursAttestation.NON_CONCERNE.name,
                ),
            ],
            formation_id=MagicMock(sigle='ABC', annee=2020),
            type_formation=TrainingType.BACHELOR,
            deliberation_translator=self.deliberation_translator,
        )

        self.assertEqual(is_in_pursuit, PoursuiteDeCycle.NO)

    def test_with_enrolments_for_the_past_year_without_pursuit_and_with_successful_block_1(self):
        deliberation = DeliberationActeeFactory(
            sigle_formation='ABC',
            noma='15150011',
        )

        deliberation.etats_cycles_annualises[0]['reussite_bloc1'] = ReussiteBloc1.REUSSITE_BLOC1.name
        deliberation.etats_cycles_annualises[0]['annee'] = 2019
        deliberation.deliberations_programmes_annuels[0]['annee'] = 2019
        deliberation.save()

        is_in_pursuit = InscriptionsUCLCandidatService.est_en_poursuite_cycle_bachelier(
            inscriptions_ucl_candidat=[
                MagicMock(
                    sigle_formation='ABC',
                    annee=2019,
                    est_premiere_annee_bachelier=True,
                    noma='15150011',
                    etat_concours_attestation=EtatConcoursAttestation.NON_CONCERNE.name,
                ),
            ],
            formation_id=MagicMock(sigle='ABC', annee=2020),
            type_formation=TrainingType.BACHELOR,
            deliberation_translator=self.deliberation_translator,
        )

        self.assertEqual(is_in_pursuit, PoursuiteDeCycle.YES)

    def test_with_enrolments_for_the_past_year_without_pursuit_and_with_successful_block_1_for_vete(self):
        deliberation = DeliberationActeeFactory(
            sigle_formation='VETE1BA',
            noma='15150011',
        )

        deliberation.etats_cycles_annualises[0]['reussite_bloc1'] = ReussiteBloc1.REUSSITE_BLOC1.name
        deliberation.etats_cycles_annualises[0]['annee'] = 2019
        deliberation.deliberations_programmes_annuels[0]['annee'] = 2019
        deliberation.save()

        is_in_pursuit = InscriptionsUCLCandidatService.est_en_poursuite_cycle_bachelier(
            inscriptions_ucl_candidat=[
                MagicMock(
                    sigle_formation='VETE1BA',
                    annee=2019,
                    est_premiere_annee_bachelier=True,
                    noma='15150011',
                    etat_concours_attestation=EtatConcoursAttestation.NON_ACCORDEE.name,
                ),
            ],
            formation_id=MagicMock(sigle='VETE1BA', annee=2020),
            type_formation=TrainingType.BACHELOR,
            deliberation_translator=self.deliberation_translator,
        )

        self.assertEqual(is_in_pursuit, PoursuiteDeCycle.NO)

        is_in_pursuit = InscriptionsUCLCandidatService.est_en_poursuite_cycle_bachelier(
            inscriptions_ucl_candidat=[
                MagicMock(
                    sigle_formation='VETE1BA',
                    annee=2019,
                    est_premiere_annee_bachelier=True,
                    noma='15150011',
                    etat_concours_attestation=EtatConcoursAttestation.ACCORDEE.name,
                ),
            ],
            formation_id=MagicMock(sigle='VETE1BA', annee=2020),
            type_formation=TrainingType.BACHELOR,
            deliberation_translator=self.deliberation_translator,
        )

        self.assertEqual(is_in_pursuit, PoursuiteDeCycle.YES)
