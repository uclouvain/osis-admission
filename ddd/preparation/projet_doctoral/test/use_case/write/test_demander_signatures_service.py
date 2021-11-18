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
from typing import List

import attr
from django.test import SimpleTestCase

from admission.ddd.preparation.projet_doctoral.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.preparation.projet_doctoral.commands import DemanderSignaturesCommand
from admission.ddd.preparation.projet_doctoral.domain.model._enums import ChoixStatusProposition
from admission.ddd.preparation.projet_doctoral.domain.model._signature_promoteur import (
    ChoixEtatSignature,
    SignaturePromoteur,
)
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import Proposition
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    DetailProjetNonCompleteException,
    GroupeDeSupervisionNonTrouveException,
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


class TestDemanderSignaturesService(SimpleTestCase):
    def setUp(self) -> None:
        self.matricule_promoteur = 'promoteur-SC3DP'
        self.uuid_proposition = 'uuid-SC3DP-promoteur-membre'
        self.uuid_proposition_sans_projet = 'uuid-SC3DP-no-project'
        uuid_proposition_admission = 'uuid-ECGE3DP'

        self.proposition_repository = PropositionInMemoryRepository()
        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        PropositionIdentityBuilder.build_from_uuid(self.uuid_proposition)
        PropositionIdentityBuilder.build_from_uuid(self.uuid_proposition_sans_projet)
        PropositionIdentityBuilder.build_from_uuid(uuid_proposition_admission)
        self.addCleanup(self.groupe_de_supervision_repository.reset)
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = DemanderSignaturesCommand(uuid_proposition=self.uuid_proposition)

    def test_should_demander_signatures(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        signatures = groupe.signatures_promoteurs  # type:List[SignaturePromoteur]
        proposition = self.proposition_repository.get(proposition_id)  # type:Proposition
        self.assertEqual(proposition.status, ChoixStatusProposition.SIGNING_IN_PROGRESS)
        self.assertTrue(proposition.est_verrouillee_pour_signature)
        self.assertEqual(len(signatures), 1)
        self.assertEqual(len(groupe.signatures_membres_CA), 1)
        self.assertEqual(signatures[0].promoteur_id.matricule, self.matricule_promoteur)
        self.assertEqual(signatures[0].etat, ChoixEtatSignature.INVITED)

    def test_should_pas_demander_si_detail_projet_pas_complete(self):
        cmd = attr.evolve(self.cmd, uuid_proposition=self.uuid_proposition_sans_projet)
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), DetailProjetNonCompleteException)

    def test_should_pas_demander_si_groupe_supervision_non_trouve(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-ECGE3DP')
        with self.assertRaises(GroupeDeSupervisionNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_demander_si_proposition_non_trouvee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='propositioninconnue')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)
