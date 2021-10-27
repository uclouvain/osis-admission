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
from django.contrib.auth.models import User
from rules import predicate

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.enums.actor_type import ActorType


@predicate
def is_admission_request_author(user: User, obj: BaseAdmission):
    return obj.candidate == user.person


@predicate
def is_admission_request_promoter(user: User, obj: DoctorateAdmission):
    return user.person.pk in obj.supervision_group.actors.filter(
        supervisionactor__type=ActorType.PROMOTER.name,
    ).values_list('person_id', flat=True)


@predicate(bind=True)
def is_part_of_doctoral_commission(self, user: User, obj: DoctorateAdmission):
    return obj.doctorate.management_entity_id in self.context['role_qs'].get_entities_ids()


@predicate
def is_part_of_committee(user: User, obj: DoctorateAdmission):
    return user.person.pk in obj.supervision_group.actors.values_list('person_id', flat=True)
