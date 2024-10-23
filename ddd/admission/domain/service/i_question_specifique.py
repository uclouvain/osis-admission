##############################################################################
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
##############################################################################
from typing import List, Dict

from typing_extensions import Union

from admission.ddd.admission.domain.model.question_specifique import QuestionSpecifique
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.enums import TypeItemFormulaire, TYPES_ITEMS_LECTURE_SEULE
from osis_common.ddd import interface


class ISuperQuestionSpecifiqueTranslator(interface.DomainService):
    @classmethod
    def search_by_proposition(
        cls,
        proposition_uuid: str,
        onglets: List[str] = None,
    ) -> List['QuestionSpecifique']:
        raise NotImplementedError

    @classmethod
    def search_dto_by_proposition(
        cls,
        proposition_uuid: str,
        onglets: List[str] = None,
        type: str = None,
        requis: bool = None,
    ) -> List['QuestionSpecifiqueDTO']:
        raise NotImplementedError

    @classmethod
    def clean_specific_question_answers(
        cls,
        questions: List[QuestionSpecifique],
        answers: Dict[str, Union[str, List[str]]],
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Clean specific question answers by keeping only the answers to the given specific questions.
        :param questions: The list of specific questions.
        :param answers: The answers to clean.
        :return: A dictionary containing only the answers to the given specific questions.
        """
        interesting_answers = {}

        for question in questions:
            if question.type.name in TYPES_ITEMS_LECTURE_SEULE:
                continue

            question_uuid = str(question.entity_id.uuid)

            if question_uuid in answers:
                interesting_answers[question_uuid] = answers[question_uuid]

            else:
                if question.type == TypeItemFormulaire.DOCUMENT:
                    interesting_answers[question_uuid] = []
                else:
                    interesting_answers[question_uuid] = ''

        return interesting_answers
