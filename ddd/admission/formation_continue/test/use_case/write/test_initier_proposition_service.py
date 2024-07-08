# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import attr
from django.test import SimpleTestCase

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import MaximumPropositionsAtteintException
from admission.ddd.admission.formation_continue.commands import InitierPropositionCommand
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    ChoixMoyensDecouverteFormation,
)
from admission.ddd.admission.formation_continue.domain.validator.exceptions import FormationNonTrouveeException
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestInitierPropositionService(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = InitierPropositionCommand(
            sigle_formation='USCC1',
            annee_formation=2020,
            matricule_candidat='01234567',
            motivations='Motivations',
            moyens_decouverte_formation=[
                ChoixMoyensDecouverteFormation.COURRIER_PERSONNALISE.name,
                ChoixMoyensDecouverteFormation.AUTRE.name,
            ],
            marque_d_interet=False,
            autre_moyen_decouverte_formation='Autre moyen',
        )

    def test_should_initier(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionContinue.EN_BROUILLON)
        self.assertEqual(proposition.formation_id.sigle, self.cmd.sigle_formation)
        self.assertEqual(proposition.formation_id.annee, self.cmd.annee_formation)
        self.assertEqual(proposition.matricule_candidat, self.cmd.matricule_candidat)
        self.assertEqual(proposition.motivations, self.cmd.motivations)
        self.assertEqual(
            proposition.moyens_decouverte_formation,
            [
                ChoixMoyensDecouverteFormation.COURRIER_PERSONNALISE,
                ChoixMoyensDecouverteFormation.AUTRE,
            ],
        )
        self.assertEqual(proposition.marque_d_interet, False)
        self.assertEqual(proposition.autre_moyen_decouverte_formation, 'Autre moyen')

    def test_should_empecher_si_pas_formation_continue(self):
        pas_formation_continue = 'DROI1BA'
        cmd = attr.evolve(self.cmd, sigle_formation=pas_formation_continue)
        with self.assertRaises(FormationNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_trop_demandes_en_parallele(self):
        for proposition_index in range(5):
            self.message_bus.invoke(self.cmd)
        with self.assertRaises(MaximumPropositionsAtteintException):
            self.message_bus.invoke(self.cmd)
