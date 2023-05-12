# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import TestCase

import freezegun
from cffi.model import BaseTypeByIdentity

from admission.ddd.admission.commands import InitierEmplacementDocumentLibreInterneCommand
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    OngletsDemande,
    IdentifiantBaseEmplacementDocument,
)
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    EmplacementDocumentInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


@freezegun.freeze_time('2023-01-01')
class TestDeposerDocumentLibreParGestionnaire(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance
        self.repository = EmplacementDocumentInMemoryRepository()
        self.repository.reset()
        self.uuid_proposition = str(uuid.uuid4())
        self.current_datetime = datetime.datetime.now()

    def test_should_deposer_document_libre_sic(self):
        identifiant_document_depose = self.message_bus.invoke(
            InitierEmplacementDocumentLibreInterneCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='0123456789',
                uuid_document='token-file',
                type_emplacement=TypeEmplacementDocument.LIBRE_INTERNE_SIC.name,
                libelle='Nom du document',
            )
        )

        document = self.repository.get(entity_id=identifiant_document_depose)

        self.assertIsNotNone(document)

        base_identifier = document.entity_id.identifiant.split('.')[0]
        self.assertEqual(
            base_identifier,
            IdentifiantBaseEmplacementDocument.LIBRE_GESTIONNAIRE.name,
        )
        self.assertEqual(document.entity_id.proposition.uuid, self.uuid_proposition)
        self.assertEqual(document.libelle, 'Nom du document')
        self.assertEqual(document.uuids_documents, ['token-file'])
        self.assertEqual(document.dernier_acteur, '0123456789')
        self.assertEqual(document.type, TypeEmplacementDocument.LIBRE_INTERNE_SIC)
        self.assertEqual(document.statut, StatutEmplacementDocument.VALIDE)
        self.assertEqual(document.justification_gestionnaire, '')
        self.assertEqual(document.reclame_le, None)
        self.assertEqual(document.a_echeance_le, None)
        self.assertEqual(document.derniere_action_le, self.current_datetime)

    def test_should_deposer_document_libre_fac(self):
        identifiant_document_depose = self.message_bus.invoke(
            InitierEmplacementDocumentLibreInterneCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='0123456789',
                uuid_document='token-file',
                type_emplacement=TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
                libelle='Nom du document',
            )
        )

        document = self.repository.get(entity_id=identifiant_document_depose)

        self.assertIsNotNone(document)

        base_identifier = document.entity_id.identifiant.split('.')[0]
        self.assertEqual(
            base_identifier,
            IdentifiantBaseEmplacementDocument.LIBRE_GESTIONNAIRE.name,
        )
        self.assertEqual(document.entity_id.proposition.uuid, self.uuid_proposition)
        self.assertEqual(document.libelle, 'Nom du document')
        self.assertEqual(document.uuids_documents, ['token-file'])
        self.assertEqual(document.dernier_acteur, '0123456789')
        self.assertEqual(document.type, TypeEmplacementDocument.LIBRE_INTERNE_FAC)
        self.assertEqual(document.statut, StatutEmplacementDocument.VALIDE)
        self.assertEqual(document.justification_gestionnaire, '')
        self.assertEqual(document.reclame_le, None)
        self.assertEqual(document.a_echeance_le, None)
        self.assertEqual(document.derniere_action_le, self.current_datetime)
