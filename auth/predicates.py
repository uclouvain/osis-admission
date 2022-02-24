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
from django.utils.translation import gettext_lazy as _
from osis_signature.enums import SignatureState
from rules import predicate

from osis_role.errors import predicate_failed_msg

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.enums.actor_type import ActorType


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be the request author to access this admission"))
def is_admission_request_author(self, user: User, obj: BaseAdmission):
    return obj.candidate == user.person


@predicate(bind=True)
@predicate_failed_msg(message=_("Invitations must have been sent"))
def invitations_sent(self, user: User, obj: DoctorateAdmission):
    return (
        obj.supervision_group
        and obj.supervision_group.actors.exclude(
            last_state=SignatureState.NOT_INVITED.name,
        ).exists()
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("The invitations must not have been sent"))
def invitations_not_sent(self, user: User, obj: DoctorateAdmission):
    return not invitations_sent(user, obj)


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be the request promoter to access this admission"))
def is_admission_request_promoter(self, user: User, obj: DoctorateAdmission):
    return obj.supervision_group and user.person.pk in obj.supervision_group.actors.filter(
        supervisionactor__type=ActorType.PROMOTER.name,
    ).values_list('person_id', flat=True)


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be a member of the doctoral commission to access this admission"))
def is_part_of_doctoral_commission(self, user: User, obj: DoctorateAdmission):
    return obj.doctorate.management_entity_id in self.context['role_qs'].get_entities_ids()


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be a member of the committee to access this admission"))
def is_part_of_committee(self, user: User, obj: DoctorateAdmission):
    return obj.supervision_group and user.person.pk in obj.supervision_group.actors.values_list('person_id', flat=True)


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be a member of the committee who has not yet given his answer"))
def is_part_of_committee_and_invited(self, user: User, obj: DoctorateAdmission):
    return obj.supervision_group and user.person.pk in obj.supervision_group.actors.filter(
        last_state=SignatureState.INVITED.name,
    ).values_list('person_id', flat=True)
