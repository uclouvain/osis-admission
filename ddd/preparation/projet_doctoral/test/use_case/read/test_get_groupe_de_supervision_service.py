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

from django.test import TestCase

from admission.ddd.preparation.projet_doctoral.commands import GetGroupeDeSupervisionCommand
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import \
    PersonneConnueUclInMemoryTranslator


class GetGroupeDeSupervisionTestCase(TestCase):
    def setUp(self):
        self.cmd = GetGroupeDeSupervisionCommand(uuid_proposition='uuid-SC3DP-promoteur-membre')
        self.message_bus = message_bus_in_memory_instance
        PersonneConnueUclInMemoryTranslator.personnes_connues_ucl = [
            PersonneConnueUclDTO(
                matricule='promoteur-SC3DP',
                email='john.doe@email.com',
                prenom='John',
                nom='Doe',
                adresse_professionnelle=None,
            ),
            PersonneConnueUclDTO(
                matricule='membre-ca-SC3DP',
                email='janet.martin@email.com',
                prenom='Janet',
                nom='Martin',
                adresse_professionnelle=None,
            ),
        ]

    def test_get_groupe_de_supervision(self):
        results = self.message_bus.invoke(self.cmd)
        self.assertIsNotNone(results)
