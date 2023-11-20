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
from typing import List, Dict

import attr

from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument
from admission.ddd.admission.domain.validator.exceptions import DocumentsCompletesDifferentsDesReclamesException
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldCompleterTousLesDocumentsReclames(BusinessValidator):
    documents_reclames: List[EmplacementDocument]
    reponses_documents_a_completer: Dict[str, List[str]]

    def validate(self, *args, **kwargs):
        if len(self.documents_reclames) != len(self.reponses_documents_a_completer) or any(
            document
            for document in self.documents_reclames
            if not self.reponses_documents_a_completer.get(document.entity_id.identifiant)
        ):
            raise DocumentsCompletesDifferentsDesReclamesException
