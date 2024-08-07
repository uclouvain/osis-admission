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
import attr
from django.test import SimpleTestCase

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import ModifierMembreSupervisionExterneCommand
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    MembreNonExterneException,
    ProcedureDemandeSignatureLanceeException,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class ModifierMembreExterneTestCase(SimpleTestCase):
    def setUp(self) -> None:
        self.matricule_membre_externe = 'promoteur-SC3DP-externe'
        self.uuid_proposition = 'uuid-SC3DP-promoteur-membre-cotutelle'

        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.proposition_id = PropositionIdentityBuilder.build_from_uuid(self.uuid_proposition)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = ModifierMembreSupervisionExterneCommand(
            uuid_proposition=self.uuid_proposition,
            uuid_membre=self.matricule_membre_externe,
            prenom="John",
            nom="Doe",
            email="john@example.org",
            est_docteur=False,
            institution="Psy",
            ville="Labah",
            pays="FR",
            langue="fr-be",
        )

        self.addCleanup(self.groupe_de_supervision_repository.reset)

    def test_should_modifier_membre_externe(self):
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(self.proposition_id)
        membres = self.groupe_de_supervision_repository.get_members(groupe.entity_id)
        self.assertEqual(len(membres), 4)
        index = next(i for i, m in enumerate(membres) if m.uuid == 'promoteur-SC3DP-externe')
        self.assertTrue(membres[index].est_externe)

        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        membres = self.groupe_de_supervision_repository.get_members(groupe.entity_id)
        self.assertEqual(len(membres), 4)
        index = next(i for i, m in enumerate(membres) if m.uuid == 'promoteur-SC3DP-externe')
        self.assertEqual(membres[index].prenom, "John")

    def test_should_empecher_si_signatures_lancees(self):
        cmd = attr.evolve(
            self.cmd,
            uuid_proposition='uuid-SC3DP-promoteurs-membres-deja-approuves',
            uuid_membre='membre-ca-SC3DP',
        )
        with self.assertRaises(ProcedureDemandeSignatureLanceeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_membre_non_externe(self):
        cmd = attr.evolve(self.cmd, uuid_membre='promoteur-SC3DP')
        with self.assertRaises(MembreNonExterneException):
            self.message_bus.invoke(cmd)
