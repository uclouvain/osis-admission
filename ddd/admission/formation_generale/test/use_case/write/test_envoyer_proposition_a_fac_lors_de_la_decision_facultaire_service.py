# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.domain.model.complement_formation import ComplementFormationIdentity
from admission.ddd.admission.domain.model.condition_complementaire_approbation import (
    ConditionComplementaireApprobationIdentity,
)
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.commands import (
    SpecifierInformationsAcceptationFacultairePropositionCommand,
    EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    SituationPropositionNonFACException,
    SituationPropositionNonSICException,
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


class TestEnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand
        cls.parametres_commande_par_defaut = {
            'gestionnaire': '00321234',
            'uuid_proposition': 'uuid-MASTER-SCI-CONFIRMED',
        }

    def setUp(self) -> None:
        self.proposition_repository.reset()
        self.proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-MASTER-SCI-CONFIRMED'))

    def test_should_etre_ok_si_proposition_confirmee(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.CONFIRMEE
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat, self.proposition.entity_id)

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.TRAITEMENT_FAC)

    def test_should_etre_ok_si_proposition_completee_pour_sic(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        self.assertEqual(resultat, self.proposition.entity_id)

    def test_should_lever_exception_si_statut_non_conforme(self):
        statuts_invalides = ChoixStatutPropositionGenerale.get_names_except(
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC,
            ChoixStatutPropositionGenerale.CONFIRMEE,
            ChoixStatutPropositionGenerale.RETOUR_DE_FAC,
        )

        for statut in statuts_invalides:
            self.proposition.statut = ChoixStatutPropositionGenerale[statut]
            with self.assertRaises(
                SituationPropositionNonSICException,
                msg=f'The following status must raise an exception: {statut}',
            ):
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
