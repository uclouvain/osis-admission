# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

import freezegun
from django.test import SimpleTestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    RecupererDocumentsPropositionQuery,
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity, EmplacementDocument
from admission.ddd.admission.domain.validator.exceptions import EmplacementDocumentNonTrouveException
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


@freezegun.freeze_time('2023-10-01')
class RecalculerEmplacementsDocumentsNonLibresPropositionTestCase(SimpleTestCase):
    def setUp(self):
        self.cmd = RecalculerEmplacementsDocumentsNonLibresPropositionCommand(
            uuid_proposition='uuid-SC3DP-promoteur-membre',
        )
        self.message_bus = message_bus_in_memory_instance

        self.academic_year_repository = AcademicYearInMemoryRepository()

        self.academic_year_repository.save(
            AcademicYear(
                entity_id=AcademicYearIdentity(year=2023),
                start_date=datetime.date(2023, 9, 15),
                end_date=datetime.date(2024, 9, 30),
            )
        )

        self.proposition_repository = PropositionInMemoryRepository()

        self.emplacement_document_repository = emplacement_document_in_memory_repository
        self.addCleanup(self.emplacement_document_repository.reset)

    def test_recalculer_emplacements_documents_non_libres_proposition(self):
        proposition = self.proposition_repository.get(PropositionIdentity('uuid-SC3DP-promoteur-membre'))

        emplacement_document = EmplacementDocument(
            entity_id=EmplacementDocumentIdentity(
                proposition_id=proposition.entity_id,
                identifiant='TAB.CUSTOM',
            ),
            uuids_documents=[],
            type=TypeEmplacementDocument.NON_LIBRE,
            statut=StatutEmplacementDocument.A_RECLAMER,
            justification_gestionnaire='',
        )

        self.emplacement_document_repository.save(emplacement_document)

        emplacement_document_curriculum = EmplacementDocument(
            entity_id=EmplacementDocumentIdentity(
                proposition_id=proposition.entity_id,
                identifiant='CURRICULUM.CURRICULUM',
            ),
            uuids_documents=[],
            type=TypeEmplacementDocument.NON_LIBRE,
            statut=StatutEmplacementDocument.A_RECLAMER,
            justification_gestionnaire='',
        )

        self.emplacement_document_repository.save(emplacement_document_curriculum)

        proposition_id = self.message_bus.invoke(self.cmd)

        self.assertEqual(proposition.entity_id, proposition_id)

        with self.assertRaises(EmplacementDocumentNonTrouveException):
            self.emplacement_document_repository.get(emplacement_document.entity_id)

        emplacement_document_pertinent = (
            self.emplacement_document_repository.get(
                emplacement_document_curriculum.entity_id,
            ),
        )

        self.assertIsNotNone(emplacement_document_pertinent)

    def test_lever_exception_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(RecupererDocumentsPropositionQuery(uuid_proposition='inexistant'))
