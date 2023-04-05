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

from django.db import models
from django.utils.translation import get_language

from admission.contrib.models import AdmissionFormItemInstantiation
from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.domain.model.question_specifique import QuestionSpecifique, QuestionSpecifiqueIdentity

from admission.ddd.admission.domain.service.i_question_specifique import ISuperQuestionSpecifiqueTranslator
from admission.ddd.admission.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.enums import TYPES_ITEMS_LECTURE_SEULE
from admission.ddd.admission.enums.question_specifique import (
    Onglets,
    TypeItemFormulaire,
)
from admission.utils import get_uuid_value


class SuperQuestionSpecifiqueTranslator(ISuperQuestionSpecifiqueTranslator):
    admission_model = BaseAdmission

    @classmethod
    def get_admission(cls, proposition_uuid):
        try:
            return cls.admission_model.objects.select_related(
                'training',
                'candidate__country_of_citizenship',
                'candidate__belgianhighschooldiploma',
                'candidate__foreignhighschooldiploma__linguistic_regime',
            ).get(uuid=proposition_uuid)
        except cls.admission_model.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def search_by_proposition(
        cls,
        proposition_uuid: str,
        onglets: List[str] = None,
    ) -> List['QuestionSpecifique']:
        return [
            QuestionSpecifique(
                entity_id=QuestionSpecifiqueIdentity(uuid=question.form_item.uuid),
                type=TypeItemFormulaire[question.form_item.type],
                requis=question.required,
                onglet=Onglets[question.tab],
                configuration=question.form_item.configuration,
            )
            for question in AdmissionFormItemInstantiation.objects.form_items_by_admission(
                admission=cls.get_admission(proposition_uuid),
                tabs=onglets,
                required=True,
            )
        ]

    @classmethod
    def build_dto(cls, question: AdmissionFormItemInstantiation, answers, language: str) -> QuestionSpecifiqueDTO:
        question_uuid = str(question.form_item.uuid)
        question_type = question.form_item.type

        if question_type in TYPES_ITEMS_LECTURE_SEULE:
            formatted_value = question.form_item.text.get(language, '')
        elif question_type == TypeItemFormulaire.DOCUMENT.name:
            formatted_value = [get_uuid_value(token) for token in answers.get(question_uuid, [])]
        elif question_type == TypeItemFormulaire.SELECTION.name:
            current_value = answers.get(question_uuid)
            selected_options = set(current_value) if isinstance(current_value, list) else {current_value}
            formatted_value = ', '.join(
                [value.get(language) for value in question.form_item.values if value.get('key') in selected_options]
            )
        else:
            formatted_value = answers.get(question_uuid, '')

        return QuestionSpecifiqueDTO(
            uuid=question_uuid,
            type=question.form_item.type,
            requis=question.required,
            onglet=question.tab,
            configuration=question.form_item.configuration,
            label=question.form_item.title.get(language, ''),
            valeur=answers.get(question_uuid),
            valeur_formatee=formatted_value,
        )

    @classmethod
    def search_dto_by_proposition(
        cls,
        proposition_uuid: str,
        onglets: List[str] = None,
        type: str = None,
        requis: bool = None,
    ) -> List['QuestionSpecifiqueDTO']:
        current_language = get_language()
        admission = cls.get_admission(proposition_uuid)
        return [
            cls.build_dto(question, admission.specific_question_answers, current_language)
            for question in AdmissionFormItemInstantiation.objects.form_items_by_admission(
                admission=admission,
                tabs=onglets,
                required=requis,
                form_item_type=type,
            ).order_by('display_according_education', 'weight')
        ]
