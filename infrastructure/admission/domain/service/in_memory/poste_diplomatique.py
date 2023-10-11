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
from typing import Optional, List

from admission.ddd.admission.domain.model.poste_diplomatique import PosteDiplomatiqueIdentity
from admission.ddd.admission.domain.service.i_poste_diplomatique import IPosteDiplomatiqueTranslator
from admission.ddd.admission.domain.validator.exceptions import PosteDiplomatiqueNonTrouveException
from admission.ddd.admission.dtos.poste_diplomatique import PosteDiplomatiqueDTO
from admission.ddd.admission.test.factory.poste_diplomatique import PosteDiplomatique, PosteDiplomatiqueFactory


class PosteDiplomatiqueInMemoryTranslator(IPosteDiplomatiqueTranslator):
    entities: List[PosteDiplomatique]

    @classmethod
    def get(cls, code: Optional[int]) -> Optional[PosteDiplomatiqueIdentity]:
        if code is not None:
            entity = next((entity for entity in cls.entities if entity.code == code), None)
            if entity:
                return PosteDiplomatiqueIdentity(code=entity.code)
            else:
                raise PosteDiplomatiqueNonTrouveException

    @classmethod
    def get_dto(cls, code: int) -> PosteDiplomatiqueDTO:
        entity = next((entity for entity in cls.entities if entity.code == code), None)
        if entity:
            return cls.build_dto(entity)
        else:
            raise PosteDiplomatiqueNonTrouveException

    @classmethod
    def build_dto(cls, diplomatic_post: PosteDiplomatique) -> PosteDiplomatiqueDTO:
        return PosteDiplomatiqueDTO(
            nom_francais=diplomatic_post.nom_francais,
            nom_anglais=diplomatic_post.nom_anglais,
            code=diplomatic_post.code,
        )


class PosteDiplomatiqueInMemoryFactory(PosteDiplomatiqueInMemoryTranslator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        PosteDiplomatiqueInMemoryTranslator.entities = [
            PosteDiplomatiqueFactory(
                code=1,
                nom_francais="Londres",
                nom_anglais="London",
            ),
            PosteDiplomatiqueFactory(
                code=2,
                nom_francais="Paris",
                nom_anglais="Paris",
            ),
            PosteDiplomatiqueFactory(
                code=3,
                nom_francais="Bruxelles",
                nom_anglais="Brussels",
            ),
        ]


PosteDiplomatiqueInMemoryFactory()
