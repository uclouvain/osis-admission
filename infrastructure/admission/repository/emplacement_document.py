# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from itertools import chain
from typing import List, Optional, Set, Union

from django.conf import settings
from django.db import transaction
from django.db.models import Case, F, OuterRef, Q, Subquery, UUIDField, When
from django.utils.dateparse import parse_date, parse_datetime

from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist as OngletsChecklistDoctorat,
)
from admission.ddd.admission.domain.model.emplacement_document import (
    EmplacementDocument,
    EmplacementDocumentIdentity,
)
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.validator.exceptions import (
    EmplacementDocumentNonTrouveException,
    PropositionNonTrouveeException,
)
from admission.ddd.admission.enums import (
    CritereItemFormulaireFormation,
    Onglets,
    TypeItemFormulaire,
)
from admission.ddd.admission.enums.emplacement_document import (
    EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES,
    EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES,
    EMPLACEMENTS_DOCUMENTS_RECLAMABLES,
    IDENTIFIANT_BASE_EMPLACEMENT_DOCUMENT_LIBRE_PAR_TYPE,
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
    TypeEmplacementDocument,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    OngletsChecklist as OngletsChecklistContinue,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    OngletsChecklist as OngletsChecklistGenerale,
)
from admission.ddd.admission.repository.i_emplacement_document import (
    IEmplacementDocumentRepository,
)
from admission.infrastructure.utils import (
    AdmissionDocument,
    get_document_from_identifier,
)
from admission.models import (
    AdmissionFormItem,
    AdmissionFormItemInstantiation,
    ContinuingEducationAdmission,
    DoctorateAdmission,
    GeneralEducationAdmission,
)
from admission.models.base import BaseAdmission
from admission.models.epc_injection import EPCInjectionStatus, EPCInjectionType
from admission.services.injection_epc.injection_dossier import (
    EPCInjection as DemandeEPCInjection,
)
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person
from osis_profile.models import OSIS_PROFILE_MODELS, Exam
from osis_profile.models.enums.exam import ExamTypes
from osis_profile.models.epc_injection import EPCInjection as CurriculumEPCInjection
from osis_profile.models.epc_injection import (
    EPCInjectionStatus as CurriculumEPCInjectionStatus,
)
from osis_profile.services.injection_epc import InjectionEPCCurriculum


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
            # In case we have several fields on the same object, we need to update them on a single instance.
            model_objects_cache = {}
            for entity in entities:
                if entity.type.name not in EMPLACEMENTS_DOCUMENTS_RECLAMABLES:
                    raise NotImplementedError

                elif entity.type.name in EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES:
                    uuid_value = entity.entity_id.identifiant.split('.')[-1]
                    if entity.entity_id.identifiant not in admission.requested_documents:
                        # Create a specific question for each new free document
                        form_item = AdmissionFormItem(
                            internal_label=f'{admission.reference}.{uuid_value}',
                            type=TypeItemFormulaire.DOCUMENT.name,
                            title={
                                settings.LANGUAGE_CODE_FR: entity.libelle_fr or entity.libelle,
                                settings.LANGUAGE_CODE_EN: entity.libelle_en or entity.libelle,
                            },
                            uuid=uuid_value,
                        )
                        form_item.save()
                        form_item_instantiation = AdmissionFormItemInstantiation(
                            form_item=form_item,
                            academic_year_id=admission.determined_academic_year_id,
                            weight=1,
                            required=False,
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
                if model_object in model_objects_cache:
                    model_object = model_objects_cache[model_object]
                else:
                    model_objects_cache[model_object] = model_object
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
                    if entity.uuids_documents:
                        change_remote_metadata(
                            token=entity.uuids_documents[0],
                            metadata={
                                'author': entity.document_soumis_par,
                            },
                        )

            experiences_injectees_uuid_set = cls._retrieve_experiences_uuid_set(admission.candidate_id)

            for model_object, fields in updated_fields_by_object.items():
                # Ensure the files are not deleted by osis_document.contrib.fields.FileField.pre_save
                model_object._files_to_keep = [
                    uuid_document
                    for entity in entities
                    for uuid_document in entity.uuids_documents
                    if isinstance(uuid_document, uuid.UUID)
                ]
                model_object.save(update_fields=fields)
                if isinstance(model_object, OSIS_PROFILE_MODELS):
                    vient_d_epc = bool(getattr(model_object, 'external_id', ''))
                    object_uuid = getattr(model_object, 'educational_experience_uuid', model_object.uuid)
                    deja_injectee = object_uuid in experiences_injectees_uuid_set
                    if vient_d_epc or deja_injectee:
                        InjectionEPCCurriculum().injecter_selon_modele(
                            model_object,
                            admission.candidate,
                            admission.last_update_author,
                        )

    @classmethod
    def _retrieve_experiences_uuid_set(cls, candidate_id: int) -> Set[uuid.UUID]:
        curriculum_injections = CurriculumEPCInjection.objects.filter(
            person_id=candidate_id,
            status__in=CurriculumEPCInjectionStatus.blocking_statuses_for_experience(),
        ).values_list('experience_uuid', flat=True)

        common_filter = Q(
            type=EPCInjectionType.DEMANDE.name,
            admission__candidate_id=candidate_id,
            status__in=EPCInjectionStatus.blocking_statuses_for_experience(),
        )
        educational_uuids = (
            DemandeEPCInjection.objects.filter(common_filter)
            .annotate(experience_uuid=F('admission__admissioneducationalvaluatedexperiences__educationalexperience_id'))
            .exclude(experience_uuid__isnull=True)
            .values_list('experience_uuid', flat=True)
        )
        professional_uuids = (
            DemandeEPCInjection.objects.filter(common_filter)
            .annotate(
                experience_uuid=F('admission__admissionprofessionalvaluatedexperiences__professionalexperience_id')
            )
            .exclude(experience_uuid__isnull=True)
            .values_list('experience_uuid', flat=True)
        )
        secondaires_uuids = (
            DemandeEPCInjection.objects.filter(
                common_filter,
                admission__training__education_group_type__name=TrainingType.BACHELOR.name,
            )
            .annotate(
                exam_secondary=Subquery(
                    Exam.objects.filter(
                        type=ExamTypes.PREMIER_CYCLE.name,
                        person=OuterRef('admission__candidate'),
                    ).values('uuid')[:1]
                ),
                experience_uuid=Case(
                    When(
                        admission__candidate__belgianhighschooldiploma__isnull=False,
                        then=F('admission__candidate__belgianhighschooldiploma__uuid'),
                    ),
                    When(
                        admission__candidate__foreignhighschooldiploma__isnull=False,
                        then=F('admission__candidate__foreignhighschooldiploma__uuid'),
                    ),
                    When(
                        exam_secondary__isnull=False,
                        then=F('exam_secondary'),
                    ),
                    output_field=UUIDField(),
                ),
            )
            .exclude(experience_uuid__isnull=True)
            .values_list('experience_uuid', flat=True)
        )
        demande_injections = list(chain(educational_uuids, professional_uuids, secondaires_uuids))

        return set(curriculum_injections) | set(demande_injections)

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
            'request_status': entity.statut_reclamation.name if entity.statut_reclamation else '',
            'related_checklist_tab': entity.onglet_checklist_associe.name if entity.onglet_checklist_associe else '',
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
            libelle_fr=emplacement_document.label_fr,
            libelle_en=emplacement_document.label_en,
            reclame_le=parse_datetime(emplacement_document.requested_at) if emplacement_document.requested_at else None,
            a_echeance_le=parse_date(emplacement_document.deadline_at) if emplacement_document.deadline_at else None,
            derniere_action_le=(
                parse_datetime(emplacement_document.last_action_at) if emplacement_document.last_action_at else None
            ),
            dernier_acteur=emplacement_document.last_actor,
            requis_automatiquement=emplacement_document.automatically_required,
            document_soumis_par=emplacement_document.document_submitted_by,
            statut_reclamation=(
                StatutReclamationEmplacementDocument[emplacement_document.request_status]
                if emplacement_document.request_status
                else None
            ),
            onglet_checklist_associe=(
                next(
                    (
                        enum[emplacement_document.related_checklist_tab]
                        for enum in [OngletsChecklistGenerale, OngletsChecklistContinue, OngletsChecklistDoctorat]
                        if hasattr(enum, emplacement_document.related_checklist_tab)
                    ),
                    None,
                )
                if emplacement_document.related_checklist_tab
                else None
            ),
        )

    @classmethod
    def reinitialiser_emplacements_documents_non_libres(
        cls,
        proposition_identity: PropositionIdentity,
        identifiants_documents_pertinents: Set[str],
    ) -> None:
        admission = cls.get_admission(entity_id=proposition_identity)

        # Remove the non-free documents that are no longer relevant to the admission
        for requested_document_identifier in list(admission.requested_documents.keys()):
            current_document = admission.requested_documents[requested_document_identifier]

            if current_document['type'] == TypeEmplacementDocument.NON_LIBRE.name:
                if requested_document_identifier not in identifiants_documents_pertinents:
                    del admission.requested_documents[requested_document_identifier]

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
