# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    SpecifierMotifsRefusPropositionParSicCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)


class TestSpecifierMotifsRefusPropositionParSic(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = SpecifierMotifsRefusPropositionParSicCommand

    def setUp(self) -> None:
        self.proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-SC3DP-confirmee'))
        self.proposition.statut = ChoixStatutPropositionDoctorale.RETOUR_DE_FAC

    def test_should_etre_ok_si_motif_connu_specifie(self):
        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition=self.proposition.entity_id.uuid,
                uuids_motifs=['uuid-nouveau-motif-refus'],
                autres_motifs=[],
                gestionnaire='0123456789',
            )
        )

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, self.proposition.entity_id.uuid)

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_EN_COURS)
        self.assertEqual(
            proposition.checklist_actuelle.decision_sic.extra,
            {'en_cours': 'refusal'},
        )
        self.assertEqual(proposition.motifs_refus, [MotifRefusIdentity(uuid='uuid-nouveau-motif-refus')])
        self.assertEqual(proposition.autres_motifs_refus, [])

    def test_should_etre_ok_si_motif_libre_specifie(self):
        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition=self.proposition.entity_id.uuid,
                uuids_motifs=[],
                autres_motifs=['Autre motif'],
                gestionnaire='0123456789',
            )
        )

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, self.proposition.entity_id.uuid)

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_EN_COURS)
        self.assertEqual(
            proposition.checklist_actuelle.decision_sic.extra,
            {'en_cours': 'refusal'},
        )
        self.assertEqual(proposition.motifs_refus, [])
        self.assertEqual(proposition.autres_motifs_refus, ['Autre motif'])
