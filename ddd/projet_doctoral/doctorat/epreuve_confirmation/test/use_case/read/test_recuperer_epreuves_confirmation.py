# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import SimpleTestCase

from admission.ddd.projet_doctoral.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import RecupererEpreuvesConfirmationQuery
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRecupererEpreuvesConfirmation(SimpleTestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def test_should_pas_trouver_si_doctorat_inconnu(self):
        with self.assertRaises(DoctoratNonTrouveException):
            self.message_bus.invoke(
                RecupererEpreuvesConfirmationQuery(
                    doctorat_uuid='inconnu',
                )
            )

    def test_should_retourner_liste_vide_si_doctorat_connu_sans_epreuve(self):
        epreuves_confirmation = self.message_bus.invoke(
            RecupererEpreuvesConfirmationQuery(
                doctorat_uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve',
            )
        )
        self.assertEqual(epreuves_confirmation, [])

    def test_should_retourner_epreuves_confirmation_si_doctorat_connu_avec_epreuves(self):
        epreuves_confirmation: List[EpreuveConfirmationDTO] = self.message_bus.invoke(
            RecupererEpreuvesConfirmationQuery(
                doctorat_uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves',
            )
        )
        self.assertEqual(len(epreuves_confirmation), 3)
        self.assertEqual(epreuves_confirmation[0].uuid, 'c2')
        self.assertEqual(epreuves_confirmation[1].uuid, 'c0')
        self.assertEqual(epreuves_confirmation[2].uuid, 'c1')
