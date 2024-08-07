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
import uuid

from django.test import TestCase

from admission.ddd.admission.commands import RecupererExperienceNonAcademiqueQuery
from admission.ddd.admission.domain.validator.exceptions import ExperienceNonTrouveeException
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRecupererExperienceNonAcademique(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def test_should_recuperer_experience_non_academique(self):
        cmd = RecupererExperienceNonAcademiqueQuery(
            uuid_proposition='uuid-MASTER-SCI',
            global_id='0123456789',
            uuid_experience='1cbdf4db-2454-4cbf-9e48-55d2a9881ee1',
        )
        experience = self.message_bus.invoke(cmd)
        self.assertEqual(experience.uuid, cmd.uuid_experience)

    def test_should_lever_exception_si_experience_non_trouvee(self):
        cmd = RecupererExperienceNonAcademiqueQuery(
            uuid_proposition='uuid-MASTER-SCI',
            global_id='0123456789',
            uuid_experience=str(uuid.uuid4()),
        )
        with self.assertRaises(ExperienceNonTrouveeException):
            self.message_bus.invoke(cmd)
