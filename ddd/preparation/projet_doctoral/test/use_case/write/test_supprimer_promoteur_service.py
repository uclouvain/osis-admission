# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.preparation.projet_doctoral.builder.proposition_identity_builder import \
    PropositionIdentityBuilder
from admission.ddd.preparation.projet_doctoral.commands import (
    SupprimerPromoteurCommand,
)
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    GroupeDeSupervisionNonTrouveException,
    PromoteurNonTrouveException,
    PropositionNonTrouveeException,
    SignataireNonTrouveException,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.preparation.projet_doctoral.repository.in_memory.groupe_de_supervision import \
    GroupeDeSupervisionInMemoryRepository
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestSupprimerPromoteurService(SimpleTestCase):
    def setUp(self) -> None:
        self.matricule_promoteur = 'promoteur-SC3DP'
        self.uuid_proposition = 'uuid-SC3DP-promoteur-membre'

        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.proposition_id = PropositionIdentityBuilder.build_from_uuid(self.uuid_proposition)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = SupprimerPromoteurCommand(
            uuid_proposition=self.uuid_proposition,
            matricule=self.matricule_promoteur,
        )
        self.addCleanup(self.groupe_de_supervision_repository.reset)

    def test_should_supprimer_promoteur_dans_groupe_supervision(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        self.assertEqual(len(groupe.signatures_promoteurs), 0)

    def test_should_pas_supprimer_personne_si_pas_promoteur(self):
        cmd = attr.evolve(self.cmd, matricule='paspromoteur')
        with self.assertRaises(SignataireNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_supprimer_membre_CA(self):
        cmd = attr.evolve(self.cmd, matricule='membre-ca-SC3DP')
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), PromoteurNonTrouveException)

    def test_should_pas_supprimer_si_groupe_proposition_non_trouve(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-ECGE3DP')
        with self.assertRaises(GroupeDeSupervisionNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_supprimer_si_proposition_non_trouvee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='propositioninconnue')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)
