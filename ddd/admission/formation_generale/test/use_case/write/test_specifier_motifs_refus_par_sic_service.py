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
from unittest import TestCase

import factory

from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.ddd.admission.formation_generale.commands import (
    SpecifierMotifsRefusPropositionParSicCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
    DecisionFacultaireEnum,
)
from admission.ddd.admission.formation_generale.test.factory.proposition import (
    PropositionFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestSpecifierMotifsRefusPropositionParSic(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = SpecifierMotifsRefusPropositionParSicCommand

    def setUp(self) -> None:
        self.proposition = PropositionFactory(
            entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-SCI-APPROVED'),
            matricule_candidat='0000000001',
            formation_id=FormationIdentityFactory(sigle="MASTER-SCI", annee=2021),
            curriculum=['file1.pdf'],
            est_confirmee=True,
            statut=ChoixStatutPropositionGenerale.CONFIRMEE,
        )
        self.proposition_repository.save(self.proposition)

    def test_should_etre_ok_si_motif_connu_specifie(self):
        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition='uuid-MASTER-SCI-APPROVED',
                type_de_refus='REFUS_AGREGATION',
                uuids_motifs=['uuid-nouveau-motif-refus'],
                autres_motifs=[],
            )
        )

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-MASTER-SCI-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_EN_COURS)
        self.assertEqual(
            proposition.checklist_actuelle.decision_sic.extra,
            {'en_cours': 'refusal'},
        )
        self.assertEqual(proposition.motifs_refus, [MotifRefusIdentity(uuid='uuid-nouveau-motif-refus')])
        self.assertEqual(proposition.autres_motifs_refus, [])
        self.assertEqual(proposition.type_de_refus, 'REFUS_AGREGATION')

    def test_should_etre_ok_si_motif_libre_specifie(self):
        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition='uuid-MASTER-SCI-APPROVED',
                type_de_refus='REFUS_AGREGATION',
                uuids_motifs=[],
                autres_motifs=['Autre motif'],
            )
        )

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-MASTER-SCI-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_EN_COURS)
        self.assertEqual(
            proposition.checklist_actuelle.decision_sic.extra,
            {'en_cours': 'refusal'},
        )
        self.assertEqual(proposition.motifs_refus, [])
        self.assertEqual(proposition.autres_motifs_refus, ['Autre motif'])
        self.assertEqual(proposition.type_de_refus, 'REFUS_AGREGATION')
