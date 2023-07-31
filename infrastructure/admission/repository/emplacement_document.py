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
from typing import Optional, List, Union

from django.db import transaction
from django.utils.dateparse import parse_datetime, parse_date
from django.utils.text import slugify

from admission.contrib.models import (
    AdmissionFormItem,
    AdmissionFormItemInstantiation,
    GeneralEducationAdmission,
    DoctorateAdmission,
    ContinuingEducationAdmission,
)
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.form_item import TRANSLATION_LANGUAGES
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument, EmplacementDocumentIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.validator.exceptions import (
    PropositionNonTrouveeException,
    EmplacementDocumentNonTrouveException,
)
from admission.ddd.admission.enums import (
    TypeItemFormulaire,
    CritereItemFormulaireFormation,
    Onglets,
)
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES,
    EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES,
    EMPLACEMENTS_DOCUMENTS_RECLAMABLES,
    IDENTIFIANT_BASE_EMPLACEMENT_DOCUMENT_LIBRE_PAR_TYPE,
)
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository
from admission.infrastructure.utils import get_document_from_identifier, AdmissionDocument
from base.models.person import Person


class BaseEmplacementDocumentRepository(IEmplacementDocumentRepository):
    admission_model_class = BaseAdmission

    @classmethod
    def search(
        cls,
        entity_ids: Optional[List[EmplacementDocumentIdentity]] = None,
        statut: Optional[StatutEmplacementDocument] = None,
        **kwargs,
    ) -> List[EmplacementDocument]:
        if not entity_ids:
            return []

        admission = cls.get_admission(entity_id=entity_ids[0].proposition_id)
        entities = []

        for entity_id in entity_ids:
            emplacement_document = get_document_from_identifier(admission, entity_id.identifiant)

            if not emplacement_document:
                raise EmplacementDocumentNonTrouveException

            entity = cls.entity_from_dict(entity_id=entity_id, emplacement_document=emplacement_document)

            if not statut or statut == entity.statut:
                entities.append(entity)

        return entities

    @classmethod
    def save_multiple_emplacements_documents_reclamables(cls, entities: List[EmplacementDocument], auteur: str) -> None:
        from osis_document.api.utils import change_remote_metadata

        if not entities:
            return

        admission = cls.get_admission(entities[0].entity_id.proposition_id)

        admission.modified_at = datetime.datetime.now()
        admission.last_update_author = Person.objects.get(global_id=auteur)

        updated_fields_by_object = {
            admission: ['requested_documents', 'modified_at', 'last_update_author'],
        }

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

                # Update the related model if it's a new file
                emplacement_document = get_document_from_identifier(admission, entity.entity_id.identifiant)

                if not emplacement_document:
                    raise EmplacementDocumentNonTrouveException

                model_object = emplacement_document.obj
                model_field = emplacement_document.field
                specific_question_uuid = emplacement_document.specific_question_uuid
                document_uuids = emplacement_document.uuids

                if document_uuids != entity.uuids_documents:
                    if model_object not in updated_fields_by_object:
                        updated_fields_by_object[model_object] = [model_field]
                    else:
                        updated_fields_by_object[model_object].append(model_field)

                    if specific_question_uuid:
                        # For a specific question, replace the previous file
                        admission.specific_question_answers[specific_question_uuid] = entity.uuids_documents
                    else:
                        # Otherwise, update the related field in the specific object
                        setattr(model_object, model_field, entity.uuids_documents)

                    # Save the author of the file
                    change_remote_metadata(
                        token=entity.uuids_documents[0],
                        metadata={
                            'author': entity.document_soumis_par,
                        },
                    )

            for model_object, fields in updated_fields_by_object.items():
                model_object.save(update_fields=fields)

    @classmethod
    def entity_to_dict(cls, entity: EmplacementDocument) -> dict:
        """Returns the request data of the entity as a dictionary to store into the admission."""
        return {
            'last_actor': entity.dernier_acteur,
            'reason': entity.justification_gestionnaire,
            'type': entity.type.name,
            'last_action_at': entity.derniere_action_le or '',
            'status': entity.statut.name,
            'requested_at': entity.reclame_le or '',
            'deadline_at': entity.a_echeance_le or '',
            'automatically_required': entity.requis_automatiquement,
        }

    @classmethod
    def save_emplacement_document_libre_non_reclamable(
        cls,
        emplacement_document: EmplacementDocument,
        auteur: str,
    ) -> None:
        admission = cls.get_admission(entity_id=emplacement_document.entity_id.proposition_id)

        # Save the metadata of the file
        from osis_document.api.utils import change_remote_metadata

        change_remote_metadata(
            token=emplacement_document.uuids_documents[0],
            metadata={
                'explicit_name': emplacement_document.libelle,
                'author': emplacement_document.document_soumis_par,
            },
        )

        # Save the file into the admission
        field_name = {
            TypeEmplacementDocument.LIBRE_INTERNE_SIC: 'uclouvain_sic_documents',
            TypeEmplacementDocument.LIBRE_INTERNE_FAC: 'uclouvain_fac_documents',
        }[emplacement_document.type]

        document_uuids = getattr(admission, field_name, [])
        try:
            old_document_uuid = uuid.UUID(emplacement_document.entity_id.identifiant.split('.')[-1])
            document_uuids.remove(old_document_uuid)
        except ValueError:
            pass
        document_uuids.append(emplacement_document.uuids_documents[0])
        admission.modified_at = datetime.datetime.now()
        admission.last_update_author = Person.objects.get(global_id=auteur)

        admission.save(update_fields=[field_name, 'last_update_author', 'modified_at'])
        emplacement_document.entity_id = EmplacementDocumentIdentity(
            proposition_id=emplacement_document.entity_id.proposition_id,
            identifiant=(
                f'{IDENTIFIANT_BASE_EMPLACEMENT_DOCUMENT_LIBRE_PAR_TYPE[emplacement_document.type.name]}.'
                f'{getattr(admission, field_name, [])[-1]}'
            ),
        )

    @classmethod
    def save_emplacement_document_reclamable(cls, entity: EmplacementDocument, auteur: str) -> None:
        cls.save_multiple_emplacements_documents_reclamables(entities=[entity], auteur=auteur)

    @classmethod
    def save_multiple(cls, entities: List[EmplacementDocument], auteur='') -> None:
        return cls.save_multiple_emplacements_documents_reclamables(entities=entities, auteur=auteur)

    @classmethod
    def save(cls, entity: EmplacementDocument, auteur='') -> None:
        if entity.type.name in EMPLACEMENTS_DOCUMENTS_RECLAMABLES:
            return cls.save_emplacement_document_reclamable(entity, auteur=auteur)
        elif entity.type.name in EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES:
            return cls.save_emplacement_document_libre_non_reclamable(entity, auteur=auteur)
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: EmplacementDocumentIdentity) -> EmplacementDocument:
        admission = cls.get_admission(entity_id=entity_id.proposition_id)
        emplacement_document = get_document_from_identifier(admission, entity_id.identifiant)

        if not emplacement_document:
            raise EmplacementDocumentNonTrouveException

        return cls.entity_from_dict(entity_id, emplacement_document)

    @classmethod
    def entity_from_dict(
        cls,
        entity_id: EmplacementDocumentIdentity,
        emplacement_document: AdmissionDocument,
    ) -> EmplacementDocument:
        return EmplacementDocument(
            entity_id=entity_id,
            uuids_documents=emplacement_document.uuids,
            type=TypeEmplacementDocument[emplacement_document.type],
            statut=StatutEmplacementDocument[emplacement_document.status],
            justification_gestionnaire=emplacement_document.reason,
            libelle=emplacement_document.label,
            reclame_le=parse_datetime(emplacement_document.requested_at) if emplacement_document.requested_at else None,
            a_echeance_le=parse_date(emplacement_document.deadline_at) if emplacement_document.deadline_at else None,
            derniere_action_le=parse_datetime(emplacement_document.last_action_at)
            if emplacement_document.last_action_at
            else None,
            dernier_acteur=emplacement_document.last_actor,
            requis_automatiquement=emplacement_document.automatically_required,
            document_soumis_par=emplacement_document.document_submitted_by,
        )

    @classmethod
    def reinitialiser_emplacements_documents_non_libres(
        cls,
        proposition_identity: PropositionIdentity,
        entities: List[EmplacementDocument],
    ) -> None:
        admission = cls.get_admission(entity_id=proposition_identity)
        entities_to_keep = set(entity.entity_id.identifiant for entity in entities)

        # Remove or update the previously requested non free documents
        for requested_document_identifier in list(admission.requested_documents.keys()):
            current_document = admission.requested_documents[requested_document_identifier]

            if current_document['type'] == TypeEmplacementDocument.NON_LIBRE.name:
                # Indicate if this document is automatically required by the system
                current_document['automatically_required'] = requested_document_identifier in entities_to_keep

                # Remove the non free documents that weren't requested by a manager
                if not current_document['last_actor']:
                    del admission.requested_documents[requested_document_identifier]

        # Add the new documents requested by the system
        for entity in entities:
            if entity.entity_id.identifiant not in admission.requested_documents:
                admission.requested_documents[entity.entity_id.identifiant] = cls.entity_to_dict(entity)

        admission.save(update_fields=['requested_documents'])

    @classmethod
    def delete(cls, entity_id: EmplacementDocumentIdentity, auteur='', supprimer_donnees=False, **kwargs) -> None:
        admission = cls.get_admission(entity_id=entity_id.proposition_id)
        emplacement_document = get_document_from_identifier(admission, entity_id.identifiant)

        if not emplacement_document:
            raise EmplacementDocumentNonTrouveException

        admission.modified_at = datetime.datetime.now()
        admission.last_update_author = Person.objects.get(global_id=auteur)

        admission_update_fields = ['last_update_author', 'modified_at']

        model_object = emplacement_document.obj
        model_field = emplacement_document.field
        specific_question_uuid = emplacement_document.specific_question_uuid

        if model_object == admission:
            admission_update_fields.append(model_field)

        entity = cls.entity_from_dict(entity_id, emplacement_document)

        if supprimer_donnees and entity.type.name in EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES:
            # Remove the document from the admission field
            getattr(admission, model_field).remove(entity.uuids_documents[0])
            admission.save(update_fields=admission_update_fields)

        elif entity.type.name in EMPLACEMENTS_DOCUMENTS_RECLAMABLES:
            # Remove the document from the field of the related object
            if supprimer_donnees:

                if specific_question_uuid:
                    # For a specific question, remove the answer from the specific question field of the admission
                    admission.specific_question_answers.pop(specific_question_uuid, None)

                else:
                    # Otherwise, reset the related field in the specific object
                    setattr(model_object, model_field, [])

                with transaction.atomic():
                    if model_object != admission:
                        model_object.save(update_fields=[model_field])
                    admission.save(update_fields=admission_update_fields)

            # Don't keep the data related to the document request
            else:
                admission.requested_documents.pop(entity.entity_id.identifiant, None)

                with transaction.atomic():
                    admission.save(update_fields=['requested_documents', 'modified_at', 'last_update_author'])

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

    @classmethod
    def get_admission(
        cls,
        entity_id: PropositionIdentity,
    ) -> Union[GeneralEducationAdmission, DoctorateAdmission, ContinuingEducationAdmission]:
        try:
            return cls.admission_model_class.objects.get(uuid=entity_id.uuid)
        except cls.admission_model_class.DoesNotExist:
            raise PropositionNonTrouveeException
