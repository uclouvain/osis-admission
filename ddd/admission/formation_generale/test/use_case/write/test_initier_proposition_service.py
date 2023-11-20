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
import uuid

import attr
from django.test import SimpleTestCase

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import MaximumPropositionsAtteintException
from admission.ddd.admission.domain.validator.exceptions import BourseNonTrouveeException
from admission.ddd.admission.enums.type_bourse import TypeBourse
from admission.ddd.admission.formation_generale.commands import InitierPropositionCommand
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.validator.exceptions import FormationNonTrouveeException
from admission.infrastructure.admission.domain.service.in_memory.bourse import BourseInMemoryTranslator
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestInitierPropositionService(SimpleTestCase):
    @classmethod
    def _get_une_bourse_par_type(cls, type_bourse: TypeBourse):
        return next(
            (bourse.entity_id.uuid for bourse in BourseInMemoryTranslator.ENTITIES if bourse.type == type_bourse),
            None,
        )

    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = InitierPropositionCommand(
            sigle_formation='MASTER-SCI',
            annee_formation=2020,
            matricule_candidat='01234567',
            bourse_erasmus_mundus=self._get_une_bourse_par_type(TypeBourse.ERASMUS_MUNDUS),
            bourse_internationale=self._get_une_bourse_par_type(TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE),
            bourse_double_diplome=self._get_une_bourse_par_type(TypeBourse.DOUBLE_TRIPLE_DIPLOMATION),
        )

    def test_should_initier(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.EN_BROUILLON)
        self.assertEqual(proposition.formation_id.sigle, self.cmd.sigle_formation)
        self.assertEqual(proposition.formation_id.annee, self.cmd.annee_formation)
        self.assertEqual(proposition.matricule_candidat, self.cmd.matricule_candidat)
        self.assertEqual(proposition.bourse_erasmus_mundus_id.uuid, self.cmd.bourse_erasmus_mundus)
        self.assertEqual(proposition.bourse_internationale_id.uuid, self.cmd.bourse_internationale)
        self.assertEqual(proposition.bourse_double_diplome_id.uuid, self.cmd.bourse_double_diplome)

    def test_should_empecher_si_pas_formation_generale(self):
        not_doctorat = 'DROI1BA'
        cmd = attr.evolve(self.cmd, sigle_formation=not_doctorat)
        with self.assertRaises(FormationNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_bourse_erasmus_invalide(self):
        cmd = attr.evolve(self.cmd, bourse_erasmus_mundus=str(uuid.uuid4()))
        with self.assertRaises(BourseNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_bourse_double_diplomation_invalide(self):
        cmd = attr.evolve(self.cmd, bourse_double_diplome=str(uuid.uuid4()))
        with self.assertRaises(BourseNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_bourse_internationale_invalide(self):
        cmd = attr.evolve(self.cmd, bourse_internationale=str(uuid.uuid4()))
        with self.assertRaises(BourseNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_trop_demandes_en_parallele(self):
        for proposition_index in range(5):
            self.message_bus.invoke(self.cmd)
        with self.assertRaises(MaximumPropositionsAtteintException):
            self.message_bus.invoke(self.cmd)
