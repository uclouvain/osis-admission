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
from unittest.mock import MagicMock

from django.test import TestCase

from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import (
    DemandePourCetteFormationDejaEnvoyeeException,
)
from admission.infrastructure.admission.shared_kernel.domain.service.maximum_propositions import (
    MaximumPropositionsAutorisees,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.tests.factories.academic_year import AcademicYearFactory


class MaxAuthorizedApplicationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.academic_years = {year: AcademicYearFactory(year=year) for year in [2023, 2024, 2025]}
        cls.admission = GeneralEducationAdmissionFactory(
            training__academic_year=cls.academic_years[2024],
            training__acronym='ABCD1',
            determined_academic_year=cls.academic_years[2024],
            status=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
        )
        cls.mock_admission = MagicMock(
            matricule_candidat=cls.admission.candidate.global_id,
            entity_id=MagicMock(uuid=str(cls.admission.uuid)),
            annee_calculee=2024,
            formation_id=MagicMock(
                annee=2024,
                sigle='ABCD1',
            ),
        )

    def test_with_no_other_admission(self):
        try:
            MaximumPropositionsAutorisees.verifier_une_seule_demande_envoyee_par_formation_generale_par_annee(
                proposition_candidat=self.mock_admission,
                annee_soumise=None,
            )
        except DemandePourCetteFormationDejaEnvoyeeException:
            self.fail('No exception must be raise.')

    def test_with_an_admission_for_another_training(self):
        other_admission = GeneralEducationAdmissionFactory(
            candidate=self.admission.candidate,
            training__acronym='ABCD2',
            training__academic_year=self.admission.training.academic_year,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Other training => no exception
        try:
            MaximumPropositionsAutorisees.verifier_une_seule_demande_envoyee_par_formation_generale_par_annee(
                proposition_candidat=self.mock_admission,
                annee_soumise=None,
            )
        except DemandePourCetteFormationDejaEnvoyeeException:
            self.fail('No exception must be raise.')

        # Same training => Exception
        other_admission.training = self.admission.training
        other_admission.save()

        with self.assertRaises(DemandePourCetteFormationDejaEnvoyeeException):
            MaximumPropositionsAutorisees.verifier_une_seule_demande_envoyee_par_formation_generale_par_annee(
                proposition_candidat=self.mock_admission,
                annee_soumise=None,
            )

    def test_depends_on_admission_status(self):
        other_admission = GeneralEducationAdmissionFactory(
            candidate=self.admission.candidate,
            training=self.admission.training,
        )

        valid_statuses = [
            ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            ChoixStatutPropositionGenerale.ANNULEE.name,
            ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        ]

        # Not submitted status => no exception
        for status in valid_statuses:
            other_admission.status = status
            other_admission.save()
            try:
                MaximumPropositionsAutorisees.verifier_une_seule_demande_envoyee_par_formation_generale_par_annee(
                    proposition_candidat=self.mock_admission,
                    annee_soumise=None,
                )
            except DemandePourCetteFormationDejaEnvoyeeException:
                self.fail('No exception must be raise.')

        # Submitted status => Exception
        for status in ChoixStatutPropositionGenerale.get_names_except(*valid_statuses):
            other_admission.status = status
            other_admission.save()

            with self.assertRaises(DemandePourCetteFormationDejaEnvoyeeException):
                MaximumPropositionsAutorisees.verifier_une_seule_demande_envoyee_par_formation_generale_par_annee(
                    proposition_candidat=self.mock_admission,
                    annee_soumise=None,
                )

    def test_with_an_admission_for_the_same_training_but_for_another_candidate(self):
        other_admission = GeneralEducationAdmissionFactory(
            training=self.admission.training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Other candidate => no exception
        try:
            MaximumPropositionsAutorisees.verifier_une_seule_demande_envoyee_par_formation_generale_par_annee(
                proposition_candidat=self.mock_admission,
                annee_soumise=None,
            )
        except DemandePourCetteFormationDejaEnvoyeeException:
            self.fail('No exception must be raise.')

        # Same candidate => Exception
        other_admission.candidate = self.admission.candidate
        other_admission.save()

        with self.assertRaises(DemandePourCetteFormationDejaEnvoyeeException):
            MaximumPropositionsAutorisees.verifier_une_seule_demande_envoyee_par_formation_generale_par_annee(
                proposition_candidat=self.mock_admission,
                annee_soumise=None,
            )

    def test_depends_on_related_year(self):
        GeneralEducationAdmissionFactory(
            candidate=self.admission.candidate,
            training=self.admission.training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        mock_admission = MagicMock(
            matricule_candidat=self.admission.candidate.global_id,
            entity_id=MagicMock(uuid=str(self.admission.uuid)),
            annee_calculee=2023,
            formation_id=MagicMock(
                annee=2024,
                sigle='ABCD1',
            ),
        )

        # Use the determined year if any
        try:
            MaximumPropositionsAutorisees.verifier_une_seule_demande_envoyee_par_formation_generale_par_annee(
                proposition_candidat=mock_admission,
                annee_soumise=None,
            )
        except DemandePourCetteFormationDejaEnvoyeeException:
            self.fail('No exception must be raise.')

        # No determined year => use the training year
        mock_admission.annee_calculee = None

        with self.assertRaises(DemandePourCetteFormationDejaEnvoyeeException):
            MaximumPropositionsAutorisees.verifier_une_seule_demande_envoyee_par_formation_generale_par_annee(
                proposition_candidat=mock_admission,
                annee_soumise=None,
            )

        # Use the submitted year if any
        try:
            MaximumPropositionsAutorisees.verifier_une_seule_demande_envoyee_par_formation_generale_par_annee(
                proposition_candidat=mock_admission,
                annee_soumise=2023,
            )
        except DemandePourCetteFormationDejaEnvoyeeException:
            self.fail('No exception must be raise.')
