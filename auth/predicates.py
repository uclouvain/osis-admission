# ##############################################################################
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
# ##############################################################################
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from osis_signature.enums import SignatureState
from rules import predicate

from admission.ddd.doctorat.domain.model.enums import (
    ChoixStatutDoctorat,
    STATUTS_DOCTORAT_EPREUVE_CONFIRMATION_EN_COURS,
)
from admission.ddd.admission.projet_doctoral.preparation.domain.model._enums import (
    ChoixStatutProposition,
    STATUTS_PROPOSITION_AVANT_SOUMISSION,
    STATUTS_PROPOSITION_AVANT_INSCRIPTION,
)
from osis_role.cache import predicate_cache
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
def in_progress(self, user: User, obj: DoctorateAdmission):
    return obj.status == ChoixStatutProposition.IN_PROGRESS.name


@predicate(bind=True)
@predicate_failed_msg(message=_("Invitations have not been sent"))
def signing_in_progress(self, user: User, obj: DoctorateAdmission):
    return obj.status == ChoixStatutProposition.SIGNING_IN_PROGRESS.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The proposition has already been confirmed or is cancelled"))
def unconfirmed_proposition(self, user: User, obj: DoctorateAdmission):
    return obj.status in STATUTS_PROPOSITION_AVANT_SOUMISSION


@predicate(bind=True)
@predicate_failed_msg(message=_("Must be enrolled"))
def is_enrolled(self, user: User, obj: DoctorateAdmission):
    return obj.status == ChoixStatutProposition.ENROLLED.name


@predicate(bind=True)
@predicate_failed_msg(message=_("Must be in the process of the enrolment"))
def is_being_enrolled(self, user: User, obj: DoctorateAdmission):
    return obj.status in STATUTS_PROPOSITION_AVANT_INSCRIPTION


@predicate(bind=True)
@predicate_failed_msg(message=_("The confirmation paper is not in progress"))
def confirmation_paper_in_progress(self, user: User, obj: DoctorateAdmission):
    return obj.post_enrolment_status in STATUTS_DOCTORAT_EPREUVE_CONFIRMATION_EN_COURS


@predicate(bind=True)
@predicate_failed_msg(message=_("The confirmation paper is not in progress"))
def submitted_confirmation_paper(self, user: User, obj: DoctorateAdmission):
    return obj.post_enrolment_status == ChoixStatutDoctorat.SUBMITTED_CONFIRMATION.name


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be the request promoter to access this admission"))
def is_admission_request_promoter(self, user: User, obj: DoctorateAdmission):
    return obj.supervision_group and user.person.pk in obj.supervision_group.actors.filter(
        supervisionactor__type=ActorType.PROMOTER.name,
    ).values_list('person_id', flat=True)


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be the reference promoter to access this admission"))
def is_admission_reference_promoter(self, user: User, obj: DoctorateAdmission):
    return (
        obj.supervision_group
        and obj.supervision_group.actors.filter(
            supervisionactor__type=ActorType.PROMOTER.name,
            supervisionactor__is_reference_promoter=True,
            person_id=user.person.pk,
        ).exists()
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be a member of the doctoral commission to access this admission"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
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
