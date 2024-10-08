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
from typing import Optional
from unittest.mock import ANY

import freezegun
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.test.factory.person import PersonneConnueUclDTOFactory
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import (
    DocumentsCurriculum,
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    OngletsDemande,
    DocumentsIdentification,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.formation_continue.commands import (
    RecupererDocumentsPropositionQuery,
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
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)


@freezegun.freeze_time('2023-10-01')
class RecupererDocumentsPropositionTestCase(TestCase):
    def setUp(self):
        self.cmd = RecupererDocumentsPropositionQuery(uuid_proposition='uuid-USCC4')
        self.message_bus = message_bus_in_memory_instance

        proposition = PropositionInMemoryRepository.get(PropositionIdentity(uuid='uuid-USCC4'))
        proposition.curriculum = ['file1.pdf']

        self.academic_year_repository = AcademicYearInMemoryRepository()

        self.emplacement_document_repository = emplacement_document_in_memory_repository
        self.addCleanup(self.emplacement_document_repository.reset)

        self.academic_year_repository.save(
            AcademicYear(
                entity_id=AcademicYearIdentity(year=2023),
                start_date=datetime.date(2023, 9, 15),
                end_date=datetime.date(2024, 9, 30),
            )
        )

        for matricule in ['00321234', '00987890']:
            PersonneConnueUclInMemoryTranslator.personnes_connues_ucl.add(
                PersonneConnueUclDTOFactory(matricule=matricule),
            )

    def test_recuperer_documents_proposition(self):
        documents = self.message_bus.invoke(self.cmd)

        self.assertTrue(len(documents) > 0)

        # Document non libre ne faisant pas l'objet d'une relance
        photo_identite: Optional[EmplacementDocumentDTO] = next(
            (doc for doc in documents if doc.identifiant == 'IDENTIFICATION.PHOTO_IDENTITE'),
            None,
        )
        self.assertIsNotNone(photo_identite)
        self.assertEqual(photo_identite.libelle, DocumentsIdentification['PHOTO_IDENTITE'])
        self.assertEqual(photo_identite.libelle_langue_candidat, DocumentsIdentification['PHOTO_IDENTITE'])
        self.assertEqual(photo_identite.document_uuids, ['uuid11'])
        self.assertEqual(photo_identite.type, TypeEmplacementDocument.NON_LIBRE.name)
        self.assertEqual(photo_identite.statut, StatutEmplacementDocument.NON_ANALYSE.name)
        self.assertEqual(photo_identite.justification_gestionnaire, '')
        self.assertEqual(photo_identite.document_soumis_par, None)
        self.assertEqual(photo_identite.document_soumis_le, None)
        self.assertEqual(photo_identite.reclame_le, None)
        self.assertEqual(photo_identite.dernier_acteur, None)
        self.assertEqual(photo_identite.derniere_action_le, None)
        self.assertEqual(photo_identite.a_echeance_le, None)
        self.assertEqual(photo_identite.onglet, OngletsDemande.IDENTIFICATION.name)
        self.assertEqual(photo_identite.nom_onglet, OngletsDemande.IDENTIFICATION.value)
        self.assertEqual(photo_identite.nom_onglet_langue_candidat, OngletsDemande.IDENTIFICATION.value)
        self.assertEqual(photo_identite.uuid_proposition, 'uuid-USCC4')
        self.assertEqual(photo_identite.requis_automatiquement, True)

        curriculum: Optional[EmplacementDocumentDTO] = next(
            (doc for doc in documents if doc.identifiant == 'CURRICULUM.CURRICULUM'),
            None,
        )
        self.assertIsNotNone(curriculum)
        self.assertEqual(curriculum.libelle, DocumentsCurriculum['CURRICULUM'])
        self.assertEqual(curriculum.libelle_langue_candidat, DocumentsCurriculum['CURRICULUM'])
        self.assertEqual(curriculum.document_uuids, ['file1.pdf'])
        self.assertEqual(curriculum.type, TypeEmplacementDocument.NON_LIBRE.name)
        self.assertEqual(curriculum.statut, StatutEmplacementDocument.RECLAME.name)
        self.assertEqual(curriculum.justification_gestionnaire, 'Le document est à mettre à jour.')
        self.assertEqual(curriculum.document_soumis_par, None)
        self.assertEqual(curriculum.document_soumis_le, datetime.datetime(2023, 1, 1))
        self.assertEqual(curriculum.reclame_le, datetime.datetime(2023, 1, 2))
        self.assertEqual(
            curriculum.dernier_acteur,
            PersonneConnueUclDTO(
                matricule='00321234', email=ANY, prenom=ANY, nom=ANY, adresse_professionnelle=ANY, langue=ANY
            ),
        )
        self.assertEqual(curriculum.derniere_action_le, datetime.datetime(2023, 1, 2))
        self.assertEqual(curriculum.a_echeance_le, datetime.date(2023, 1, 19))
        self.assertEqual(curriculum.onglet, OngletsDemande.CURRICULUM.name)
        self.assertEqual(curriculum.nom_onglet, OngletsDemande.CURRICULUM.value)
        self.assertEqual(curriculum.nom_onglet_langue_candidat, OngletsDemande.CURRICULUM.value)
        self.assertEqual(
            curriculum.statut_reclamation,
            StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
        )
        self.assertEqual(curriculum.uuid_proposition, 'uuid-USCC4')
        self.assertEqual(curriculum.requis_automatiquement, False)

    def test_lever_exception_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(RecupererDocumentsPropositionQuery(uuid_proposition='inexistant'))
