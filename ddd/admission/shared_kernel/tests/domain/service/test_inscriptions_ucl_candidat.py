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

from django.test import TestCase

from admission.ddd.admission.shared_kernel.domain.service.inscriptions_ucl_candidat import (
    InscriptionsUCLCandidatService,
)
from admission.infrastructure.admission.shared_kernel.domain.service.deliberation_translator import (
    DeliberationTranslator,
)
from admission.infrastructure.admission.shared_kernel.domain.service.noma_translator import NomasTranslator
from base.models.enums.academic_type import AcademicTypes
from base.tests.factories.academic_year import AcademicYearFactory
from epc.models.enums.decision_resultat_cycle import DecisionResultatCycle
from epc.models.enums.etat_inscription import EtatInscriptionFormation
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
