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
import uuid
from unittest import TestCase

import freezegun

from admission.constants import UUID_REGEX
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    IdentifiantBaseEmplacementDocument,
    OngletsDemande,
)
from admission.ddd.admission.formation_generale.commands import (
    InitialiserEmplacementDocumentAReclamerCommand,
)
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestInitialiserEmplacementDocumentAReclamer(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance
        self.repository = emplacement_document_in_memory_repository
        self.addCleanup(self.repository.reset)
        self.uuid_proposition = str(uuid.uuid4())
        self.regex_identifiant = r'' + IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name + '.' + UUID_REGEX

    @freezegun.freeze_time('2023-01-01')
    def test_should_initialiser_emplacement_document_a_reclamer_non_libre(self):
        identifiant_document_non_libre = f'{OngletsDemande.IDENTIFICATION.name}.PASSEPORT'

        identifiant_document_initialise = self.message_bus.invoke(
            InitialiserEmplacementDocumentAReclamerCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='987654321',
                raison='La raison.',
                identifiant_emplacement=identifiant_document_non_libre,
                type_emplacement=TypeEmplacementDocument.NON_LIBRE.name,
            )
        )

        self.assertIsNotNone(identifiant_document_initialise)

        document = self.repository.get(entity_id=identifiant_document_initialise)

        self.assertIsNotNone(document)

        self.assertEqual(document.entity_id.proposition_id.uuid, self.uuid_proposition)
        self.assertEqual(document.libelle, '')
        self.assertEqual(document.uuids_documents, [])
        self.assertEqual(document.dernier_acteur, '987654321')
        self.assertEqual(document.type, TypeEmplacementDocument.NON_LIBRE)
        self.assertEqual(document.statut, StatutEmplacementDocument.A_RECLAMER)
        self.assertEqual(document.justification_gestionnaire, 'La raison.')
        self.assertEqual(document.reclame_le, None)
        self.assertEqual(document.a_echeance_le, None)
        self.assertEqual(document.derniere_action_le, datetime.datetime(2023, 1, 1))
        self.assertEqual(document.document_soumis_par, '')
        self.assertEqual(document.requis_automatiquement, True)
