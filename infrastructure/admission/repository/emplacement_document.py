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
from django.utils.text import slugify

from admission.contrib.models import AdmissionFormItem, AdmissionFormItemInstantiation
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.form_item import TRANSLATION_LANGUAGES
from admission.ddd.admission.domain.model.demande import DemandeIdentity
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument, EmplacementDocumentIdentity
from admission.ddd.admission.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.ddd.admission.enums import TypeItemFormulaire, CritereItemFormulaireFormation, Onglets
from admission.ddd.admission.enums.emplacement_document import TypeDocument
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository
from osis_common.ddd.interface import EntityIdentity, ApplicationService, RootEntity


class EmplacementDocumentRepository(IEmplacementDocumentRepository):
    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        pass

    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        pass

    @classmethod
    def save_emplacement_document_gestionnaire(cls, document: EmplacementDocument):
        try:
            admission: BaseAdmission = BaseAdmission.objects.get(uuid=document.demande.uuid)

            # Save the metadata of the file
            from osis_document.api.utils import change_remote_metadata

            change_remote_metadata(
                token=document.uuids[0],
                metadata={
                    'explicit_name': document.libelle,
                    'author': document.auteur,
                },
            )

            # Save the file into the admission
            field_name = {
                TypeDocument.CANDIDAT_SIC: 'sic_documents',
                TypeDocument.CANDIDAT_FAC: 'fac_documents',
            }[document.type]

            getattr(admission, field_name).append(document.uuids[0])
            admission.save(update_fields=[field_name])

        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def save_emplacement_document_candidat(cls, entity: EmplacementDocument):
        cls.save_multiple_emplacements_documents_candidat(entities=[entity])

    @classmethod
    def save(cls, entity: EmplacementDocument) -> None:
        pass

    @classmethod
    def get(cls, entity_id: EntityIdentity) -> RootEntity:
        pass

    @classmethod
    def reinitialiser_emplacements_documents_candidat(
        cls,
        demande_identity: DemandeIdentity,
        entities: List[EmplacementDocument],
    ) -> None:
        try:
            admission: BaseAdmission = BaseAdmission.objects.get(uuid=demande_identity.uuid)

            # In the previous requested documents, only keep the free ones
            admission.requested_documents = {
                identifier: content
                for identifier, content in admission.requested_documents.items()
                if content.get('type') != TypeDocument.NON_LIBRE.name
            }

            # Add the documents requested by the system
            for entity in entities:
                admission.requested_documents[entity.entity_id.identifiant] = cls.get_requested_document_to_save(entity)

            admission.save(update_fields=['requested_documents'])

        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def get_requested_document_to_save(cls, entity: EmplacementDocument):
        return {
            'author': entity.auteur,
            'reason': entity.justification_gestionnaire,
            'type': entity.type.name,
            'last_action_at': entity.derniere_action_le,
            'status': entity.statut.name,
        }

    @classmethod
    def save_multiple_emplacements_documents_candidat(cls, entities: List[EmplacementDocument]) -> None:
        if not entities:
            return
        try:
            admission: BaseAdmission = BaseAdmission.objects.get(uuid=entities[0].demande.uuid)
            with transaction.atomic():

                for entity in entities:
                    # Create a specific question for each free document
                    if (
                        entity.type in {TypeDocument.CANDIDAT_SIC, TypeDocument.CANDIDAT_FAC}
                        and entity.entity_id.identifiant not in admission.requested_documents
                    ):
                        form_item = AdmissionFormItem(
                            internal_label=f'{admission.reference}.{slugify(entity.libelle)}',
                            type=TypeItemFormulaire.DOCUMENT.name,
                            title={language: entity.libelle for language in TRANSLATION_LANGUAGES},
                            uuid=entity.entity_id.identifiant.split('.')[-1],
                        )
                        form_item.save()
                        form_item_instantiation = (
                            AdmissionFormItemInstantiation(
                                form_item=form_item,
                                academic_year_id=admission.determined_academic_year_id,
                                weight=1,
                                required=True,
                                display_according_education=CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name,
                                admission=admission,
                                tab=Onglets.DOCUMENTS.name,
                            )
                        )
                        form_item_instantiation.save()

                    admission.requested_documents[entity.entity_id.identifiant] = cls.get_requested_document_to_save(entity)

                admission.save(update_fields=['requested_documents'])

        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def delete_emplacement_candidat(
        cls,
        entity_id: EmplacementDocumentIdentity,
        demande_entity_id: DemandeIdentity,
        type_document: TypeDocument,
    ) -> None:
        try:
            admission = BaseAdmission.objects.get(uuid=demande_entity_id.uuid)
            admission.requested_documents.pop(entity_id.identifiant)
            with transaction.atomic():
                if type_document in {TypeDocument.CANDIDAT_SIC, TypeDocument.CANDIDAT_FAC}:
                    # For free documents, also delete the specific question
                    specific_question_uuid = entity_id.identifiant.split('.')[-1]
                    form_item_instantiation_to_delete = AdmissionFormItemInstantiation.objects.filter(form_item__uuid=specific_question_uuid).first()
                    related_form_item = form_item_instantiation_to_delete.form_item
                    form_item_instantiation_to_delete.delete()
                    related_form_item.delete()

                admission.save(update_fields=['requested_documents'])

        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException
