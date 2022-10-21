##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from typing import List, Optional

from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_continue.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.formation_continue.domain.validator.exceptions import PropositionNonTrouveeException
from admission.infrastructure.admission.domain.service.in_memory.question_specifique import (
    SuperQuestionSpecifiqueInMemoryTranslator,
)
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)


class QuestionSpecifiqueInMemoryTranslator(IQuestionSpecifiqueTranslator, SuperQuestionSpecifiqueInMemoryTranslator):
    proposition_repository = PropositionInMemoryRepository

    @classmethod
    def _search_by_proposition_qs(
        cls,
        proposition_uuid: str,
        onglets: List[str] = None,
        type: Optional[str] = None,
        requis: Optional[bool] = None,
    ):
        try:
            proposition = cls.proposition_repository.get(PropositionIdentity(uuid=proposition_uuid))
        except PropositionNonTrouveeException:
            return []

        return [
            entity
            for entity in cls.entities
            if entity.formation.annee == proposition.formation_id.annee
            and entity.formation.sigle == proposition.formation_id.sigle
            and (not onglets or entity.onglet in onglets)
            and (not type or entity.type == type)
            and (not requis or entity.requis == requis)
        ]
