# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid
from typing import Dict

import freezegun
from django.test import SimpleTestCase

from admission.ddd.admission.domain.model.emplacement_document import (
    EmplacementDocument,
    EmplacementDocumentIdentity,
)
from admission.ddd.admission.domain.validator.exceptions import (
    DocumentsCompletesDifferentsDesReclamesException,
    DocumentsReclamesImmediatementNonCompletesException,
)
from admission.ddd.admission.enums.emplacement_document import (
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
    TypeEmplacementDocument,
)
from admission.ddd.admission.formation_generale.commands import (
    CompleterEmplacementsDocumentsParCandidatCommand,
    ReclamerDocumentsAuCandidatParFACCommand,
    ReclamerDocumentsAuCandidatParSICCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
    AcademicYearIdentity,
)
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import (
    AcademicYearInMemoryRepository,
)


class CompleterEmplacementsDocumentsParCandidatTestCase(SimpleTestCase):
    def setUp(self) -> None:
        self.emplacements_document_repository = emplacement_document_in_memory_repository
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.addCleanup(self.emplacements_document_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.uuid_id1 = str(uuid.uuid4())
        self.uuid_id2 = str(uuid.uuid4())
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

    @freezegun.freeze_time("2023-01-03", as_kwarg="freeze_time")
    def test_should_completer_emplacements_documents_demandes_par_fac(self, freeze_time):
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

        # Le candidat remplit les emplacements demandés
        proposition_id = self.message_bus.invoke(
            CompleterEmplacementsDocumentsParCandidatCommand(
                uuid_proposition='uuid-MASTER-SCI',
                reponses_documents_a_completer={
                    self.id_curriculum: [self.uuid_id1],
                    self.id_document_libre: [self.uuid_id2],
                },
            ),
        )

        emplacements_documents: Dict[str, EmplacementDocument] = {
            emplacement_document.entity_id.identifiant: emplacement_document
            for emplacement_document in self.emplacements_document_repository.search()
        }

        proposition = self.proposition_repository.get(proposition_id)

        # Les emplacements des documents réclamés ont été modifiés
        for identifiant in [self.id_curriculum, self.id_document_libre]:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, self.proposition.matricule_candidat)
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, datetime.date(2023, 1, 15))
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 5))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, datetime.datetime(2023, 1, 3))
            self.assertEqual(
                emplacements_documents[identifiant].statut,
                StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION,
            )
            self.assertEqual(emplacements_documents[identifiant].statut_reclamation, None)
            self.assertEqual(emplacements_documents[identifiant].document_soumis_par, proposition.matricule_candidat)

        self.assertEqual(emplacements_documents[self.id_curriculum].uuids_documents, [self.uuid_id1])
        self.assertEqual(emplacements_documents[self.id_document_libre].uuids_documents, [self.uuid_id2])

        # Les emplacements des documents non réclamés sont restés identifiques
        for identifiant in ['ID3', 'ID4']:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, '0123456789')
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, None)
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 1))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, None)
            self.assertEqual(emplacements_documents[identifiant].statut, StatutEmplacementDocument.A_RECLAMER)

        # Le statut de la proposition a changé et la date d'échéance de réclamation est réinitialisée
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC)
        self.assertIsNone(proposition.echeance_demande_documents)

    @freezegun.freeze_time("2023-01-03", as_kwarg="freeze_time")
    def test_should_completer_emplacements_documents_demandes_immediatement_par_fac(self, freeze_time):
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

        # Le candidat remplit les emplacements demandés immédiatement uniquement
        proposition_id = self.message_bus.invoke(
            CompleterEmplacementsDocumentsParCandidatCommand(
                uuid_proposition='uuid-MASTER-SCI',
                reponses_documents_a_completer={
                    self.id_curriculum: [self.uuid_id1],
                    self.id_document_libre: [],
                },
            ),
        )

        emplacements_documents: Dict[str, EmplacementDocument] = {
            emplacement_document.entity_id.identifiant: emplacement_document
            for emplacement_document in self.emplacements_document_repository.search()
        }

        proposition = self.proposition_repository.get(proposition_id)

        # Les emplacements des documents réclamés ont été modifiés
        # Le curriculum a été complété par le candidat
        self.assertEqual(emplacements_documents[self.id_curriculum].dernier_acteur, proposition.matricule_candidat)
        self.assertEqual(emplacements_documents[self.id_curriculum].a_echeance_le, datetime.date(2023, 1, 15))
        self.assertEqual(emplacements_documents[self.id_curriculum].derniere_action_le, datetime.datetime(2023, 1, 5))
        self.assertEqual(emplacements_documents[self.id_curriculum].reclame_le, datetime.datetime(2023, 1, 3))
        self.assertEqual(
            emplacements_documents[self.id_curriculum].statut,
            StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION,
        )
        self.assertEqual(emplacements_documents[self.id_curriculum].statut_reclamation, None)
        self.assertEqual(emplacements_documents[self.id_curriculum].document_soumis_par, proposition.matricule_candidat)

        self.assertEqual(emplacements_documents[self.id_curriculum].uuids_documents, [self.uuid_id1])

        # Le document libre n'a pas été complété par le candidat
        self.assertEqual(emplacements_documents[self.id_document_libre].dernier_acteur, proposition.matricule_candidat)
        self.assertEqual(emplacements_documents[self.id_document_libre].a_echeance_le, datetime.date(2023, 1, 15))
        self.assertEqual(
            emplacements_documents[self.id_document_libre].derniere_action_le,
            datetime.datetime(2023, 1, 5),
        )
        self.assertEqual(emplacements_documents[self.id_document_libre].reclame_le, datetime.datetime(2023, 1, 3))
        self.assertEqual(emplacements_documents[self.id_document_libre].statut, StatutEmplacementDocument.A_RECLAMER)
        self.assertEqual(emplacements_documents[self.id_document_libre].document_soumis_par, '')
        self.assertEqual(
            emplacements_documents[self.id_document_libre].statut_reclamation,
            StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT,
        )

        self.assertEqual(emplacements_documents[self.id_document_libre].uuids_documents, [])

        # Le statut de la proposition a changé et la date d'échéance de réclamation est réinitialisée
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC)
        self.assertIsNone(proposition.echeance_demande_documents)

    @freezegun.freeze_time("2023-01-03")
    def test_should_pas_completer_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                CompleterEmplacementsDocumentsParCandidatCommand(
                    uuid_proposition='INCONNUE',
                    reponses_documents_a_completer={
                        'ID1': [self.uuid_id1],
                        'ID2': [self.uuid_id2],
                    },
                )
            )

    @freezegun.freeze_time("2023-01-03")
    def test_should_lever_exception_si_documents_reclames_immediatement_ne_sont_pas_completes(self):
        # Le gestionnaire réclame les emplacements de documents
        self.message_bus.invoke(
            ReclamerDocumentsAuCandidatParFACCommand(
                uuid_proposition='uuid-MASTER-SCI',
                identifiants_emplacements=[self.id_curriculum, self.id_curriculum],
                a_echeance_le=datetime.date(2023, 1, 15),
                objet_message='Objet du message',
                corps_message='Corps du message',
                auteur='987654321',
            )
        )

        # Le candidat ne remplit pas tous les emplacements demandés immédiatement
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                CompleterEmplacementsDocumentsParCandidatCommand(
                    uuid_proposition='uuid-MASTER-SCI',
                    reponses_documents_a_completer={
                        self.id_curriculum: [],
                        self.id_document_libre: [],
                    },
                ),
            )
            exception = context.exception.exceptions.pop()
            self.assertIsInstance(exception, DocumentsReclamesImmediatementNonCompletesException)

    @freezegun.freeze_time("2023-01-03")
    def test_should_lever_exception_si_documents_non_reclames_sont_completes(self):
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

        # Le candidat remplit un document qui n'est pas demandé
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                CompleterEmplacementsDocumentsParCandidatCommand(
                    uuid_proposition='uuid-MASTER-SCI',
                    reponses_documents_a_completer={
                        self.id_curriculum: [self.uuid_id1],
                        'ID3': [self.uuid_id2],
                    },
                ),
            )
            exception = context.exception.exceptions.pop()
            self.assertIsInstance(exception, DocumentsCompletesDifferentsDesReclamesException)

    @freezegun.freeze_time("2023-01-03", as_kwarg="freeze_time")
    def test_should_completer_emplacements_documents_demandes_par_sic(self, freeze_time):
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

        # Le candidat remplit les emplacements demandés
        proposition_id = self.message_bus.invoke(
            CompleterEmplacementsDocumentsParCandidatCommand(
                uuid_proposition='uuid-MASTER-SCI',
                reponses_documents_a_completer={
                    self.id_curriculum: [self.uuid_id1],
                    self.id_document_libre: [self.uuid_id2],
                },
            ),
        )

        emplacements_documents: Dict[str, EmplacementDocument] = {
            emplacement_document.entity_id.identifiant: emplacement_document
            for emplacement_document in self.emplacements_document_repository.search()
        }

        proposition = self.proposition_repository.get(proposition_id)

        # Les emplacements de documents réclamés ont été modifiés
        for identifiant in [self.id_curriculum, self.id_document_libre]:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, proposition.matricule_candidat)
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, datetime.date(2023, 1, 15))
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 5))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, datetime.datetime(2023, 1, 3))
            self.assertEqual(
                emplacements_documents[identifiant].statut,
                StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION,
            )
            self.assertEqual(emplacements_documents[identifiant].document_soumis_par, proposition.matricule_candidat)
            self.assertEqual(emplacements_documents[identifiant].statut_reclamation, None)

        self.assertEqual(emplacements_documents[self.id_curriculum].uuids_documents, [self.uuid_id1])
        self.assertEqual(emplacements_documents[self.id_document_libre].uuids_documents, [self.uuid_id2])

        # Les emplacements de documents non réclamés sont restés identifiques
        for identifiant in ['ID3', 'ID4']:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, '0123456789')
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, None)
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 1))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, None)
            self.assertEqual(emplacements_documents[identifiant].statut, StatutEmplacementDocument.A_RECLAMER)

        # Le statut de la proposition a changé
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC)
