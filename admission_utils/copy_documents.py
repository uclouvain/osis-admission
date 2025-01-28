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
import uuid


def copy_documents(objs):
    """
    Create copies of the files of the specified objects and affect them to the specified objects.
    :param objs: The list of objects.
    """
    from osis_document.api.utils import get_several_remote_metadata, get_remote_tokens, documents_remote_duplicate
    from osis_document.contrib import FileField
    from osis_document.utils import generate_filename

    all_document_uuids = []
    all_document_upload_paths = {}
    document_fields_by_obj_uuid = {}

    # Get all the document fields and the uuids of the documents to duplicate
    for obj in objs:
        document_fields_by_obj_uuid[obj.uuid] = {}

        for field in obj._meta.get_fields():
            if isinstance(field, FileField):
                document_uuids = getattr(obj, field.name)

                if document_uuids:
                    document_fields_by_obj_uuid[obj.uuid][field.name] = field
                    all_document_uuids += [document_uuid for document_uuid in document_uuids if document_uuid]

    all_tokens = get_remote_tokens(all_document_uuids)
    metadata_by_token = get_several_remote_metadata(tokens=list(all_tokens.values()))

    # Get the upload paths of the documents to duplicate
    for obj in objs:
        for field_name, field in document_fields_by_obj_uuid[obj.uuid].items():
            document_uuids = getattr(obj, field_name)

            for document_uuid in document_uuids:
                if not document_uuid:
                    continue

                document_uuid_str = str(document_uuid)
                file_name = 'file'

                if document_uuid_str in all_tokens and all_tokens[document_uuid_str] in metadata_by_token:
                    metadata = metadata_by_token[all_tokens[document_uuid_str]]
                    if metadata.get('name'):
                        file_name = metadata['name']

                all_document_upload_paths[document_uuid_str] = generate_filename(obj, file_name, field.upload_to)

    # Make a copy of the documents and return the uuids of the copied documents
    duplicates_documents_uuids = documents_remote_duplicate(
        uuids=all_document_uuids,
        with_modified_upload=True,
        upload_path_by_uuid=all_document_upload_paths,
    )

    # Update the uuids of the documents with the uuids of the copied documents
    for obj in objs:
        for field_name in document_fields_by_obj_uuid[obj.uuid]:
            setattr(
                obj,
                field_name,
                [
                    uuid.UUID(duplicates_documents_uuids[str(document_uuid)])
                    for document_uuid in getattr(obj, field_name)
                    if duplicates_documents_uuids.get(str(document_uuid))
                ],
            )
