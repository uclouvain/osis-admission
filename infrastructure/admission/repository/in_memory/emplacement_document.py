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
from typing import Optional, List, Set

from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument, EmplacementDocumentIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.validator.exceptions import EmplacementDocumentNonTrouveException
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
    OngletsDemande,
)
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository
from osis_common.ddd.interface import EntityIdentity, ApplicationService


class EmplacementDocumentInMemoryRepository(IEmplacementDocumentRepository):
    entities: List[EmplacementDocument] = []

    def __init__(self):
        self.reset()

    @classmethod
    def reset(cls):
        cls.entities = [
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant='ID1',
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
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant='ID2',
                    proposition_id=PropositionIdentity(uuid='uuid-MASTER-SCI'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC,
                statut=StatutEmplacementDocument.A_RECLAMER,
                statut_reclamation=StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT,
                justification_gestionnaire='Ma raison 2',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant='ID3',
                    proposition_id=PropositionIdentity(uuid='uuid-MASTER-SCC'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC,
                statut=StatutEmplacementDocument.A_RECLAMER,
                justification_gestionnaire='Ma raison 3',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant='ID4',
                    proposition_id=PropositionIdentity(uuid='uuid-MASTER-SCI'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC,
                statut=StatutEmplacementDocument.A_RECLAMER,
                justification_gestionnaire='Ma raison 4',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant=f'{OngletsDemande.SUITE_AUTORISATION.name}.VISA_ETUDES',
                    proposition_id=PropositionIdentity(uuid='uuid-MASTER-SCI-APPROVED'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.NON_LIBRE,
                statut=StatutEmplacementDocument.NON_ANALYSE,
                justification_gestionnaire='Ma raison 4',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant=f'{OngletsDemande.SUITE_AUTORISATION.name}.AUTORISATION_PDF_SIGNEE',
                    proposition_id=PropositionIdentity(uuid='uuid-MASTER-SCI-APPROVED'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.NON_LIBRE,
                statut=StatutEmplacementDocument.NON_ANALYSE,
                justification_gestionnaire='Ma raison 4',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant=f'{OngletsDemande.SUITE_AUTORISATION.name}.VISA_ETUDES',
                    proposition_id=PropositionIdentity(uuid='uuid-SC3DP-APPROVED'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.NON_LIBRE,
                statut=StatutEmplacementDocument.NON_ANALYSE,
                justification_gestionnaire='Ma raison 4',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant=f'{OngletsDemande.SUITE_AUTORISATION.name}.AUTORISATION_PDF_SIGNEE',
                    proposition_id=PropositionIdentity(uuid='uuid-SC3DP-APPROVED'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.NON_LIBRE,
                statut=StatutEmplacementDocument.NON_ANALYSE,
                justification_gestionnaire='Ma raison 4',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant='ID1-FC',
                    proposition_id=PropositionIdentity(uuid='uuid-USCC4'),
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
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant='ID2-FC',
                    proposition_id=PropositionIdentity(uuid='uuid-USCC4'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC,
                statut=StatutEmplacementDocument.A_RECLAMER,
                statut_reclamation=StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT,
                justification_gestionnaire='Ma raison 2',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant='ID3-FC',
                    proposition_id=PropositionIdentity(uuid='uuid-MASTER-SCC'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC,
                statut=StatutEmplacementDocument.A_RECLAMER,
                justification_gestionnaire='Ma raison 3',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant='ID4-FC',
                    proposition_id=PropositionIdentity(uuid='uuid-USCC4'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC,
                statut=StatutEmplacementDocument.A_RECLAMER,
                justification_gestionnaire='Ma raison 4',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant='ID1-FD',
                    proposition_id=PropositionIdentity(uuid='uuid-SC3DP-promoteur-membre'),
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
            EmplacementDocument(
                entity_id=EmplacementDocumentIdentity(
                    identifiant='LIBRE_CANDIDAT.36de0c3d-3c06-4c93-8eb4-c8648f04f142',
                    proposition_id=PropositionIdentity(uuid='uuid-SC3DP-promoteur-membre'),
                ),
                uuids_documents=[],
                type=TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC,
                statut=StatutEmplacementDocument.A_RECLAMER,
                statut_reclamation=StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT,
                justification_gestionnaire='Ma raison 2',
                requis_automatiquement=False,
                libelle='Example',
                reclame_le=None,
                a_echeance_le=None,
                derniere_action_le=datetime.datetime(2023, 1, 1),
                dernier_acteur='0123456789',
                document_soumis_par='',
            ),
        ]

    @classmethod
    def search(
        cls,
        entity_ids: Optional[List[EmplacementDocumentIdentity]] = None,
        statut: Optional[StatutEmplacementDocument] = None,
        **kwargs,
    ) -> List[EmplacementDocument]:
        return [
            entity
            for entity in cls.entities
            if (entity_ids is None or entity.entity_id in entity_ids) and (statut is None or entity.statut == statut)
        ]

    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        for entity in cls.entities:
            if entity.entity_id == entity_id:
                cls.entities.remove(entity)
                return
        raise EmplacementDocumentNonTrouveException

    @classmethod
    def save(cls, entity: EmplacementDocument, auteur='') -> None:
        for previous_entity in cls.entities:
            if previous_entity.entity_id == entity.entity_id:
                cls.entities.remove(previous_entity)
        cls.entities.append(entity)

    @classmethod
    def get(cls, entity_id: EmplacementDocumentIdentity) -> EmplacementDocument:
        entity = next((entity for entity in cls.entities if entity.entity_id == entity_id), None)
        if not entity:
            raise EmplacementDocumentNonTrouveException
        return entity

    @classmethod
    def save_multiple(cls, entities: List[EmplacementDocument], auteur='') -> None:
        for entity in entities:
            cls.save(entity, auteur)

    @classmethod
    def reinitialiser_emplacements_documents_non_libres(
        cls,
        proposition_identity: PropositionIdentity,
        identifiants_documents_pertinents: Set[str],
    ) -> None:
        cls.entities = [
            entity
            for entity in cls.entities
            if entity.entity_id.proposition_id != proposition_identity
            or entity.type != TypeEmplacementDocument.NON_LIBRE
            or entity.entity_id.identifiant in identifiants_documents_pertinents
        ]


emplacement_document_in_memory_repository = EmplacementDocumentInMemoryRepository()
