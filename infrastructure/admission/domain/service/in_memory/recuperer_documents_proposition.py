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
from typing import List

from admission.constants import PDF_MIME_TYPE
from admission.ddd.admission.domain.service.i_emplacements_documents_proposition import (
    IEmplacementsDocumentsPropositionTranslator,
)


class EmplacementsDocumentsPropositionInMemoryTranslator(IEmplacementsDocumentsPropositionTranslator):
    metadata = {
        'file1.pdf': {
            'mimetype': PDF_MIME_TYPE,
            'author': '',
            'uploaded_at': '2023-01-01T00:00:00',
        },
        '24de0c3d-3c06-4c93-8eb4-c8648f04f144': {
            'mimetype': PDF_MIME_TYPE,
            'author': '00321234',
            'uploaded_at': '2023-01-04T00:00:00',
        },
        '24de0c3d-3c06-4c93-8eb4-c8648f04f140': {
            'mimetype': PDF_MIME_TYPE,
            'explicit_name': 'My candidate sic file',
            'author': '00987890',
            'uploaded_at': '2023-01-05T00:00:00',
        },
        '24de0c3d-3c06-4c93-8eb4-c8648f04f141': {
            'mimetype': PDF_MIME_TYPE,
            'explicit_name': 'My candidate fac file',
            'author': '00321234',
            'uploaded_at': '2023-01-01T00:00:00',
        },
        '24de0c3d-3c06-4c93-8eb4-c8648f04f142': {
            'mimetype': PDF_MIME_TYPE,
            'explicit_name': 'My uclouvain sic file',
            'author': '00987890',
            'uploaded_at': '2023-01-02T00:00:00',
        },
        '24de0c3d-3c06-4c93-8eb4-c8648f04f143': {
            'mimetype': PDF_MIME_TYPE,
            'explicit_name': 'My uclouvain fac file',
            'author': '00321234',
            'uploaded_at': '2023-01-03T00:00:00',
        },
    }

    @classmethod
    def recuperer_metadonnees_par_uuid_document(cls, uuids_documents: List[str]) -> dict:
        return {uuid: cls.metadata.get(uuid, {}) for uuid in uuids_documents}
