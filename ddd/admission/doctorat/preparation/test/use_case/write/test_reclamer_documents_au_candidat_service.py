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
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import ReclamerDocumentsAuCandidatCommand
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument
from admission.ddd.admission.domain.model.enums.type_gestionnaire import TypeGestionnaire
from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class ReclamerDocumentsAuCandidatParFacTestCase(TestCase):
    def setUp(self) -> None:
        self.emplacements_document_repository = emplacement_document_in_memory_repository
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.addCleanup(self.emplacements_document_repository.reset)
        self.message_bus = message_bus_in_memory_instance

    @freezegun.freeze_time("2023-01-03")
    def test_should_reclamer_emplacements_au_candidat_par_fac(self):
        proposition_id = self.message_bus.invoke(
            ReclamerDocumentsAuCandidatCommand(
                uuid_proposition='uuid-SC3DP-promoteur-membre',
                identifiants_emplacements=['ID1-FD'],
                a_echeance_le=datetime.date(2023, 1, 15),
                objet_message='Objet du message',
                corps_message='Corps du message',
                auteur='987654321',
                type_gestionnaire=TypeGestionnaire.FAC.name,
            )
        )

        emplacements_documents: Dict[str, EmplacementDocument] = {
            emplacement_document.entity_id.identifiant: emplacement_document
            for emplacement_document in self.emplacements_document_repository.search()
        }

        # Les emplacements de documents réclamés ont été modifiés
        for identifiant in ['ID1-FD']:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, '987654321')
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, datetime.date(2023, 1, 15))
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 3))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, datetime.datetime(2023, 1, 3))
            self.assertEqual(emplacements_documents[identifiant].statut, StatutEmplacementDocument.RECLAME)

        # Les emplacements de documents non réclamés sont restés identifiques
        for identifiant in ['LIBRE_CANDIDAT.36de0c3d-3c06-4c93-8eb4-c8648f04f142']:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, '0123456789')
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, None)
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 1))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, None)
            self.assertEqual(emplacements_documents[identifiant].statut, StatutEmplacementDocument.A_RECLAMER)

        # Le statut de la proposition a changé
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC)

    @freezegun.freeze_time("2023-01-03")
    def test_should_reclamer_emplacements_au_candidat_par_sic(self):
        proposition_id = self.message_bus.invoke(
            ReclamerDocumentsAuCandidatCommand(
                uuid_proposition='uuid-SC3DP-promoteur-membre',
                identifiants_emplacements=['LIBRE_CANDIDAT.36de0c3d-3c06-4c93-8eb4-c8648f04f142'],
                a_echeance_le=datetime.date(2023, 1, 15),
                objet_message='Objet du message',
                corps_message='Corps du message',
                auteur='987654321',
                type_gestionnaire=TypeGestionnaire.SIC.name,
            )
        )

        emplacements_documents: Dict[str, EmplacementDocument] = {
            emplacement_document.entity_id.identifiant: emplacement_document
            for emplacement_document in self.emplacements_document_repository.search()
        }

        # Les emplacements de documents réclamés ont été modifiés
        for identifiant in ['LIBRE_CANDIDAT.36de0c3d-3c06-4c93-8eb4-c8648f04f142']:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, '987654321')
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, datetime.date(2023, 1, 15))
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 3))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, datetime.datetime(2023, 1, 3))
            self.assertEqual(emplacements_documents[identifiant].statut, StatutEmplacementDocument.RECLAME)

        # Les emplacements de documents non réclamés sont restés identifiques
        for identifiant in ['ID1-FD']:
            self.assertEqual(emplacements_documents[identifiant].dernier_acteur, '0123456789')
            self.assertEqual(emplacements_documents[identifiant].a_echeance_le, None)
            self.assertEqual(emplacements_documents[identifiant].derniere_action_le, datetime.datetime(2023, 1, 1))
            self.assertEqual(emplacements_documents[identifiant].reclame_le, None)
            self.assertEqual(emplacements_documents[identifiant].statut, StatutEmplacementDocument.A_RECLAMER)

        # Le statut de la proposition a changé
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC)

    def test_should_pas_reclames_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                ReclamerDocumentsAuCandidatCommand(
                    uuid_proposition='INCONNUE',
                    identifiants_emplacements=['ID1', 'ID2'],
                    a_echeance_le=datetime.date(2023, 1, 15),
                    objet_message='Objet du message',
                    corps_message='Corps du message',
                    auteur='987654321',
                    type_gestionnaire=TypeGestionnaire.FAC.name,
                )
            )
