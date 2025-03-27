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
import datetime
from unittest import TestCase, mock

from admission.ddd.admission.dtos.periode import PeriodeDTO
from admission.ddd.admission.formation_generale.commands import (
    RecupererPeriodeInscriptionSpecifiqueBachelierMedecineDentisterieQuery,
)
from admission.infrastructure.admission.domain.service.in_memory.calendrier_inscription import (
    CalendrierInscriptionInMemory,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)


class RecupererPeriodeInscriptionSpecifiqueBachelierMedecineDentisterieTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.message_bus = message_bus_in_memory_instance
        cls.cmd = RecupererPeriodeInscriptionSpecifiqueBachelierMedecineDentisterieQuery()

    def test_sans_periode_inscription(self):
        periode = self.message_bus.invoke(self.cmd)
        self.assertIsNone(periode)

    def test_avec_periode_inscription(self):
        with mock.patch.object(
            CalendrierInscriptionInMemory,
            'recuperer_periode_inscription_specifique_medecine_dentisterie',
            return_value=PeriodeDTO(
                date_debut=datetime.date(2020, 9, 6),
                date_fin=datetime.date(2021, 2, 15),
            ),
        ):
            periode = self.message_bus.invoke(self.cmd)

            self.assertIsNotNone(periode)
            self.assertEqual(periode.date_debut, datetime.date(2020, 9, 6))
            self.assertEqual(periode.date_fin, datetime.date(2021, 2, 15))
