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
from typing import List

from admission.ddd.admission.shared_kernel.domain.service.i_emplacements_documents_proposition import (
    IEmplacementsDocumentsPropositionTranslator,
)
from admission.ddd.admission.shared_kernel.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.shared_kernel.dtos.resume import ResumePropositionDTO
from admission.exports.admission_recap.section import get_sections
from base.forms.utils.file_field import PDF_MIME_TYPE


class EmplacementsDocumentsPropositionInMemoryTranslator(IEmplacementsDocumentsPropositionTranslator):
    metadata = {
        'file1.pdf': {
            'mimetype': PDF_MIME_TYPE,
            'author': '',
            'uploaded_at': '2023-01-01T00:00:00',
        },
        'uuid12': {
            'mimetype': PDF_MIME_TYPE,
            'author': '',
            'uploaded_at': '2023-01-01T00:00:00',
        },
        '24de0c3d-3c06-4c93-8eb4-c8648f04f144': {
            'mimetype': PDF_MIME_TYPE,
            'author': '00321234',
            'uploaded_at': '2023-01-04T00:00:00',
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
        'file_token.pdf': {
            'mimetype': PDF_MIME_TYPE,
            'author': '',
            'uploaded_at': '2023-01-01T00:00:00',
        },
    }

    @classmethod
    def recuperer_metadonnees_par_uuid_document(cls, uuids_documents: List[str]) -> dict:
        return {uuid: cls.metadata.get(uuid, {}) for uuid in uuids_documents}

    @classmethod
    def get_sections(
        cls,
        resume_dto: ResumePropositionDTO,
        questions_specifiques: List[QuestionSpecifiqueDTO],
        avec_documents_libres: bool,
    ) -> dict:
        return get_sections(
            context=resume_dto,
            specific_questions=questions_specifiques,
            with_free_requestable_documents=avec_documents_libres,
        )
