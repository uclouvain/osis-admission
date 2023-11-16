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

import uuid
from unittest import TestCase

from admission.constants import UUID_REGEX
from admission.ddd.admission.formation_generale.commands import (
    InitialiserEmplacementDocumentLibreAReclamerCommand,
    AnnulerReclamationEmplacementDocumentCommand,
)
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument, EmplacementDocumentIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.validator.exceptions import EmplacementDocumentNonTrouveException
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    IdentifiantBaseEmplacementDocument,
    OngletsDemande,
    StatutReclamationEmplacementDocument,
)
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    EmplacementDocumentInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestAnnulerReclamationEmplacementDocument(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance
        self.repository = EmplacementDocumentInMemoryRepository()
        self.repository.reset()
        self.uuid_proposition = str(uuid.uuid4())
        self.regex_identifiant = r'' + IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name + '.' + UUID_REGEX

    def test_should_lever_exception_si_emplacement_document_inconnu(self):
        with self.assertRaises(EmplacementDocumentNonTrouveException):
            self.message_bus.invoke(
                AnnulerReclamationEmplacementDocumentCommand(
                    uuid_proposition=self.uuid_proposition,
                    identifiant_emplacement='inconnu',
                    auteur='0123456789',
                )
            )

    def test_should_annuler_reclamation_emplacement_document_sic(self):
        # Initialiser un emplacement de document libre sic
        identifiant_emplacement_document_depose = self.message_bus.invoke(
            InitialiserEmplacementDocumentLibreAReclamerCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='0123456789',
                type_emplacement=TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                libelle='Nom du document',
                raison='La raison expliquant l\'intérêt de ce nouveau document.',
                statut_reclamation=StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
            )
        )

        self.assertIsNotNone(identifiant_emplacement_document_depose)

        identifiant_emplacement_supprime = self.message_bus.invoke(
            AnnulerReclamationEmplacementDocumentCommand(
                uuid_proposition=self.uuid_proposition,
                identifiant_emplacement=identifiant_emplacement_document_depose.identifiant,
                auteur='0123456789',
            )
        )

        self.assertEqual(identifiant_emplacement_supprime, identifiant_emplacement_document_depose)

        with self.assertRaises(EmplacementDocumentNonTrouveException):
            self.repository.get(entity_id=identifiant_emplacement_document_depose)

    def test_should_annuler_reclamation_emplacement_document_fac(self):
        # Initialiser un emplacement de document libre fac
        identifiant_emplacement_document_depose = self.message_bus.invoke(
            InitialiserEmplacementDocumentLibreAReclamerCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='0123456789',
                type_emplacement=TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
                libelle='Nom du document',
                raison='La raison expliquant l\'intérêt de ce nouveau document.',
                statut_reclamation=StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
            )
        )

        self.assertIsNotNone(identifiant_emplacement_document_depose)

        identifiant_emplacement_supprime = self.message_bus.invoke(
            AnnulerReclamationEmplacementDocumentCommand(
                uuid_proposition=self.uuid_proposition,
                identifiant_emplacement=identifiant_emplacement_document_depose.identifiant,
                auteur='0123456789',
            )
        )

        self.assertEqual(identifiant_emplacement_supprime, identifiant_emplacement_document_depose)

        with self.assertRaises(EmplacementDocumentNonTrouveException):
            self.repository.get(entity_id=identifiant_emplacement_document_depose)

    def test_should_annuler_reclamation_emplacement_document_non_libre(self):
        # Initialiser un emplacement de document non libre
        identifiant_document_non_libre = f'{OngletsDemande.IDENTIFICATION.name}.PASSEPORT'

        # Initialiser un emplacement de document non libre
        emplacement_document = EmplacementDocument(
            entity_id=EmplacementDocumentIdentity(
                identifiant=identifiant_document_non_libre,
                proposition_id=PropositionIdentity(self.uuid_proposition),
            ),
            uuids_documents=[],
            type=TypeEmplacementDocument.NON_LIBRE,
            statut=StatutEmplacementDocument.A_RECLAMER,
            justification_gestionnaire='',
            requis_automatiquement=True,
            libelle='',
            reclame_le=None,
            a_echeance_le=None,
            derniere_action_le=None,
            dernier_acteur='',
            document_soumis_par='',
        )
        self.repository.entities.append(emplacement_document)

        identifiant_emplacement_supprime = self.message_bus.invoke(
            AnnulerReclamationEmplacementDocumentCommand(
                uuid_proposition=self.uuid_proposition,
                identifiant_emplacement=identifiant_document_non_libre,
                auteur='0123456789',
            )
        )

        self.assertEqual(identifiant_emplacement_supprime, emplacement_document.entity_id)

        with self.assertRaises(EmplacementDocumentNonTrouveException):
            self.repository.get(entity_id=emplacement_document.entity_id)
