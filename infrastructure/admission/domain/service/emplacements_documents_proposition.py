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

from admission.ddd.admission.domain.service.i_emplacements_documents_proposition import (
    IEmplacementsDocumentsPropositionTranslator,
)


class EmplacementsDocumentsPropositionTranslator(IEmplacementsDocumentsPropositionTranslator):
    @classmethod
    def recuperer_metadonnees_par_uuid_document(cls, uuids_documents: List[str]) -> dict:
        from osis_document.api.utils import get_remote_tokens, get_several_remote_metadata

        tokens = get_remote_tokens(uuids_documents)
        metadata = get_several_remote_metadata(list(tokens.values()))

        return {
            uuid: metadata[tokens[uuid]] if uuid in tokens and tokens[uuid] in metadata else {}
            for uuid in uuids_documents
        }
