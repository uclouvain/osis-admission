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

from django.utils.translation import get_language

from admission.auth.roles.ca_member import CommitteeMember
from admission.ddd.preparation.projet_doctoral.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.preparation.projet_doctoral.domain.service.i_membre_CA import IMembreCATranslator
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import MembreCANonTrouveException
from admission.ddd.preparation.projet_doctoral.dtos import MembreCADTO
from base.models.person import Person


class MembreCATranslator(IMembreCATranslator):
    @classmethod
    def get(cls, matricule: str) -> 'MembreCAIdentity':
        if not Person.objects.filter(global_id=matricule):
            raise MembreCANonTrouveException
        return MembreCAIdentity(matricule=matricule)

    @classmethod
    def get_dto(cls, matricule: str) -> MembreCADTO:
        member_role = CommitteeMember.objects.select_related('person', 'country').get(person__global_id=matricule)
        return MembreCADTO(
            matricule=matricule,
            nom=member_role.person.last_name,
            prenom=member_role.person.first_name,
            email=member_role.person.email,
            titre=member_role.title,
            institution=member_role.institute,
            ville=member_role.city,
            pays=(
                member_role.country_id
                and getattr(member_role.country, 'name_en' if get_language() == 'en' else 'name')
                or ''
            ),
        )

    @classmethod
    def search(cls, matricules: List[str]) -> List['MembreCAIdentity']:
        raise NotImplementedError

    @classmethod
    def est_externe(cls, identity: 'MembreCAIdentity') -> bool:  # pragma: no cover
        return CommitteeMember.objects.get(person__global_id=identity.matricule).is_external
