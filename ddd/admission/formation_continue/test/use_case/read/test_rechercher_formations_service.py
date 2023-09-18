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
import freezegun
from django.test import SimpleTestCase

from admission.ddd.admission.formation_continue.commands import RechercherFormationContinueQuery
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRechercherFormationService(SimpleTestCase):
    def setUp(self) -> None:
        self.cmd = RechercherFormationContinueQuery(
            terme_de_recherche='USCC1',
        )
        self.message_bus = message_bus_in_memory_instance

    def test_should_rechercher_par_intitule_formation(self):
        with freezegun.freeze_time('2020-11-01'):
            results = self.message_bus.invoke(self.cmd)
            self.assertEqual(results[0].sigle, 'USCC1')
            self.assertEqual(results[0].annee, 2020)

        with freezegun.freeze_time('2022-11-01'):
            results = self.message_bus.invoke(self.cmd)
            self.assertEqual(results[0].sigle, 'USCC1')
            self.assertEqual(results[0].annee, 2022)

    @freezegun.freeze_time('2022-11-01')
    def test_should_rechercher_par_intitule_formation_et_par_campus(self):
        # Tous les campus
        results = self.message_bus.invoke(RechercherFormationContinueQuery(terme_de_recherche='USCC'))
        self.assertEqual(len(results), 5)

        # Un campus
        results = self.message_bus.invoke(
            RechercherFormationContinueQuery(
                terme_de_recherche='USCC',
                campus='Mons',
            )
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].campus, 'Mons')
