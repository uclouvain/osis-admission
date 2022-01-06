# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
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

from admission.ddd.preparation.projet_doctoral.commands import VerifierPropositionCommand
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    CotutelleDoitAvoirAuMoinsUnPromoteurExterneException,
    CotutelleNonCompleteException,
    DetailProjetNonCompleteException,
    GroupeDeSupervisionNonTrouveException,
    MembreCAManquantException,
    PromoteurManquantException,
    PropositionNonTrouveeException,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.preparation.projet_doctoral.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.preparation.projet_doctoral.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestVerifierPropositionService(SimpleTestCase):
    def setUp(self) -> None:
        self.uuid_proposition = 'uuid-SC3DP-promoteur-membre-cotutelle'
        self.proposition_repository = PropositionInMemoryRepository()
        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.addCleanup(self.groupe_de_supervision_repository.reset)
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = VerifierPropositionCommand(uuid_proposition=self.uuid_proposition)

    def test_should_verifier_etre_ok(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)

    def test_should_retourner_erreur_si_detail_projet_pas_complete(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-no-project')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), DetailProjetNonCompleteException)

    def test_should_retourner_erreur_si_cotutelle_pas_complete(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-cotutelle-indefinie')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertTrue(any(isinstance(exc, CotutelleNonCompleteException) for exc in context.exception.exceptions))

    def test_should_retourner_erreur_si_groupe_supervision_non_trouve(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-ECGE3DP')
        with self.assertRaises(GroupeDeSupervisionNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_retourner_erreur_si_proposition_non_trouvee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='propositioninconnue')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_retourner_erreur_si_cotutelle_sans_promoteur_externe(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-cotutelle-sans-promoteur-externe')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), CotutelleDoitAvoirAuMoinsUnPromoteurExterneException)

    def test_should_verifier_etre_ok_si_cotutelle_avec_promoteur_externe(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-cotutelle-avec-promoteur-externe')
        proposition_id = self.message_bus.invoke(cmd)
        self.assertEqual(proposition_id.uuid, 'uuid-SC3DP-cotutelle-avec-promoteur-externe')

    def test_should_retourner_erreur_si_groupe_de_supervision_a_pas_promoteur(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-sans-promoteur')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), PromoteurManquantException)

    def test_should_retourner_erreur_si_groupe_de_supervision_a_pas_membre_CA(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-sans-membre_CA')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), MembreCAManquantException)
