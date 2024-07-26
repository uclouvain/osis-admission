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

import os.path
import uuid
from collections import defaultdict
from typing import List

from django.db import transaction
from django.utils.text import slugify
from osis_document.enums import PostProcessingType

from admission.models import (
    AdmissionTask,
    ContinuingEducationAdmission,
    DoctorateAdmission,
    GeneralEducationAdmission,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    RecupererDocumentsPropositionQuery as RecupererDocumentsPropositionDoctoraleQuery,
)
from admission.ddd.admission.domain.validator.exceptions import EmplacementDocumentNonTrouveException
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import DOCUMENTS_A_NE_PAS_CONVERTIR_A_LA_SOUMISSION
from admission.ddd.admission.formation_continue.commands import (
    RecupererDocumentsPropositionQuery as RecupererDocumentsPropositionContinueQuery,
)
from admission.ddd.admission.formation_generale.commands import (
    RecupererDocumentsPropositionQuery as RecupererDocumentsPropositionGeneraleQuery,
)
from admission.exceptions import DocumentPostProcessingException, InvalidMimeTypeException, MergeDocumentsException
from admission.infrastructure.utils import get_document_from_identifier
from base.forms.utils.file_field import PDF_MIME_TYPE
from infrastructure.messages_bus import message_bus_instance


def base_education_admission_document_merging(admission):
    """Merging of each document field of the proposition into one PDF."""
    from osis_document.api.utils import launch_post_processing

    command = {
        GeneralEducationAdmission: RecupererDocumentsPropositionGeneraleQuery,
        ContinuingEducationAdmission: RecupererDocumentsPropositionContinueQuery,
        DoctorateAdmission: RecupererDocumentsPropositionDoctoraleQuery,
    }[admission.__class__]

    # Load all documents related to the admission
    documents: List[EmplacementDocumentDTO] = message_bus_instance.invoke(command(uuid_proposition=admission.uuid))

    results = {}

    # If necessary, merge each document field of the proposition into one PDF
    for updated_document in documents:
        post_processing_types = []
        post_processing_params = {
            PostProcessingType.MERGE.name: {},
            PostProcessingType.CONVERT.name: {},
        }

        # Some fields must not be merged
        if (
            not updated_document.est_reclamable
            or not updated_document.document_uuids
            or updated_document.identifiant in DOCUMENTS_A_NE_PAS_CONVERTIR_A_LA_SOUMISSION
        ):
            continue

        if any(mimetype != PDF_MIME_TYPE for mimetype in updated_document.types_documents.values()):
            # If the file is not a PDF, convert it
            post_processing_types.append(PostProcessingType.CONVERT.name)

        if len(updated_document.document_uuids) > 1:
            # If there is more than one file, merge them
            post_processing_types.append(PostProcessingType.MERGE.name)
            filename = slugify(updated_document.libelle_langue_candidat)
            post_processing_params[PostProcessingType.MERGE.name]['output_filename'] = f'{filename}.pdf'
        elif post_processing_types:
            # If there is only one file which is not a PDF, convert it
            filename, _ = os.path.splitext(next(iter(updated_document.noms_documents_televerses.values())))
            post_processing_params[PostProcessingType.CONVERT.name]['output_filename'] = f'{filename}.pdf'

        if post_processing_types:
            results[updated_document.identifiant] = launch_post_processing(
                uuid_list=updated_document.document_uuids,
                post_processing_types=post_processing_types,
                post_process_params=post_processing_params,
                async_post_processing=False,
            )

    updated_fields_by_object = defaultdict(list)
    document_exceptions = {}

    # Update the models whose some document fields have been merged
    with transaction.atomic():
        for identifier, result in results.items():
            # An error occurred during the post processing
            if result.get('error'):
                document_exceptions[identifier] = DocumentPostProcessingException(result['error'])
                continue

            updated_document = get_document_from_identifier(admission, identifier)

            # The related field has not been found
            if not updated_document:
                document_exceptions[identifier] = EmplacementDocumentNonTrouveException
                continue

            # The PDF type is not one of the mimetypes of the related field
            if PDF_MIME_TYPE not in updated_document.mimetypes:
                document_exceptions[identifier] = InvalidMimeTypeException(
                    field=identifier,
                    field_mimetypes=updated_document.mimetypes,
                    current_mimetype=PDF_MIME_TYPE,
                )
                continue

            model_object = updated_document.obj
            model_field = updated_document.field
            specific_question_uuid = updated_document.specific_question_uuid

            new_document_uuids = [
                uuid.UUID(
                    result[
                        PostProcessingType.MERGE.name
                        if result[PostProcessingType.MERGE.name].get('output')
                        else PostProcessingType.CONVERT.name
                    ]['output']['upload_objects'][0]
                )
            ]

            updated_fields_by_object[model_object].append(model_field)

            if specific_question_uuid:
                # For a specific question, replace the previous file
                admission.specific_question_answers[specific_question_uuid] = new_document_uuids
            else:
                # Otherwise, update the related field in the specific object
                setattr(model_object, model_field, new_document_uuids)

        for model_object, fields in updated_fields_by_object.items():
            model_object.save(update_fields=fields)

    if document_exceptions:
        raise MergeDocumentsException(document_exceptions)


def general_education_admission_document_merging_from_task(task_uuid: str):
    """Merging of each document field of a general education proposition into one PDF."""
    task = AdmissionTask.objects.select_related(f'admission__generaleducationadmission').get(task__uuid=task_uuid)
    base_education_admission_document_merging(admission=task.admission.generaleducationadmission)


def continuing_education_admission_document_merging_from_task(task_uuid: str):
    """Merging of each document field of a continuing education proposition into one PDF."""
    task = AdmissionTask.objects.select_related(f'admission__continuingeducationadmission').get(task__uuid=task_uuid)
    base_education_admission_document_merging(admission=task.admission.continuingeducationadmission)


def doctorate_education_admission_document_merging_from_task(task_uuid: str):
    """Merging of each document field of a doctorate education proposition into one PDF."""
    task = AdmissionTask.objects.select_related(f'admission__doctorateadmission').get(task__uuid=task_uuid)
    base_education_admission_document_merging(admission=task.admission.doctorateadmission)
