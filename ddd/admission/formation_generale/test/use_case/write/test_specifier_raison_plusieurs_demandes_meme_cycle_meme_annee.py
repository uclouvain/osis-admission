# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import SimpleTestCase

from admission.ddd.admission.formation_generale.commands import (
    SpecifierRaisonPlusieursDemandesMemeCycleMemeAnneeCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    RaisonPlusieursDemandesMemesCycleEtAnnee,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)


class TesSpecifierRaisonPlusieursDemandesMemeCycleMemeAnneeService(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance

    def test_specifier_raison(self):
        proposition_id = self.message_bus.invoke(
            SpecifierRaisonPlusieursDemandesMemeCycleMemeAnneeCommand(
                uuid_proposition="uuid-MASTER-SCI",
                raison_plusieurs_demandes_meme_cycle_meme_annee=(
                    RaisonPlusieursDemandesMemesCycleEtAnnee.SUIVRE_EN_PARALLELE.name
                ),
                justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee='1',
            )
        )
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(
            proposition.raison_plusieurs_demandes_meme_cycle_meme_annee,
            RaisonPlusieursDemandesMemesCycleEtAnnee.SUIVRE_EN_PARALLELE,
        )
        self.assertEqual(proposition.justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee, '1')

    def test_specifier_raison_vide(self):
        proposition_id = self.message_bus.invoke(
            SpecifierRaisonPlusieursDemandesMemeCycleMemeAnneeCommand(
                uuid_proposition="uuid-MASTER-SCI",
                raison_plusieurs_demandes_meme_cycle_meme_annee='',
                justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee='',
            )
        )
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(proposition.raison_plusieurs_demandes_meme_cycle_meme_annee, None)
        self.assertEqual(proposition.justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee, '')
