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
from admission.ddd.admission.domain.model.document import Document
from admission.ddd.admission.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.enums import TypeItemFormulaire, CritereItemFormulaireFormation, Onglets
from admission.ddd.admission.enums.document import TypeDocument, DocumentsInterOnglets
from admission.ddd.admission.repository.i_document import IDocumentRepository
from osis_common.ddd.interface import EntityIdentity, ApplicationService, RootEntity


class DocumentRepository(IDocumentRepository):
    @classmethod
    def get(cls, entity_id: EntityIdentity) -> RootEntity:
        pass

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        pass

    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        pass

    @classmethod
    def save_document_gestionnaire(cls, document: Document):
        try:
            admission: BaseAdmission = BaseAdmission.objects.get(uuid=document.proposition.uuid)

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
    def save_document_candidat(cls, document: Document):
        try:
            with transaction.atomic():
                admission: BaseAdmission = BaseAdmission.objects.get(uuid=document.proposition.uuid)

                # Create a specific question related to the admission
                form_item = AdmissionFormItem.objects.create(
                    internal_label=f'{admission.reference}.{slugify(document.libelle)}',
                    type=TypeItemFormulaire.DOCUMENT.name,
                    title={language: document.libelle for language in TRANSLATION_LANGUAGES},
                    uuid=document.entity_id.identifiant.split('.')[-1],
                )
                AdmissionFormItemInstantiation.objects.create(
                    form_item=form_item,
                    academic_year_id=admission.determined_academic_year_id,
                    weight=1,
                    required=True,
                    display_according_education=CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name,
                    admission=admission,
                    tab=Onglets.DOCUMENTS.name,
                )

                # Save information about the request
                admission.requested_documents[
                    f'{DocumentsInterOnglets.QUESTION_SPECIFIQUE.name}.{str(form_item.uuid)}'
                ] = {
                    'author': document.auteur,
                    'reason': document.justification_gestionnaire,
                    'type': document.type.name,
                    'last_action_at': document.derniere_action_le,
                }
                admission.save(update_fields=['requested_documents'])

        except BaseAdmission.DoesNotExist:
            raise PropositionNonTrouveeException
