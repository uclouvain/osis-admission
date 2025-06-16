# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.db.models import Exists, OuterRef
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.doctorat.preparation.domain.model._membre_CA import (
    MembreCAIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_membre_CA import (
    IMembreCATranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    MembreCANonTrouveException,
)
from admission.ddd.admission.doctorat.preparation.dtos import MembreCADTO
from admission.models import SupervisionActor
from admission.models.enums.actor_type import ActorType
from base.models.person import Person
from base.models.student import Student


class MembreCATranslator(IMembreCATranslator):
    @classmethod
    def get(cls, membre_ca_id: 'MembreCAIdentity') -> 'MembreCAIdentity':
        raise NotImplementedError

    @classmethod
    def get_dto(cls, membre_ca_id: 'MembreCAIdentity') -> MembreCADTO:
        actor = SupervisionActor.objects.select_related('person__tutor', 'country').get(
            type=ActorType.CA_MEMBER.name,
            uuid=membre_ca_id.uuid,
        )
        return MembreCADTO(
            uuid=membre_ca_id.uuid,
            matricule=actor.person and actor.person.global_id or '',
            nom=actor.last_name,
            prenom=actor.first_name,
            email=actor.email,
            est_docteur=(
                True
                if not actor.is_external and hasattr(actor.person, 'tutor')
                else actor.is_external and actor.is_doctor
            ),
            institution=_('ucl') if not actor.is_external else actor.institute,
            ville=actor.city,
            code_pays=actor.country_id and actor.country.iso_code or '',
            pays=actor.country_id and getattr(actor.country, 'name_en' if get_language() == 'en' else 'name') or '',
            est_externe=actor.is_external,
        )

    @classmethod
    def search(cls, matricules: List[str]) -> List['MembreCAIdentity']:
        raise NotImplementedError

    @classmethod
    def est_externe(cls, membre_ca_id: 'MembreCAIdentity') -> bool:
        raise NotImplementedError

    @classmethod
    def verifier_existence(cls, matricule: Optional[str]) -> bool:
        if matricule and not cls._get_queryset(matricule).exists():
            raise MembreCANonTrouveException
        return True

    @classmethod
    def _get_queryset(cls, matricule):
        return Person.objects.alias(
            # Is the person a student and not a tutor?
            is_student_and_not_tutor=Exists(Student.objects.filter(person=OuterRef('pk'), person__tutor__isnull=True)),
        ).filter(
            global_id=matricule,
            # Remove unexistent users
            user_id__isnull=False,
            # Remove students who aren't tutors
            is_student_and_not_tutor=False,
        )
