# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import List, Optional

from django.utils.translation import get_language, gettext_lazy as _

from admission.contrib.models import SupervisionActor
from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import PromoteurNonTrouveException
from admission.ddd.admission.doctorat.preparation.dtos import PromoteurDTO
from base.auth.roles.tutor import Tutor


class PromoteurTranslator(IPromoteurTranslator):
    @classmethod
    def get(cls, promoteur_id: 'PromoteurIdentity') -> 'PromoteurIdentity':
        raise NotImplementedError

    @classmethod
    def get_dto(cls, promoteur_id: 'PromoteurIdentity') -> 'PromoteurDTO':
        actor = SupervisionActor.objects.select_related('person__tutor', 'country').get(
            type=ActorType.PROMOTER.name,
            uuid=promoteur_id.uuid,
        )
        return PromoteurDTO(
            uuid=promoteur_id.uuid,
            matricule=actor.person and actor.person.global_id or '',
            nom=actor.last_name,
            prenom=actor.first_name,
            email=actor.email,
            est_docteur=True
            if not actor.is_external and hasattr(actor.person, 'tutor')
            else actor.is_external and actor.is_doctor,
            institution=_('ucl') if not actor.is_external else actor.institute,
            ville=actor.city,
            code_pays=actor.country_id and actor.country.iso_code or '',
            pays=actor.country_id and getattr(actor.country, 'name_en' if get_language() == 'en' else 'name') or '',
            est_externe=actor.is_external,
        )

    @classmethod
    def search(cls, matricules: List[str]) -> List['PromoteurIdentity']:
        raise NotImplementedError

    @classmethod
    def est_externe(cls, promoteur_id: 'PromoteurIdentity') -> bool:
        return SupervisionActor.objects.get(type=ActorType.PROMOTER.name, uuid=promoteur_id.uuid).is_external

    @classmethod
    def verifier_existence(cls, matricule: Optional[str]) -> bool:
        if matricule and not cls._get_queryset(matricule).exists():
            raise PromoteurNonTrouveException
        return True

    @classmethod
    def _get_queryset(cls, matricule):
        return Tutor.objects.filter(
            person__user_id__isnull=False,
            person__global_id=matricule,
        ).select_related("person")
