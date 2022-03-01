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

from admission.ddd.preparation.projet_doctoral.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.preparation.projet_doctoral.commands import (
    ApprouverPropositionCommand,
    ApprouverPropositionParPdfCommand,
)
from admission.ddd.preparation.projet_doctoral.domain.model._signature_membre_CA import SignatureMembreCA
from admission.ddd.preparation.projet_doctoral.domain.model._signature_promoteur import (
    ChoixEtatSignature,
    SignaturePromoteur,
)
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    GroupeDeSupervisionNonTrouveException,
    InstitutTheseObligatoireException,
    PropositionNonTrouveeException,
    SignataireNonTrouveException,
    SignatairePasInviteException,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.preparation.projet_doctoral.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.preparation.projet_doctoral.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestApprouverPropositionService(SimpleTestCase):
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
        self.cmd = ApprouverPropositionCommand(
            uuid_proposition=self.uuid_proposition,
            matricule=self.matricule_promoteur,
            commentaire_interne='Commentaire interne',
            commentaire_externe='Commentaire externe',
        )

    def test_should_approuver_promoteur(self):
        cmd = attr.evolve(self.cmd, institut_these="9f30aa8a-6a67-4424-b30a-1f4cd0868871")
        proposition_id = self.message_bus.invoke(cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        signatures = groupe.signatures_promoteurs  # type:List[SignaturePromoteur]
        self.assertEqual(len(signatures), 1)
        self.assertEqual(len(groupe.signatures_membres_CA), 2)
        self.assertEqual(signatures[0].promoteur_id.matricule, self.matricule_promoteur)
        self.assertEqual(signatures[0].etat, ChoixEtatSignature.APPROVED)
        self.assertEqual(signatures[0].commentaire_interne, 'Commentaire interne')
        self.assertEqual(signatures[0].commentaire_externe, 'Commentaire externe')
        self.assertEqual(signatures[0].motif_refus, '')

    def test_should_approuver_promoteur_par_pdf(self):
        cmd = ApprouverPropositionParPdfCommand(
            uuid_proposition=self.uuid_proposition,
            matricule=self.matricule_promoteur,
            pdf='some-uuid',
        )
        proposition_id = self.message_bus.invoke(cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        signatures = groupe.signatures_promoteurs  # type:List[SignaturePromoteur]
        self.assertEqual(len(signatures), 1)
        self.assertEqual(len(groupe.signatures_membres_CA), 2)
        self.assertEqual(signatures[0].promoteur_id.matricule, self.matricule_promoteur)
        self.assertEqual(signatures[0].etat, ChoixEtatSignature.APPROVED)
        self.assertEqual(signatures[0].commentaire_interne, '')
        self.assertEqual(signatures[0].commentaire_externe, '')
        self.assertEqual(signatures[0].motif_refus, '')
        self.assertEqual(signatures[0].pdf, 'some-uuid')

    def test_should_approuver_membre_ca(self):
        cmd = attr.evolve(self.cmd, matricule=self.matricule_membre)
        proposition_id = self.message_bus.invoke(cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        signatures = groupe.signatures_membres_CA  # type:List[SignatureMembreCA]
        self.assertEqual(len(signatures), 2)
        self.assertEqual(signatures[-1].membre_CA_id.matricule, self.matricule_membre)
        self.assertEqual(signatures[-1].etat, ChoixEtatSignature.APPROVED)

    def test_should_approuver_membre_ca_par_pdf(self):
        cmd = ApprouverPropositionParPdfCommand(
            uuid_proposition=self.uuid_proposition,
            matricule=self.matricule_membre,
            pdf='some-uuid',
        )
        proposition_id = self.message_bus.invoke(cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        signatures = groupe.signatures_membres_CA  # type:List[SignatureMembreCA]
        self.assertEqual(len(signatures), 2)
        self.assertEqual(signatures[-1].membre_CA_id.matricule, self.matricule_membre)
        self.assertEqual(signatures[-1].etat, ChoixEtatSignature.APPROVED)
        self.assertEqual(signatures[-1].pdf, 'some-uuid')

    def test_should_pas_approuve_si_pas_dans_groupe(self):
        cmd = attr.evolve(self.cmd, matricule='paspromoteur')
        with self.assertRaises(SignataireNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_approuve_si_pas_invite(self):
        cmd = attr.evolve(self.cmd, uuid_proposition="uuid-SC3DP-sans-promoteur", matricule='membre-ca-SC3DP')
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), SignatairePasInviteException)

    def test_should_pas_approuver_si_groupe_proposition_non_trouve(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-ECGE3DP')
        with self.assertRaises(GroupeDeSupervisionNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_approuver_si_proposition_non_trouvee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='propositioninconnue')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_pas_approuver_si_premier_promoteur_et_institut_non_renseigne(self):
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), InstitutTheseObligatoireException)
