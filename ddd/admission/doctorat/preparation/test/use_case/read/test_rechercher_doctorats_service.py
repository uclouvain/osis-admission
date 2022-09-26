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
import datetime

import mock
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import RechercherDoctoratQuery
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRechercherDoctoratService(TestCase):
    def setUp(self) -> None:
        self.cmd = RechercherDoctoratQuery(sigle_secteur_entite_gestion='SST')
        self.message_bus = message_bus_in_memory_instance

    @mock.patch('admission.infrastructure.admission.domain.service.in_memory.annee_inscription_formation.today')
    def test_should_rechercher_par_sigle_secteur_entite_gestion(self, mock_today):
        mock_today.return_value = datetime.date(2020, 11, 1)
        results = self.message_bus.invoke(self.cmd)
        self.assertEqual(results[0].sigle_entite_gestion, 'CDSC')
        self.assertEqual(results[0].annee, 2020)

        mock_today.return_value = datetime.date(2022, 11, 1)
        results = self.message_bus.invoke(self.cmd)
        self.assertEqual(results[0].sigle_entite_gestion, 'CDSS')
        self.assertEqual(results[0].annee, 2022)
