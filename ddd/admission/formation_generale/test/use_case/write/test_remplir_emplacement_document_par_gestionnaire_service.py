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
import uuid
from unittest import TestCase

import freezegun

from admission.constants import UUID_REGEX
from admission.ddd.admission.formation_generale.commands import (
    InitialiserEmplacementDocumentLibreAReclamerCommand,
    RemplirEmplacementDocumentParGestionnaireCommand,
    InitialiserEmplacementDocumentLibreNonReclamableCommand,
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
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRemplirEmplacementDocumentParGestionnaire(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance
        self.repository = emplacement_document_in_memory_repository
        self.addCleanup(self.repository.reset)
        self.uuid_proposition = str(uuid.uuid4())
        self.regex_identifiant_candidat = (
            r'' + IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name + '.' + UUID_REGEX
        )
        self.regex_identifiant_gestionnaire = (
            r'' + IdentifiantBaseEmplacementDocument.LIBRE_GESTIONNAIRE.name + '.' + UUID_REGEX
        )

    def test_should_lever_exception_si_emplacement_document_inconnu(self):
        with self.assertRaises(EmplacementDocumentNonTrouveException):
            self.message_bus.invoke(
                RemplirEmplacementDocumentParGestionnaireCommand(
                    uuid_proposition=self.uuid_proposition,
                    auteur='0123456789',
                    uuid_document='uuid-document',
                    identifiant_emplacement='inconnu',
                )
            )

    @freezegun.freeze_time('2023-01-01', as_kwarg='freeze_time')
    def test_should_remplir_emplacement_document_sic_reclamable(self, freeze_time):
        # Initialiser un emplacement de document libre sic
        identifiant_emplacement_document_depose = self.message_bus.invoke(
            InitialiserEmplacementDocumentLibreAReclamerCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='0123456789',
                type_emplacement=TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                libelle_fr='Nom du document',
                libelle_en='Name of the document',
                raison='La raison.',
                statut_reclamation=StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            )
        )

        self.assertIsNotNone(identifiant_emplacement_document_depose)

        freeze_time.move_to('2023-01-03')
        identifiant_document_modifie = self.message_bus.invoke(
            RemplirEmplacementDocumentParGestionnaireCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='987654321',
                uuid_document='nouvel-uuid-document',
                identifiant_emplacement=identifiant_emplacement_document_depose.identifiant,
            )
        )

        self.assertIsNotNone(identifiant_document_modifie)

        document = self.repository.get(entity_id=identifiant_emplacement_document_depose)

        self.assertIsNotNone(document)

        self.assertRegex(document.entity_id.identifiant, self.regex_identifiant_candidat)
        self.assertEqual(document.entity_id.proposition_id.uuid, self.uuid_proposition)
        self.assertEqual(identifiant_document_modifie, identifiant_emplacement_document_depose)
        self.assertEqual(document.libelle, 'Nom du document')
        self.assertEqual(document.uuids_documents, ['nouvel-uuid-document'])
        self.assertEqual(document.dernier_acteur, '0123456789')
        self.assertEqual(document.type, TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC)
        self.assertEqual(document.statut, StatutEmplacementDocument.VALIDE)
        self.assertEqual(document.justification_gestionnaire, 'La raison.')
        self.assertEqual(document.reclame_le, None)
        self.assertEqual(document.a_echeance_le, None)
        self.assertEqual(document.derniere_action_le, datetime.datetime(2023, 1, 1))
        self.assertEqual(document.document_soumis_par, '987654321')
        self.assertEqual(document.requis_automatiquement, False)
        self.assertEqual(document.statut_reclamation, None)

    @freezegun.freeze_time('2023-01-01', as_kwarg='freeze_time')
    def test_should_remplir_emplacement_document_sic_non_reclamable_interne(self, freeze_time):
        # Initialiser un emplacement de document libre sic
        identifiant_emplacement_document_depose = self.message_bus.invoke(
            InitialiserEmplacementDocumentLibreNonReclamableCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='0123456789',
                type_emplacement=TypeEmplacementDocument.LIBRE_INTERNE_SIC.name,
                libelle='Nom du document',
                uuid_document='uuid-document',
            )
        )

        self.assertIsNotNone(identifiant_emplacement_document_depose)

        freeze_time.move_to('2023-01-03')
        identifiant_document_modifie = self.message_bus.invoke(
            RemplirEmplacementDocumentParGestionnaireCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='987654321',
                uuid_document='nouvel-uuid-document',
                identifiant_emplacement=identifiant_emplacement_document_depose.identifiant,
            )
        )

        self.assertIsNotNone(identifiant_document_modifie)

        document = self.repository.get(entity_id=identifiant_emplacement_document_depose)

        self.assertIsNotNone(document)

        self.assertRegex(document.entity_id.identifiant, self.regex_identifiant_gestionnaire)
        self.assertEqual(document.entity_id.proposition_id.uuid, self.uuid_proposition)
        self.assertEqual(identifiant_document_modifie, identifiant_emplacement_document_depose)
        self.assertEqual(document.libelle, 'Nom du document')
        self.assertEqual(document.uuids_documents, ['nouvel-uuid-document'])
        self.assertEqual(document.dernier_acteur, '0123456789')
        self.assertEqual(document.type, TypeEmplacementDocument.LIBRE_INTERNE_SIC)
        self.assertEqual(document.statut, StatutEmplacementDocument.VALIDE)
        self.assertEqual(document.justification_gestionnaire, '')
        self.assertEqual(document.reclame_le, None)
        self.assertEqual(document.a_echeance_le, None)
        self.assertEqual(document.derniere_action_le, datetime.datetime(2023, 1, 1))
        self.assertEqual(document.document_soumis_par, '987654321')
        self.assertEqual(document.requis_automatiquement, False)
        self.assertEqual(document.statut_reclamation, None)

    @freezegun.freeze_time('2023-01-01', as_kwarg='freeze_time')
    def test_should_remplir_emplacement_document_fac_reclamable(self, freeze_time):
        # Initialiser un emplacement de document libre fac
        identifiant_emplacement_document_depose = self.message_bus.invoke(
            InitialiserEmplacementDocumentLibreAReclamerCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='0123456789',
                type_emplacement=TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                libelle_fr='Nom du document',
                libelle_en='Name of the document',
                raison='La raison.',
                statut_reclamation=StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT.name,
            )
        )

        self.assertIsNotNone(identifiant_emplacement_document_depose)

        freeze_time.move_to('2023-01-03')
        identifiant_document_modifie = self.message_bus.invoke(
            RemplirEmplacementDocumentParGestionnaireCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='987654321',
                uuid_document='nouvel-uuid-document',
                identifiant_emplacement=identifiant_emplacement_document_depose.identifiant,
            )
        )

        self.assertIsNotNone(identifiant_document_modifie)

        document = self.repository.get(entity_id=identifiant_emplacement_document_depose)

        self.assertIsNotNone(document)

        self.assertRegex(document.entity_id.identifiant, self.regex_identifiant_candidat)
        self.assertEqual(document.entity_id.proposition_id.uuid, self.uuid_proposition)
        self.assertEqual(identifiant_document_modifie, identifiant_emplacement_document_depose)
        self.assertEqual(document.libelle, 'Nom du document')
        self.assertEqual(document.uuids_documents, ['nouvel-uuid-document'])
        self.assertEqual(document.dernier_acteur, '0123456789')
        self.assertEqual(document.type, TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC)
        self.assertEqual(document.statut, StatutEmplacementDocument.VALIDE)
        self.assertEqual(document.justification_gestionnaire, 'La raison.')
        self.assertEqual(document.reclame_le, None)
        self.assertEqual(document.a_echeance_le, None)
        self.assertEqual(document.derniere_action_le, datetime.datetime(2023, 1, 1))
        self.assertEqual(document.document_soumis_par, '987654321')
        self.assertEqual(document.requis_automatiquement, False)
        self.assertEqual(document.statut_reclamation, None)

    @freezegun.freeze_time('2023-01-01', as_kwarg='freeze_time')
    def test_should_remplir_emplacement_document_fac_non_reclamable_interne(self, freeze_time):
        # Initialiser un emplacement de document libre fac
        identifiant_emplacement_document_depose = self.message_bus.invoke(
            InitialiserEmplacementDocumentLibreNonReclamableCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='0123456789',
                type_emplacement=TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
                libelle='Nom du document',
                uuid_document='uuid-document',
            )
        )

        self.assertIsNotNone(identifiant_emplacement_document_depose)

        freeze_time.move_to('2023-01-03')
        identifiant_document_modifie = self.message_bus.invoke(
            RemplirEmplacementDocumentParGestionnaireCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='987654321',
                uuid_document='nouvel-uuid-document',
                identifiant_emplacement=identifiant_emplacement_document_depose.identifiant,
            )
        )

        self.assertIsNotNone(identifiant_document_modifie)

        document = self.repository.get(entity_id=identifiant_emplacement_document_depose)

        self.assertIsNotNone(document)

        self.assertRegex(document.entity_id.identifiant, self.regex_identifiant_gestionnaire)
        self.assertEqual(document.entity_id.proposition_id.uuid, self.uuid_proposition)
        self.assertEqual(identifiant_document_modifie, identifiant_emplacement_document_depose)
        self.assertEqual(document.libelle, 'Nom du document')
        self.assertEqual(document.uuids_documents, ['nouvel-uuid-document'])
        self.assertEqual(document.dernier_acteur, '0123456789')
        self.assertEqual(document.type, TypeEmplacementDocument.LIBRE_INTERNE_FAC)
        self.assertEqual(document.statut, StatutEmplacementDocument.VALIDE)
        self.assertEqual(document.justification_gestionnaire, '')
        self.assertEqual(document.reclame_le, None)
        self.assertEqual(document.a_echeance_le, None)
        self.assertEqual(document.derniere_action_le, datetime.datetime(2023, 1, 1))
        self.assertEqual(document.document_soumis_par, '987654321')
        self.assertEqual(document.requis_automatiquement, False)
        self.assertEqual(document.statut_reclamation, None)

    @freezegun.freeze_time('2023-01-01', as_kwarg='freeze_time')
    def test_should_remplir_emplacement_document_non_libre(self, freeze_time):
        identifiant_document_non_libre = f'{OngletsDemande.IDENTIFICATION.name}.PASSEPORT'

        # Initialiser un emplacement de document non libre
        self.repository.entities.append(
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant=identifiant_document_non_libre,
                    proposition_id=PropositionIdentity(self.uuid_proposition),
                ),
                uuids_documents=['uuid-document'],
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
                statut_reclamation=StatutReclamationEmplacementDocument.IMMEDIATEMENT,
            )
        )

        # Modifier l'emplacement de document non libre
        freeze_time.move_to('2023-01-03')
        identifiant_document_modifie = self.message_bus.invoke(
            RemplirEmplacementDocumentParGestionnaireCommand(
                uuid_proposition=self.uuid_proposition,
                auteur='987654321',
                uuid_document='nouvel-uuid-document',
                identifiant_emplacement=identifiant_document_non_libre,
            )
        )

        self.assertIsNotNone(identifiant_document_modifie)

        document = self.repository.get(entity_id=identifiant_document_modifie)

        self.assertIsNotNone(document)

        self.assertEqual(document.entity_id.proposition_id.uuid, self.uuid_proposition)
        self.assertEqual(document.libelle, '')
        self.assertEqual(document.uuids_documents, ['nouvel-uuid-document'])
        self.assertEqual(document.dernier_acteur, '')
        self.assertEqual(document.type, TypeEmplacementDocument.NON_LIBRE)
        self.assertEqual(document.statut, StatutEmplacementDocument.VALIDE)
        self.assertEqual(document.justification_gestionnaire, '')
        self.assertEqual(document.reclame_le, None)
        self.assertEqual(document.a_echeance_le, None)
        self.assertEqual(document.derniere_action_le, None)
        self.assertEqual(document.document_soumis_par, '987654321')
        self.assertEqual(document.requis_automatiquement, True)
        self.assertEqual(document.statut_reclamation, None)
