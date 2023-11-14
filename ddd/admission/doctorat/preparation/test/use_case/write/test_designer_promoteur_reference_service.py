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
from unittest import TestCase

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import DesignerPromoteurReferenceCommand
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    PropositionNonTrouveeException,
    SignataireNonTrouveException,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestDesignerPromoteurDeReferenceService(TestCase):
    def setUp(self) -> None:
        self.uuid_promoteur = 'promoteur-SC3DP'
        self.uuid_proposition = 'uuid-SC3DP-sans-promoteur-reference'

        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.proposition_id = PropositionIdentityBuilder.build_from_uuid(self.uuid_proposition)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = DesignerPromoteurReferenceCommand(
            uuid_proposition=self.uuid_proposition,
            uuid_promoteur=self.uuid_promoteur,
        )
        self.addCleanup(self.groupe_de_supervision_repository.reset)

    def test_should_designer_promoteur_reference(self):
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(self.proposition_id)
        self.assertIsNone(groupe.promoteur_reference_id)

        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        self.assertEqual(groupe.promoteur_reference_id.uuid, self.uuid_promoteur)

    def test_should_changer_promoteur_reference(self):
        uuid_proposition = "uuid-SC3DP-promoteur-deja-approuve"
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(
            PropositionIdentityBuilder.build_from_uuid(uuid_proposition)
        )
        self.assertEqual(groupe.promoteur_reference_id.uuid, "promoteur-SC3DP")

        proposition_id = self.message_bus.invoke(
            DesignerPromoteurReferenceCommand(
                uuid_proposition=uuid_proposition,
                uuid_promoteur="promoteur-SC3DP-deja-approuve",
            )
        )
        self.assertEqual(proposition_id.uuid, uuid_proposition)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        self.assertEqual(groupe.promoteur_reference_id.uuid, "promoteur-SC3DP-deja-approuve")

    def test_should_pas_designer_personne_si_pas_promoteur(self):
        cmd = attr.evolve(self.cmd, uuid_promoteur='paspromoteur')
        with self.assertRaises(SignataireNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_designer_si_groupe_proposition_non_trouve(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='propositioninconnue')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)
