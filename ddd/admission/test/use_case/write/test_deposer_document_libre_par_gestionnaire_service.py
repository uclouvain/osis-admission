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

from admission.ddd.admission.commands import DeposerDocumentLibreParGestionnaireCommand
from admission.ddd.admission.domain.model.document import DocumentIdentity
from admission.ddd.admission.enums.document import TypeDocument, StatutDocument, OngletsDemande
from admission.infrastructure.admission.repository.in_memory.document import DocumentInMemoryRepository
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


@freezegun.freeze_time('2023-01-01')
class TestDeposerDocumentLibreParGestionnaire(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance
        self.repository = DocumentInMemoryRepository()
        self.repository.reset()
        self.uuid_proposition = str(uuid.uuid4())
        self.current_datetime = datetime.datetime.now()

    def test_should_deposer_document_libre_sic(self):
        identifiant_document_depose = self.message_bus.invoke(
            DeposerDocumentLibreParGestionnaireCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='0123456789',
                token_document='token-file',
                type_document=TypeDocument.CANDIDAT_SIC.name,
                nom_document='Nom du document',
            )
        )

        document = self.repository.get(entity_id=DocumentIdentity(identifiant=identifiant_document_depose))

        self.assertIsNotNone(document)

        self.assertEqual(document.entity_id.identifiant, f'{OngletsDemande.DOCUMENTS_ADDITIONNELS.name}.token-file')
        self.assertEqual(document.proposition.uuid, self.uuid_proposition)
        self.assertEqual(document.libelle, 'Nom du document')
        self.assertEqual(document.onglet, OngletsDemande.DOCUMENTS_ADDITIONNELS)
        self.assertEqual(document.uuids, ['token-file'])
        self.assertEqual(document.auteur, '0123456789')
        self.assertEqual(document.type, TypeDocument.CANDIDAT_SIC)
        self.assertEqual(document.statut, StatutDocument.VALIDE)
        self.assertEqual(document.justification_gestionnaire, '')
        self.assertEqual(document.soumis_le, self.current_datetime)
        self.assertEqual(document.reclame_le, None)
        self.assertEqual(document.a_echeance_le, None)
        self.assertEqual(document.derniere_action_le, self.current_datetime)

    def test_should_deposer_document_libre_fac(self):
        identifiant_document_depose = self.message_bus.invoke(
            DeposerDocumentLibreParGestionnaireCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='0123456789',
                token_document='token-file',
                type_document=TypeDocument.CANDIDAT_FAC.name,
                nom_document='Nom du document',
            )
        )

        document = self.repository.get(entity_id=DocumentIdentity(identifiant=identifiant_document_depose))

        self.assertIsNotNone(document)

        self.assertEqual(document.entity_id.identifiant, f'{OngletsDemande.DOCUMENTS_ADDITIONNELS.name}.token-file')
        self.assertEqual(document.proposition.uuid, self.uuid_proposition)
        self.assertEqual(document.libelle, 'Nom du document')
        self.assertEqual(document.onglet, OngletsDemande.DOCUMENTS_ADDITIONNELS)
        self.assertEqual(document.uuids, ['token-file'])
        self.assertEqual(document.auteur, '0123456789')
        self.assertEqual(document.type, TypeDocument.CANDIDAT_FAC)
        self.assertEqual(document.statut, StatutDocument.VALIDE)
        self.assertEqual(document.justification_gestionnaire, '')
        self.assertEqual(document.soumis_le, self.current_datetime)
        self.assertEqual(document.reclame_le, None)
        self.assertEqual(document.a_echeance_le, None)
        self.assertEqual(document.derniere_action_le, self.current_datetime)
