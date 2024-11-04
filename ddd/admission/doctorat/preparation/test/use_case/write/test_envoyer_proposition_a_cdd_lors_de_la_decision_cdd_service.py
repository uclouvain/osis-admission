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
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    EnvoyerPropositionACddLorsDeLaDecisionCddCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    SituationPropositionNonSICException,
)
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestEnvoyerPropositionACddLorsDeLaDecisionCddCommand(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = EnvoyerPropositionACddLorsDeLaDecisionCddCommand
        cls.parametres_commande_par_defaut = {
            'gestionnaire': '00321234',
            'uuid_proposition': 'uuid-SC3DP-promoteurs-membres-deja-approuves',
        }

    def setUp(self) -> None:
        self.proposition_repository.reset()
        self.proposition = self.proposition_repository.get(
            PropositionIdentity(uuid='uuid-SC3DP-promoteurs-membres-deja-approuves'),
        )

    def test_should_etre_ok_si_proposition_confirmee(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.CONFIRMEE
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat, self.proposition.entity_id)

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC)

    def test_should_etre_ok_si_proposition_completee_pour_sic(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        self.assertEqual(resultat, self.proposition.entity_id)

    def test_should_lever_exception_si_statut_non_conforme(self):
        statuts_invalides = ChoixStatutPropositionDoctorale.get_names_except(
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC,
            ChoixStatutPropositionDoctorale.CONFIRMEE,
            ChoixStatutPropositionDoctorale.RETOUR_DE_FAC,
        )

        for statut in statuts_invalides:
            self.proposition.statut = ChoixStatutPropositionDoctorale[statut]
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
                self.assertIsInstance(context.exception.exceptions.pop(), SituationPropositionNonSICException)
