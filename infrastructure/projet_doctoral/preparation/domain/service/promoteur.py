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

from django.utils.translation import get_language, gettext_lazy as _

from admission.auth.roles.promoter import Promoter
from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import PromoteurNonTrouveException
from admission.ddd.admission.doctorat.preparation.dtos import PromoteurDTO
from base.auth.roles.tutor import Tutor


class PromoteurTranslator(IPromoteurTranslator):
    @classmethod
    def get(cls, matricule: str) -> 'PromoteurIdentity':
        if not Tutor.objects.filter(person__global_id=matricule):
            raise PromoteurNonTrouveException
        return PromoteurIdentity(matricule=matricule)

    @classmethod
    def get_dto(cls, matricule: str) -> 'PromoteurDTO':
        promoter_role = Promoter.objects.select_related('person__tutor', 'country').get(person__global_id=matricule)
        return PromoteurDTO(
            matricule=matricule,
            nom=promoter_role.person.last_name,
            prenom=promoter_role.person.first_name,
            email=promoter_role.person.email,
            titre=_('Prof.') if hasattr(promoter_role.person, 'tutor') else promoter_role.title,
            institution=_('ucl') if not promoter_role.is_external else promoter_role.institute,
            ville=promoter_role.city,
            pays=(
                promoter_role.country_id
                and getattr(promoter_role.country, 'name_en' if get_language() == 'en' else 'name')
                or ''
            ),
        )

    @classmethod
    def search(cls, matricules: List[str]) -> List['PromoteurIdentity']:
        raise NotImplementedError

    @classmethod
    def est_externe(cls, identity: 'PromoteurIdentity') -> bool:
        return Promoter.objects.get(person__global_id=identity.matricule).is_external
