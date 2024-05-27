# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import SimpleTestCase

from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_continue.commands import RecupererFormationContinueQuery
from admission.ddd.admission.formation_continue.domain.validator.exceptions import FormationNonTrouveeException
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRecupererFormationService(SimpleTestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def test_should_recuperer_formation_selon_sigle_et_annee(self):
        result: FormationDTO = self.message_bus.invoke(RecupererFormationContinueQuery(sigle='USCC1', annee=2020))
        self.assertEqual(result.sigle, 'USCC1')
        self.assertEqual(result.annee, 2020)

    def test_should_lever_exception_si_formation_non_trouvee(self):
        with self.assertRaises(FormationNonTrouveeException):
            self.message_bus.invoke(RecupererFormationContinueQuery(sigle='INCONNUE', annee=2020))
