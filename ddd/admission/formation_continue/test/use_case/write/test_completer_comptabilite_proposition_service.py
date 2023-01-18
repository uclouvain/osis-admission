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
from unittest import TestCase

from admission.ddd.admission.formation_continue.commands import CompleterComptabilitePropositionCommand
from admission.ddd.admission.enums import ChoixTypeCompteBancaire
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestCompleterComptabilitePropositionService(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance
        self.proposition_repository = PropositionInMemoryRepository()
        self.cmd = CompleterComptabilitePropositionCommand(
            uuid_proposition='uuid-USCC1',
            # Affiliations
            etudiant_solidaire=True,
            # Compte bancaire
            type_numero_compte=ChoixTypeCompteBancaire.IBAN.name,
            numero_compte_iban='BARC20658244971655GB87',
            iban_valide=True,
            numero_compte_autre_format='123456',
            code_bic_swift_banque='GEBABEBB',
            prenom_titulaire_compte='Jane',
            nom_titulaire_compte='Poe',
        )

    def test_should_completer(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.comptabilite.etudiant_solidaire, self.cmd.etudiant_solidaire)
        self.assertEqual(
            proposition.comptabilite.type_numero_compte,
            ChoixTypeCompteBancaire[self.cmd.type_numero_compte],
        )
        self.assertEqual(proposition.comptabilite.numero_compte_iban, self.cmd.numero_compte_iban)
        self.assertEqual(proposition.comptabilite.iban_valide, self.cmd.iban_valide)
        self.assertEqual(proposition.comptabilite.numero_compte_autre_format, self.cmd.numero_compte_autre_format)
        self.assertEqual(proposition.comptabilite.code_bic_swift_banque, self.cmd.code_bic_swift_banque)
        self.assertEqual(proposition.comptabilite.prenom_titulaire_compte, self.cmd.prenom_titulaire_compte)
        self.assertEqual(proposition.comptabilite.nom_titulaire_compte, self.cmd.nom_titulaire_compte)
