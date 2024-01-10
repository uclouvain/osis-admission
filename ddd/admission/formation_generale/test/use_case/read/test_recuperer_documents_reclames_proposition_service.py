# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import SimpleTestCase

from admission.ddd.admission.doctorat.preparation.test.factory.person import PersonneConnueUclDTOFactory
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import (
    DocumentsCurriculum,
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    OngletsDemande,
    IdentifiantBaseEmplacementDocument,
)
from admission.ddd.admission.formation_generale.commands import (
    RecupererDocumentsPropositionQuery,
    RecupererDocumentsReclamesPropositionQuery,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PropositionNonTrouveeException
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)


@freezegun.freeze_time('2023-10-01')
class RecupererDocumentsReclamesPropositionTestCase(SimpleTestCase):
    def setUp(self):
        self.cmd = RecupererDocumentsReclamesPropositionQuery(uuid_proposition='uuid-MASTER-SCI')
        self.message_bus = message_bus_in_memory_instance

        self.academic_year_repository = AcademicYearInMemoryRepository()

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

    def test_recuperer_documents_reclames_proposition(self):
        documents = self.message_bus.invoke(self.cmd)

        self.assertTrue(len(documents), 2)

        # Document non libre faisant l'objet d'une relance
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
                matricule='00321234',
                email=ANY,
                prenom=ANY,
                nom=ANY,
                adresse_professionnelle=ANY,
                langue=ANY,
            ),
        )
        self.assertEqual(curriculum.derniere_action_le, datetime.datetime(2023, 1, 2))
        self.assertEqual(curriculum.a_echeance_le, datetime.date(2023, 1, 19))
        self.assertEqual(curriculum.onglet, OngletsDemande.CURRICULUM.name)
        self.assertEqual(curriculum.nom_onglet, OngletsDemande.CURRICULUM.value)
        self.assertEqual(curriculum.nom_onglet_langue_candidat, OngletsDemande.CURRICULUM.value)
        self.assertEqual(curriculum.uuid_proposition, 'uuid-MASTER-SCI')
        self.assertEqual(curriculum.requis_automatiquement, False)

        # Documents libres réclamables
        document: Optional[EmplacementDocumentDTO] = next(
            (doc for doc in documents if doc.identifiant == 'LIBRE_CANDIDAT.16de0c3d-3c06-4c93-8eb4-c8648f04f146'),
            None,
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.libelle, '')
        self.assertEqual(document.libelle_langue_candidat, '')
        self.assertEqual(document.document_uuids, [])
        self.assertEqual(document.type, TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name)
        self.assertEqual(document.statut, StatutEmplacementDocument.RECLAME.name)
        self.assertEqual(document.justification_gestionnaire, 'Ce nouveau document pourrait être intéressant.')
        self.assertEqual(document.document_soumis_par, None)
        self.assertEqual(document.document_soumis_le, None)
        self.assertEqual(document.reclame_le, datetime.datetime(2023, 1, 3))
        self.assertEqual(
            document.dernier_acteur,
            PersonneConnueUclDTO(
                matricule='00987890',
                email=ANY,
                prenom=ANY,
                nom=ANY,
                adresse_professionnelle=ANY,
                langue=ANY,
            ),
        )
        self.assertEqual(document.derniere_action_le, datetime.datetime(2023, 1, 3))
        self.assertEqual(document.a_echeance_le, datetime.date(2023, 1, 19))
        self.assertEqual(document.onglet, IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name)
        self.assertEqual(document.nom_onglet, IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.value)
        self.assertEqual(document.nom_onglet_langue_candidat, IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.value)
        self.assertEqual(document.uuid_proposition, 'uuid-MASTER-SCI')
        self.assertEqual(document.requis_automatiquement, False)

    def test_lever_exception_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(RecupererDocumentsPropositionQuery(uuid_proposition='inexistant'))
