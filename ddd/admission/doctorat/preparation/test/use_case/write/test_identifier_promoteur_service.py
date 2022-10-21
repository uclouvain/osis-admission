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
from unittest import TestCase

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import IdentifierMembreCACommand, IdentifierPromoteurCommand
from admission.ddd.admission.doctorat.preparation.domain.model._signature_promoteur import (
    SignaturePromoteur,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixEtatSignature
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    DejaMembreCAException,
    DejaPromoteurException,
    GroupeDeSupervisionNonTrouveException,
    GroupeSupervisionCompletPourPromoteursException,
    PromoteurNonTrouveException,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestIdentifierPromoteurService(TestCase):
    def setUp(self) -> None:
        self.matricule_promoteur = '00987890'
        self.uuid_proposition = 'uuid-SC3DP'

        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.proposition_id = PropositionIdentityBuilder.build_from_uuid(self.uuid_proposition)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = IdentifierPromoteurCommand(
            uuid_proposition=self.uuid_proposition,
            matricule=self.matricule_promoteur,
        )
        self.addCleanup(self.groupe_de_supervision_repository.reset)

    def test_should_ajouter_promoteur_dans_groupe_supervision(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        groupe = self.groupe_de_supervision_repository.get_by_proposition_id(proposition_id)
        signatures = groupe.signatures_promoteurs  # type:List[SignaturePromoteur]
        self.assertEqual(signatures[0].promoteur_id.matricule, self.matricule_promoteur)
        self.assertEqual(signatures[0].etat, ChoixEtatSignature.NOT_INVITED)

    def test_should_pas_ajouter_personne_si_pas_promoteur(self):
        cmd = attr.evolve(self.cmd, matricule='paspromoteur')
        with self.assertRaises(PromoteurNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_ajouter_personne_si_deja_promoteur(self):
        self.message_bus.invoke(self.cmd)
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), DejaPromoteurException)

    def test_should_pas_ajouter_personne_si_deja_membre_CA(self):
        self.message_bus.invoke(
            IdentifierMembreCACommand(
                uuid_proposition=self.uuid_proposition,
                matricule=self.matricule_promoteur,
            )
        )
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), DejaMembreCAException)

    def test_should_pas_ajouter_si_groupe_proposition_non_trouve(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='propositioninconnue')
        with self.assertRaises(GroupeDeSupervisionNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_ajouter_personne_si_groupe_complet_pour_promoteurs(self):
        # Add 3 promoters -> valid
        for k in range(1, 4):
            self.message_bus.invoke(
                IdentifierPromoteurCommand(
                    uuid_proposition=self.uuid_proposition,
                    matricule='0098789{}'.format(k),
                )
            )
        # Add a 4th promoter -> invalid
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), GroupeSupervisionCompletPourPromoteursException)
