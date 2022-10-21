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

from admission.contrib.models import AdmissionFormItemInstantiation
from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.domain.model.question_specifique import QuestionSpecifique, QuestionSpecifiqueIdentity

from admission.ddd.admission.domain.service.i_question_specifique import ISuperQuestionSpecifiqueTranslator
from admission.ddd.admission.enums.question_specifique import (
    Onglets,
    TypeItemFormulaire,
)


class SuperQuestionSpecifiqueTranslator(ISuperQuestionSpecifiqueTranslator):
    admission_model = BaseAdmission

    @classmethod
    def _search_form_item_instantiation_by_proposition(
        cls,
        proposition_uuid: str,
        onglets: List[str] = None,
        type: Optional[str] = None,
        requis: Optional[bool] = None,
    ) -> models.QuerySet[AdmissionFormItemInstantiation]:

        admission = cls.admission_model.objects.select_related(
            'training',
            'candidate__country_of_citizenship',
            'candidate__belgianhighschooldiploma',
            'candidate__foreignhighschooldiploma__linguistic_regime',
        ).get(uuid=proposition_uuid)

        return AdmissionFormItemInstantiation.objects.form_items_by_admission(
            admission=admission,
            tabs=onglets,
            form_item_type=type,
            required=requis,
        )

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
            for question in cls._search_form_item_instantiation_by_proposition(
                proposition_uuid=proposition_uuid,
                onglets=onglets,
                requis=True,
            )
        ]
