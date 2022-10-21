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
import abc
from typing import List, Optional

import attr

from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.domain.model.question_specifique import QuestionSpecifique, QuestionSpecifiqueIdentity

from admission.ddd.admission.domain.service.i_question_specifique import ISuperQuestionSpecifiqueTranslator
from admission.ddd.admission.enums.question_specifique import (
    Onglets,
    TypeItemFormulaire,
)


@attr.dataclass(slots=True)
class QuestionSpecifiqueEtendue(QuestionSpecifique):
    formation: FormationIdentity


class SuperQuestionSpecifiqueInMemoryTranslator(ISuperQuestionSpecifiqueTranslator):
    proposition_repository = None

    entities = [
        QuestionSpecifiqueEtendue(
            entity_id=QuestionSpecifiqueIdentity(uuid='06de0c3d-3c06-4c93-8eb4-c8648f04f140'),
            type=TypeItemFormulaire.TEXTE,
            requis=True,
            configuration={},
            onglet=Onglets.CHOIX_FORMATION,
            formation=FormationIdentity(sigle='SC3DP', annee=2020),
        ),
        QuestionSpecifiqueEtendue(
            entity_id=QuestionSpecifiqueIdentity(uuid="06de0c3d-3c06-4c93-8eb4-c8648f04f141"),
            type=TypeItemFormulaire.TEXTE,
            requis=False,
            configuration={},
            onglet=Onglets.CHOIX_FORMATION,
            formation=FormationIdentity(sigle='SC3DP', annee=2020),
        ),
        QuestionSpecifiqueEtendue(
            entity_id=QuestionSpecifiqueIdentity(uuid="06de0c3d-3c06-4c93-8eb4-c8648f04f142"),
            type=TypeItemFormulaire.TEXTE,
            requis=True,
            configuration={},
            onglet=Onglets.CURRICULUM,
            formation=FormationIdentity(sigle='SC3DP', annee=2020),
        ),
        QuestionSpecifiqueEtendue(
            entity_id=QuestionSpecifiqueIdentity(uuid="06de0c3d-3c06-4c93-8eb4-c8648f04f143"),
            type=TypeItemFormulaire.TEXTE,
            requis=True,
            configuration={},
            onglet=Onglets.ETUDES_SECONDAIRES,
            formation=FormationIdentity(sigle='SC3DP', annee=2020),
        ),
    ]

    @classmethod
    @abc.abstractmethod
    def _search_by_proposition_qs(
        cls,
        proposition_uuid: str,
        onglets: List[str] = None,
        type: Optional[str] = None,
        requis: Optional[bool] = None,
    ):
        raise NotImplementedError

    @classmethod
    def search_by_proposition(
        cls,
        proposition_uuid: str,
        onglets: List[str] = None,
    ) -> List['QuestionSpecifique']:
        return [
            QuestionSpecifique(
                entity_id=question.entity_id,
                type=question.type,
                requis=question.requis,
                onglet=question.onglet,
                configuration=question.configuration,
            )
            for question in cls._search_by_proposition_qs(
                proposition_uuid=proposition_uuid,
                onglets=onglets,
                requis=True,
            )
        ]
