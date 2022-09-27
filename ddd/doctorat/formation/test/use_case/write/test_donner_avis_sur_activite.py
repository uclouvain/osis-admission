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

from django.test import SimpleTestCase

from admission.ddd.doctorat.formation.commands import DonnerAvisSurActiviteCommand
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.doctorat.formation.repository.in_memory.activite import (
    ActiviteInMemoryRepository,
)


class DonnerAvisSurActiviteTestCase(SimpleTestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def test_donner_avis_sur_activite(self):
        activite_id = ActiviteInMemoryRepository.entities[0].entity_id
        self.message_bus.invoke(
            DonnerAvisSurActiviteCommand(
                doctorat_uuid="uuid-SC3DP-promoteurs-membres-deja-approuves",
                activite_uuid=activite_id.uuid,
                approbation=False,
                commentaire="Pas ok",
            )
        )
        self.assertEqual(ActiviteInMemoryRepository.get(activite_id).commentaire_promoteur_reference, "Pas ok")
