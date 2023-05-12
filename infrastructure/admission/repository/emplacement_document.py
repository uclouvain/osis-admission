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
from typing import Optional, List

from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify

from admission.contrib.models import AdmissionFormItem, AdmissionFormItemInstantiation
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.form_item import TRANSLATION_LANGUAGES
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument, EmplacementDocumentIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.validator.exceptions import (
    PropositionNonTrouveeException,
    EmplacementDocumentNonTrouveException,
)
from admission.ddd.admission.enums import TypeItemFormulaire, CritereItemFormulaireFormation, Onglets
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES,
    EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES,
    EMPLACEMENTS_DOCUMENTS_RECLAMABLES,
)
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository
from admission.infrastructure.utils import get_document_from_identifier


class EmplacementDocumentRepository(IEmplacementDocumentRepository):
    @classmethod
    def search(
        cls,
        entity_ids: Optional[List[EmplacementDocumentIdentity]] = None,
        **kwargs,
    ) -> List[EmplacementDocument]:
        if not entity_ids:
            return []
        try:
            admission = BaseAdmission.objects.get(uuid=entity_ids[0].proposition.uuid)
            entities = []

            for entity_id in entity_ids:
                pass
                emplacement_document = get_document_from_identifier(admission, entity_id.identifiant)

                if not emplacement_document:
                    raise EmplacementDocumentNonTrouveException

                entities.append(cls.entity_from_dict(entity_id=entity_id, emplacement_document=emplacement_document))

            return entities

        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def save_multiple_emplacements_documents_reclamables(cls, entities: List[EmplacementDocument]) -> None:
        if not entities:
            return
        try:
            admission: BaseAdmission = BaseAdmission.objects.get(uuid=entities[0].entity_id.proposition.uuid)

            with transaction.atomic():
                for entity in entities:
                    if entity.type.name not in EMPLACEMENTS_DOCUMENTS_RECLAMABLES:
                        raise NotImplementedError

                    # Create a specific question for each new free document
                    elif (
                        entity.type.name in EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES
                        and entity.entity_id.identifiant not in admission.requested_documents
                    ):
                        form_item = AdmissionFormItem(
                            internal_label=f'{admission.reference}.{slugify(entity.libelle)}',
                            type=TypeItemFormulaire.DOCUMENT.name,
                            title={language: entity.libelle for language in TRANSLATION_LANGUAGES},
                            uuid=entity.entity_id.identifiant.split('.')[-1],
                        )
                        form_item.save()
                        form_item_instantiation = AdmissionFormItemInstantiation(
                            form_item=form_item,
                            academic_year_id=admission.determined_academic_year_id,
                            weight=1,
                            required=True,
                            display_according_education=CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name,
                            admission=admission,
                            tab=Onglets.DOCUMENTS.name,
                        )
                        form_item_instantiation.save()

                    admission.requested_documents[entity.entity_id.identifiant] = cls.entity_to_dict(entity)

                admission.save(update_fields=['requested_documents'])

        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def entity_to_dict(cls, entity: EmplacementDocument) -> dict:
        return {
            'last_actor': entity.dernier_acteur,
            'reason': entity.justification_gestionnaire,
            'type': entity.type.name,
            'last_action_at': entity.derniere_action_le,
            'status': entity.statut.name,
            'requested_at': entity.reclame_le,
            'deadline_at': entity.a_echeance_le,
        }

    @classmethod
    def save_emplacement_document_libre_non_reclamable(cls, emplacement_document: EmplacementDocument):
        try:
            admission: BaseAdmission = BaseAdmission.objects.get(uuid=emplacement_document.entity_id.proposition.uuid)

            # Save the metadata of the file
            from osis_document.api.utils import change_remote_metadata

            change_remote_metadata(
                token=emplacement_document.uuids_documents[0],
                metadata={
                    'explicit_name': emplacement_document.libelle,
                    'author': emplacement_document.dernier_acteur,
                },
            )

            # Save the file into the admission
            field_name = {
                TypeEmplacementDocument.LIBRE_CANDIDAT_SIC: 'sic_documents',
                TypeEmplacementDocument.LIBRE_CANDIDAT_FAC: 'fac_documents',
                TypeEmplacementDocument.LIBRE_INTERNE_SIC: 'uclouvain_sic_documents',
                TypeEmplacementDocument.LIBRE_INTERNE_FAC: 'uclouvain_fac_documents',
            }[emplacement_document.type]

            getattr(admission, field_name).append(emplacement_document.uuids_documents[0])
            admission.save(update_fields=[field_name])

        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def save_emplacement_document_reclamable(cls, entity: EmplacementDocument):
        cls.save_multiple_emplacements_documents_reclamables(entities=[entity])

    @classmethod
    def save_multiple(cls, entities: List[EmplacementDocument]) -> None:
        return cls.save_multiple_emplacements_documents_reclamables(entities=entities)

    @classmethod
    def save(cls, entity: EmplacementDocument) -> None:
        if entity.type.name in EMPLACEMENTS_DOCUMENTS_RECLAMABLES:
            return cls.save_emplacement_document_reclamable(entity)
        elif entity.type.name in EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES:
            return cls.save_emplacement_document_libre_non_reclamable(entity)
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: EmplacementDocumentIdentity) -> EmplacementDocument:
        try:
            admission = BaseAdmission.objects.get(uuid=entity_id.proposition.uuid)
            emplacement_document = get_document_from_identifier(admission, entity_id.identifiant)

            if not emplacement_document:
                raise EmplacementDocumentNonTrouveException

            return cls.entity_from_dict(entity_id, emplacement_document)

        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def entity_from_dict(
        cls,
        entity_id: EmplacementDocumentIdentity,
        emplacement_document: dict,
    ) -> EmplacementDocument:
        return EmplacementDocument(
            entity_id=entity_id,
            uuids_documents=emplacement_document['uuids'],
            type=TypeEmplacementDocument[emplacement_document['type']],
            statut=StatutEmplacementDocument[emplacement_document['status']],
            justification_gestionnaire=emplacement_document['reason'] or '',
            libelle='',  # TODO ?
            reclame_le=emplacement_document['requested_at'] and parse_datetime(emplacement_document['requested_at']),
            a_echeance_le=emplacement_document['deadline_at'] and parse_datetime(emplacement_document['deadline_at']),
            derniere_action_le=emplacement_document['last_action_at']
            and parse_datetime(emplacement_document['last_action_at']),
            dernier_acteur=emplacement_document['last_actor'],
        )

    @classmethod
    def reinitialiser_emplacements_documents_non_libres(
        cls,
        proposition_identity: PropositionIdentity,
        entities: List[EmplacementDocument],
    ) -> None:
        try:
            admission: BaseAdmission = BaseAdmission.objects.get(uuid=proposition_identity.uuid)
            entities_to_keep = set(entity.entity_id.identifiant for entity in entities)

            # Remove the previous non free documents that are not requested anymore
            for requested_document_identifier in list(admission.requested_documents.keys()):
                if (
                    admission.requested_documents[requested_document_identifier].get('type')
                    == TypeEmplacementDocument.NON_LIBRE.name
                    and requested_document_identifier not in entities_to_keep
                ):
                    del admission.requested_documents[requested_document_identifier]

            # Add the new documents requested by the system
            for entity in entities:
                if entity.entity_id.identifiant not in admission.requested_documents:
                    admission.requested_documents[entity.entity_id.identifiant] = cls.entity_to_dict(entity)

            admission.save(update_fields=['requested_documents'])

        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def delete(cls, entity_id: EmplacementDocumentIdentity, supprimer_donnees=False, **kwargs) -> None:
        try:
            admission = BaseAdmission.objects.get(uuid=entity_id.proposition.uuid)
            emplacement_document = get_document_from_identifier(admission, entity_id.identifiant)

            if not emplacement_document:
                raise EmplacementDocumentNonTrouveException

            model_object = emplacement_document.get('obj')
            model_field = emplacement_document.get('field')
            specific_question_uuid = emplacement_document.get('specific_question_uuid')

            entity = cls.entity_from_dict(entity_id, emplacement_document)

            if supprimer_donnees and entity.type.name in EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES:
                # Remove the document from the admission field
                getattr(model_object, model_field).remove(entity.uuids_documents[0])
                model_object.save(update_fields=[model_field])

            elif entity.type.name in EMPLACEMENTS_DOCUMENTS_RECLAMABLES:
                admission_update_fields = []

                # Remove the document from the field of the related object
                if supprimer_donnees:

                    if specific_question_uuid:
                        # For a specific question, remove the answer from the specific question field of the admission
                        admission_update_fields = [model_field]
                        admission.specific_question_answers.pop(specific_question_uuid, None)

                    else:
                        # Otherwise, reset the related field in the specific object
                        setattr(model_object, model_field, [])

                        if model_object == admission:
                            admission_update_fields = [model_field]

                # Don't keep the data related to the document request
                else:
                    admission.requested_documents.pop(entity.entity_id.identifiant, None)
                    admission_update_fields.append('requested_documents')

                with transaction.atomic():
                    if admission_update_fields:
                        admission.save(update_fields=admission_update_fields)

                    if model_object != admission:
                        model_object.save(update_fields=[model_field])

                    # Remove the specific question for a free question
                    if entity.type.name in EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES:
                        form_item_instantiation_to_delete = AdmissionFormItemInstantiation.objects.filter(
                            form_item__uuid=specific_question_uuid
                        ).first()
                        related_form_item = form_item_instantiation_to_delete.form_item
                        form_item_instantiation_to_delete.delete()
                        related_form_item.delete()

            else:
                raise NotImplementedError

        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException
