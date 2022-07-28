# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

import attr

from admission.ddd.projet_doctoral.preparation.domain.model._enums import TypeItemFormulaire
from base.ddd.utils.converters import to_upper_case_converter
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class QuestionSpecifiqueIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True)
class QuestionSpecifique(interface.Entity):
    entity_id: QuestionSpecifiqueIdentity
    type: TypeItemFormulaire
    poids: int
    supprimee: bool
    label_interne: str
    requis: bool
    titre: dict
    texte: dict
    texte_aide: dict
    configuration: dict


@attr.dataclass(frozen=True, slots=True)
class ListeDesQuestionsSpecifiquesDeLaFormationIdentity(interface.EntityIdentity):
    sigle: str = attr.ib(converter=to_upper_case_converter)
    annee: int


@attr.dataclass(slots=True)
class ListeDesQuestionsSpecifiquesDeLaFormation(interface.RootEntity):
    entity_id: ListeDesQuestionsSpecifiquesDeLaFormationIdentity
    questions: List[QuestionSpecifique] = []
