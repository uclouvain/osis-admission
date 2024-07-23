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
from unittest import TestCase

import freezegun

from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity
from admission.ddd.admission.doctorat.preparation.commands import RetyperDocumentCommand
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class RetyperDocumentTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first_document_id = 'ID1-FD'
        cls.second_document_id = 'LIBRE_CANDIDAT.36de0c3d-3c06-4c93-8eb4-c8648f04f142'

    def setUp(self) -> None:
        self.emplacements_document_repository = emplacement_document_in_memory_repository
        self.addCleanup(self.emplacements_document_repository.reset)
        self.message_bus = message_bus_in_memory_instance

    @freezegun.freeze_time("2023-01-03")
    def test_should_retyper_document(self):
        self.message_bus.invoke(
            RetyperDocumentCommand(
                uuid_proposition='uuid-SC3DP-promoteur-membre',
                identifiant_source=self.first_document_id,
                identifiant_cible=self.second_document_id,
                auteur='0123456789',
            )
        )
        document_1 = self.emplacements_document_repository.get(
            EmplacementDocumentIdentity(
                identifiant=self.first_document_id,
                proposition_id=PropositionIdentity(uuid='uuid-SC3DP-promoteur-membre'),
            )
        )
        document_2 = self.emplacements_document_repository.get(
            EmplacementDocumentIdentity(
                identifiant=self.second_document_id,
                proposition_id=PropositionIdentity(uuid='uuid-SC3DP-promoteur-membre'),
            )
        )
        self.assertEqual(document_1.justification_gestionnaire, 'Ma raison 2')
        self.assertEqual(document_2.justification_gestionnaire, 'Ma raison 1')
