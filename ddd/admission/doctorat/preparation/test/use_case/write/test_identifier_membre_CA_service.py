# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import List

import attr
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    IdentifierMembreCACommand,
    IdentifierPromoteurCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model._signature_membre_CA import (
    SignatureMembreCA,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixEtatSignature,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    DejaMembreException,
    GroupeDeSupervisionNonTrouveException,
    GroupeSupervisionCompletPourMembresCAException,
    MembreCANonTrouveException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.person import (
    PersonneConnueUclDTOFactory,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)


class TestIdentifierMembreCAService(TestCase):
    def setUp(self) -> None:
        self.matricule_membre_CA = '00987890'
        self.uuid_proposition = 'uuid-SC3DP'
        PersonneConnueUclInMemoryTranslator.personnes_connues_ucl.add(
            PersonneConnueUclDTOFactory(matricule="0123456"),
        )

        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.proposition_repository = PropositionInMemoryRepository()
        self.proposition_id = PropositionIdentityBuilder.build_from_uuid(self.uuid_proposition)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = IdentifierMembreCACommand(
            uuid_proposition=self.uuid_proposition,
            matricule_auteur="0123456",
            matricule=self.matricule_membre_CA,
            prenom="",
            nom="",
            email="",
            est_docteur=False,
            institution="",
            ville="",
            pays="",
            langue="",
        )
        self.addCleanup(self.groupe_de_supervision_repository.reset)
        self.addCleanup(self.proposition_repository.reset)

    def test_should_ajouter_membre_CA_dans_groupe_supervision(self):
        membre_CA_id = self.message_bus.invoke(self.cmd)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(self.proposition_id)
        signatures: List[SignatureMembreCA] = groupe.signatures_membres_CA
        self.assertEqual(len(signatures), 1)
        self.assertEqual(signatures[0].membre_CA_id, membre_CA_id)
        self.assertEqual(signatures[0].etat, ChoixEtatSignature.NOT_INVITED)

    def test_should_pas_ajouter_personne_si_pas_membre_CA(self):
        cmd = attr.evolve(self.cmd, matricule='pasmembre_CA')
        with self.assertRaises(MembreCANonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_ajouter_personne_si_deja_membre_CA(self):
        self.message_bus.invoke(self.cmd)
        with self.assertRaises(DejaMembreException):
            self.message_bus.invoke(self.cmd)

    def test_should_pas_ajouter_personne_si_deja_promoteur(self):
        self.message_bus.invoke(
            IdentifierPromoteurCommand(
                uuid_proposition=self.uuid_proposition,
                matricule=self.matricule_membre_CA,
                matricule_auteur="0123456",
                prenom="",
                nom="",
                email="",
                est_docteur=False,
                institution="",
                ville="",
                pays="",
                langue="",
            )
        )
        with self.assertRaises(DejaMembreException):
            self.message_bus.invoke(self.cmd)

    def test_should_pas_ajouter_si_groupe_proposition_non_trouve(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='propositioninconnue')
        with self.assertRaises(GroupeDeSupervisionNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_ajouter_personne_si_groupe_complet_pour_membres_ca(self):
        # Add 10 CA members -> valid
        for k in range(1, 11):
            self.message_bus.invoke(
                IdentifierMembreCACommand(
                    uuid_proposition=self.uuid_proposition,
                    matricule='',
                    matricule_auteur="0123456",
                    prenom=f"p{k}",
                    nom=f"n{k}",
                    email=f"{k}@test.be",
                    est_docteur=False,
                    institution="I1",
                    ville="V1",
                    pays="P1",
                    langue="L1",
                )
            )
        # Add a 11th member -> invalid
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), GroupeSupervisionCompletPourMembresCAException)
