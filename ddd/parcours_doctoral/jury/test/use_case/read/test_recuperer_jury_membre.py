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
from django.test import TestCase

from admission.ddd.parcours_doctoral.jury.commands import RecupererJuryMembreQuery
from admission.ddd.parcours_doctoral.jury.dtos.jury import MembreJuryDTO
from admission.ddd.parcours_doctoral.jury.validator.exceptions import (
    JuryNonTrouveException,
    MembreNonTrouveDansJuryException,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRecupererJuryMembre(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def test_should_pas_trouver_si_jury_inconnu(self):
        with self.assertRaises(JuryNonTrouveException):
            self.message_bus.invoke(
                RecupererJuryMembreQuery(
                    uuid_jury='inconnu',
                    uuid_membre='uuid-membre',
                )
            )

    def test_should_pas_trouver_si_jury_membre_inconnu(self):
        with self.assertRaises(MembreNonTrouveDansJuryException):
            self.message_bus.invoke(
                RecupererJuryMembreQuery(
                    uuid_jury='uuid-jury',
                    uuid_membre='inconnu',
                )
            )

    def test_should_recuperer_jury_membre_connu(self):
        membre_dto: MembreJuryDTO = self.message_bus.invoke(
            RecupererJuryMembreQuery(
                uuid_jury='uuid-jury',
                uuid_membre='uuid-membre',
            )
        )
        self.assertEqual(membre_dto.uuid, 'uuid-membre')
        self.assertEqual(membre_dto.role, 'MEMBRE')
        self.assertEqual(membre_dto.est_promoteur, False)
        self.assertEqual(membre_dto.matricule, None)
        self.assertEqual(membre_dto.institution, 'AUTRE')
        self.assertEqual(membre_dto.autre_institution, '')
        self.assertEqual(membre_dto.pays, 'pays')
        self.assertEqual(membre_dto.nom, 'nom')
        self.assertEqual(membre_dto.prenom, 'prenom')
        self.assertEqual(membre_dto.titre, 'DOCTEUR')
        self.assertEqual(membre_dto.justification_non_docteur, None)
        self.assertEqual(membre_dto.genre, 'AUTRE')
        self.assertEqual(membre_dto.email, 'email')
