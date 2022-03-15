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
from typing import List

import attr
from django.test import SimpleTestCase

from admission.ddd.projet_doctoral.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.projet_doctoral.preparation.commands import RefuserPropositionCommand
from admission.ddd.projet_doctoral.preparation.domain.model._signature_membre_CA import SignatureMembreCA
from admission.ddd.projet_doctoral.preparation.domain.model._signature_promoteur import (
    ChoixEtatSignature,
    SignaturePromoteur,
)
from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import (
    GroupeDeSupervisionNonTrouveException,
    PropositionNonTrouveeException,
    SignataireNonTrouveException,
    SignatairePasInviteException,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.projet_doctoral.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.projet_doctoral.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestRefuserPropositionService(SimpleTestCase):
    def setUp(self) -> None:
        self.matricule_promoteur = 'promoteur-SC3DP'
        self.matricule_membre = 'membre-ca-SC3DP-invite'
        self.uuid_proposition = 'uuid-SC3DP-membres-invites'

        self.proposition_repository = PropositionInMemoryRepository()
        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.proposition_id = PropositionIdentityBuilder.build_from_uuid(self.uuid_proposition)
        self.addCleanup(self.groupe_de_supervision_repository.reset)
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = RefuserPropositionCommand(
            uuid_proposition=self.uuid_proposition,
            matricule=self.matricule_promoteur,
            commentaire_interne='Commentaire interne',
            commentaire_externe='Commentaire externe',
            motif_refus="Motif de refus",
        )

    def test_should_refuser_promoteur(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        signatures = groupe.signatures_promoteurs  # type:List[SignaturePromoteur]
        self.assertEqual(len(signatures), 1)
        self.assertEqual(len(groupe.signatures_membres_CA), 2)
        self.assertEqual(signatures[0].promoteur_id.matricule, self.matricule_promoteur)
        self.assertEqual(signatures[0].etat, ChoixEtatSignature.DECLINED)
        self.assertEqual(signatures[0].commentaire_interne, 'Commentaire interne')
        self.assertEqual(signatures[0].commentaire_externe, 'Commentaire externe')
        self.assertEqual(signatures[0].motif_refus, 'Motif de refus')

    def test_should_refuser_membre_ca(self):
        cmd = attr.evolve(self.cmd, matricule=self.matricule_membre)
        proposition_id = self.message_bus.invoke(cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        signatures = groupe.signatures_membres_CA  # type:List[SignatureMembreCA]
        self.assertEqual(len(signatures), 2)
        self.assertEqual(signatures[-1].membre_CA_id.matricule, self.matricule_membre)
        self.assertEqual(signatures[-1].etat, ChoixEtatSignature.DECLINED)

    def test_should_pas_refuser_si_pas_dans_groupe(self):
        cmd = attr.evolve(self.cmd, matricule='paspromoteur')
        with self.assertRaises(SignataireNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_refuser_si_pas_invite(self):
        cmd = attr.evolve(self.cmd, uuid_proposition="uuid-SC3DP-sans-promoteur", matricule='membre-ca-SC3DP')
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), SignatairePasInviteException)

    def test_should_pas_refuser_si_groupe_proposition_non_trouve(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-ECGE3DP')
        with self.assertRaises(GroupeDeSupervisionNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_refuser_si_proposition_non_trouvee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='propositioninconnue')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_reinitialiser_autres_promoteurs(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-promoteur-deja-approuve')
        proposition_id = self.message_bus.invoke(cmd)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        signatures = groupe.signatures_promoteurs  # type:List[SignaturePromoteur]
        self.assertEqual(len(signatures), 2)
        self.assertEqual(len(groupe.signatures_membres_CA), 1)
        self.assertEqual(signatures[0].promoteur_id.matricule, self.matricule_promoteur)
        self.assertEqual(signatures[0].etat, ChoixEtatSignature.DECLINED)
        self.assertEqual(signatures[0].commentaire_interne, 'Commentaire interne')
        self.assertEqual(signatures[0].commentaire_externe, 'Commentaire externe')
        self.assertEqual(signatures[0].motif_refus, 'Motif de refus')
        self.assertEqual(signatures[1].etat, ChoixEtatSignature.NOT_INVITED)
