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
import datetime
from typing import Dict

import freezegun
from django.test import SimpleTestCase

from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument, EmplacementDocumentIdentity
from admission.ddd.admission.enums.emplacement_document import (
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
    TypeEmplacementDocument,
)
from admission.ddd.admission.formation_generale.commands import (
    ReclamerDocumentsAuCandidatParFACCommand,
    ReclamerDocumentsAuCandidatParSICCommand,
    AnnulerReclamationDocumentsAuCandidatCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PropositionNonTrouveeException
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


class AnnulerReclamationDocumentsAuCandidatTestCase(SimpleTestCase):
    def setUp(self) -> None:
        self.emplacements_document_repository = emplacement_document_in_memory_repository
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.addCleanup(self.emplacements_document_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-MASTER-SCI'))
        academic_year_repository = AcademicYearInMemoryRepository()
        for annee in range(2016, 2023):
            academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )
        self.id_curriculum = 'CURRICULUM.CURRICULUM'
        self.id_document_libre = 'LIBRE_CANDIDAT.16de0c3d-3c06-4c93-8eb4-c8648f04f146'

        # Initialiser les emplacements
        emplacement_document_in_memory_repository.save(
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant=self.id_curriculum,
                    proposition_id=PropositionIdentity(uuid='uuid-MASTER-SCI'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC,
                statut=StatutEmplacementDocument.A_RECLAMER,
                statut_reclamation=StatutReclamationEmplacementDocument.IMMEDIATEMENT,
                justification_gestionnaire='Ma raison 1',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
        )
        emplacement_document_in_memory_repository.save(
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant=self.id_document_libre,
                    proposition_id=PropositionIdentity(uuid='uuid-MASTER-SCI'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC,
                statut=StatutEmplacementDocument.A_RECLAMER,
                statut_reclamation=StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT,
                justification_gestionnaire='Ma raison 2',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
        )

    @freezegun.freeze_time("2023-01-03", as_kwarg="freeze_time")
    def test_should_annuler_reclamation_documents_par_fac(self, freeze_time):
        # Le gestionnaire réclame les emplacements de documents
        self.message_bus.invoke(
            ReclamerDocumentsAuCandidatParFACCommand(
                uuid_proposition='uuid-MASTER-SCI',
                identifiants_emplacements=[self.id_curriculum, self.id_document_libre],
                a_echeance_le=datetime.date(2023, 1, 15),
                objet_message='Objet du message',
                corps_message='Corps du message',
                auteur='987654321',
            )
        )

        freeze_time.move_to('2023-01-05')

        # Le gestionnaire annule la réclamation
        proposition_id = self.message_bus.invoke(
            AnnulerReclamationDocumentsAuCandidatCommand(
                uuid_proposition='uuid-MASTER-SCI',
                auteur='987654321',
                par_fac=True,
            )
        )

        emplacements_documents: Dict[str, EmplacementDocument] = {
            emplacement_document.entity_id.identifiant: emplacement_document
            for emplacement_document in self.emplacements_document_repository.search()
        }

        proposition = self.proposition_repository.get(proposition_id)

        # Les emplacements des documents réclamés ont été modifiés
        for identifiant in [self.id_curriculum, self.id_document_libre]:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, '987654321')
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, datetime.date(2023, 1, 15))
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 5))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, datetime.datetime(2023, 1, 3))
            self.assertEqual(emplacements_documents[identifiant].statut, StatutEmplacementDocument.RECLAMATION_ANNULEE)
            self.assertEqual(emplacements_documents[identifiant].document_soumis_par, '')
            self.assertEqual(emplacements_documents[identifiant].uuids_documents, [])

        emplacement_curriculum = emplacements_documents[self.id_curriculum]
        self.assertEqual(emplacement_curriculum.statut_reclamation, StatutReclamationEmplacementDocument.IMMEDIATEMENT)
        self.assertEqual(emplacement_curriculum.justification_gestionnaire, 'Ma raison 1')

        emplacement_document_libre = emplacements_documents[self.id_document_libre]
        self.assertEqual(
            emplacement_document_libre.statut_reclamation, StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT
        )
        self.assertEqual(emplacement_document_libre.justification_gestionnaire, 'Ma raison 2')

        # Les emplacements des documents non réclamés sont restés identifiques
        for identifiant in ['ID3', 'ID4']:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, '0123456789')
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, None)
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 1))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, None)
            self.assertEqual(emplacements_documents[identifiant].statut, StatutEmplacementDocument.A_RECLAMER)

        # Le statut de la proposition a changé
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.TRAITEMENT_FAC)

    @freezegun.freeze_time("2023-01-03", as_kwarg="freeze_time")
    def test_should_annuler_reclamation_documents_par_sic(self, freeze_time):
        # Le gestionnaire réclame les emplacements de documents
        self.message_bus.invoke(
            ReclamerDocumentsAuCandidatParSICCommand(
                uuid_proposition='uuid-MASTER-SCI',
                identifiants_emplacements=[self.id_curriculum, self.id_document_libre],
                a_echeance_le=datetime.date(2023, 1, 15),
                objet_message='Objet du message',
                corps_message='Corps du message',
                auteur='987654321',
            )
        )

        freeze_time.move_to('2023-01-05')

        # Le gestionnaire annule la réclamation
        proposition_id = self.message_bus.invoke(
            AnnulerReclamationDocumentsAuCandidatCommand(
                uuid_proposition='uuid-MASTER-SCI',
                auteur='987654321',
                par_fac=False,
            )
        )

        emplacements_documents: Dict[str, EmplacementDocument] = {
            emplacement_document.entity_id.identifiant: emplacement_document
            for emplacement_document in self.emplacements_document_repository.search()
        }

        proposition = self.proposition_repository.get(proposition_id)

        # Les emplacements des documents réclamés ont été modifiés
        for identifiant in [self.id_curriculum, self.id_document_libre]:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, '987654321')
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, datetime.date(2023, 1, 15))
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 5))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, datetime.datetime(2023, 1, 3))
            self.assertEqual(emplacements_documents[identifiant].statut, StatutEmplacementDocument.RECLAMATION_ANNULEE)
            self.assertEqual(emplacements_documents[identifiant].document_soumis_par, '')
            self.assertEqual(emplacements_documents[identifiant].uuids_documents, [])

        emplacement_curriculum = emplacements_documents[self.id_curriculum]
        self.assertEqual(emplacement_curriculum.statut_reclamation, StatutReclamationEmplacementDocument.IMMEDIATEMENT)
        self.assertEqual(emplacement_curriculum.justification_gestionnaire, 'Ma raison 1')

        emplacement_document_libre = emplacements_documents[self.id_document_libre]
        self.assertEqual(
            emplacement_document_libre.statut_reclamation, StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT
        )
        self.assertEqual(emplacement_document_libre.justification_gestionnaire, 'Ma raison 2')

        # Les emplacements des documents non réclamés sont restés identifiques
        for identifiant in ['ID3', 'ID4']:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, '0123456789')
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, None)
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 1))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, None)
            self.assertEqual(emplacements_documents[identifiant].statut, StatutEmplacementDocument.A_RECLAMER)

        # Le statut de la proposition a changé
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.CONFIRMEE)

    @freezegun.freeze_time("2023-01-03")
    def test_should_lever_exception_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                AnnulerReclamationDocumentsAuCandidatCommand(
                    uuid_proposition='INCONNUE',
                    auteur='987654321',
                    par_fac=True,
                )
            )
