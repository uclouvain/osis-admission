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
from django.test import SimpleTestCase

from admission.ddd.preparation.projet_doctoral.commands import SearchDoctoratCommand
from admission.ddd.preparation.projet_doctoral.domain.service.i_doctorat import IDoctoratTranslator
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRechercherDoctoratService(SimpleTestCase):
    def setUp(self) -> None:
        self._mock_message_bus()
        self.doctorat_translator = mock.Mock(spec=IDoctoratTranslator)
        self.cmd = SearchDoctoratCommand(
            sigle_secteur_entite_gestion='SST',
        )

    def _mock_message_bus(self):
        message_bus_patcher = mock.patch.multiple(
            'infrastructure.message_bus_in_memory',
            DoctoratInMemoryTranslator=lambda: self.doctorat_translator,
        )
        message_bus_patcher.start()
        self.addCleanup(message_bus_patcher.stop)
        self.message_bus = message_bus_in_memory_instance

    def test_should_appeler_doctorat_translator(self):
        self.message_bus.invoke(self.cmd)
        self.doctorat_translator.search.assert_called_with('SST', datetime.date.today().year)
