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

from admission.ddd.admission.formation_generale.commands import (
    SpecifierBesoinDeDerogationSicCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    BesoinDeDerogation,
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


class TestSpecifierBesoinDeDerogation(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = SpecifierBesoinDeDerogationSicCommand

    def setUp(self) -> None:
        self.proposition = PropositionFactory(
            entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-SCI-APPROVED'),
            matricule_candidat='0000000001',
            formation_id=FormationIdentityFactory(sigle="MASTER-SCI", annee=2021),
            curriculum=['file1.pdf'],
            est_confirmee=True,
            est_approuvee_par_sic=True,
            statut=ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION,
        )
        self.proposition_repository.save(self.proposition)
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-MASTER-SCI-APPROVED',
            'besoin_de_derogation': BesoinDeDerogation.AVIS_DIRECTION_DEMANDE.name,
        }

    def test_should_etre_ok_si_statut_correct(self):
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-MASTER-SCI-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.besoin_de_derogation, BesoinDeDerogation.AVIS_DIRECTION_DEMANDE.name)
