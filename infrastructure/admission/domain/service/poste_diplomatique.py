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
from typing import Optional

from admission.contrib.models import DiplomaticPost
from admission.ddd.admission.domain.model.poste_diplomatique import PosteDiplomatiqueIdentity

from admission.ddd.admission.domain.service.i_poste_diplomatique import IPosteDiplomatiqueTranslator
from admission.ddd.admission.domain.validator.exceptions import PosteDiplomatiqueNonTrouveException
from admission.ddd.admission.dtos.poste_diplomatique import PosteDiplomatiqueDTO


class PosteDiplomatiqueTranslator(IPosteDiplomatiqueTranslator):
    @classmethod
    def get(cls, code: Optional[int]) -> Optional[PosteDiplomatiqueIdentity]:
        if code is not None:
            try:
                diplomatic_post = DiplomaticPost.objects.get(code=code)
                return PosteDiplomatiqueIdentity(code=code)
            except DiplomaticPost.DoesNotExist:
                raise PosteDiplomatiqueNonTrouveException

    @classmethod
    def get_dto(cls, code: int) -> PosteDiplomatiqueDTO:
        try:
            return cls.build_dto(DiplomaticPost.objects.get(code=code))
        except DiplomaticPost.DoesNotExist:
            raise PosteDiplomatiqueNonTrouveException

    @classmethod
    def build_dto(cls, diplomatic_post: DiplomaticPost) -> PosteDiplomatiqueDTO:
        return PosteDiplomatiqueDTO(
            nom_francais=diplomatic_post.name_fr,
            nom_anglais=diplomatic_post.name_en,
            code=diplomatic_post.code,
            adresse_email=diplomatic_post.email,
        )
