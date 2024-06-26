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
from unittest import mock

import freezegun
from django.test import SimpleTestCase

from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity as SuperPropositionIdentity
from admission.ddd.admission.domain.validator.exceptions import EmplacementDocumentNonTrouveException
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.formation_continue.commands import (
    RecupererDocumentsPropositionQuery,
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_continue.domain.validator.exceptions import PropositionNonTrouveeException
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from infrastructure.shared_kernel.profil.repository.in_memory.profil import ProfilInMemoryRepository


@freezegun.freeze_time('2023-10-01')
class RecalculerEmplacementsDocumentsNonLibresPropositionTestCase(SimpleTestCase):
    def setUp(self):
        self.cmd = RecalculerEmplacementsDocumentsNonLibresPropositionCommand(uuid_proposition='uuid-USCC4')
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

        self.candidate = next(
            candidat
            for candidat in ProfilInMemoryRepository.profil
            if candidat.matricule == '0123456789'
        )

        patcher = mock.patch.multiple(self.candidate, carte_identite=[])
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_recalculer_emplacements_documents_non_libres_proposition(self):
        nb_entites = len(self.emplacement_document_repository.entities)

        proposition = self.proposition_repository.get(PropositionIdentity('uuid-USCC4'))
        proposition.documents_demandes['IDENTIFICATION.CARTE_IDENTITE'] = proposition.documents_demandes[
            'CURRICULUM.CURRICULUM'
        ]
        proposition_id = self.message_bus.invoke(self.cmd)

        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertTrue(len(self.emplacement_document_repository.entities) > nb_entites)

        try:
            emplacement_entity_id = EmplacementDocumentIdentity(
                identifiant='IDENTIFICATION.CARTE_IDENTITE',
                proposition_id=SuperPropositionIdentity('uuid-USCC4'),
            )
            emplacement = self.emplacement_document_repository.get(emplacement_entity_id)
            self.assertEqual(emplacement.entity_id, emplacement_entity_id)
            self.assertEqual(emplacement.uuids_documents, [])
            self.assertEqual(emplacement.type, TypeEmplacementDocument.NON_LIBRE)
            self.assertEqual(emplacement.statut, StatutEmplacementDocument.A_RECLAMER)
            self.assertEqual(emplacement.statut_reclamation, StatutReclamationEmplacementDocument.IMMEDIATEMENT)
            self.assertEqual(emplacement.justification_gestionnaire, '')
            self.assertEqual(emplacement.requis_automatiquement, True)
            self.assertEqual(emplacement.libelle, '')
            self.assertEqual(emplacement.reclame_le, None)
            self.assertEqual(emplacement.a_echeance_le, None)
            self.assertEqual(emplacement.derniere_action_le, datetime.datetime(2023, 10, 1))
            self.assertEqual(emplacement.dernier_acteur, '')
            self.assertEqual(emplacement.document_soumis_par, '')

        except EmplacementDocumentNonTrouveException:
            self.fail('The document placement \'CURRICULUM.CURRICULUM\' has not been added to the repository.')

    def test_lever_exception_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(RecupererDocumentsPropositionQuery(uuid_proposition='inexistant'))
