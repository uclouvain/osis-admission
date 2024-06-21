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
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from osis_signature.enums import SignatureState
from rules import predicate

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    STATUTS_PROPOSITION_AVANT_SOUMISSION,
    ChoixTypeAdmission,
    STATUTS_PROPOSITION_AVANT_INSCRIPTION,
)
from admission.ddd.parcours_doctoral.domain.model.enums import (
    ChoixStatutDoctorat,
    STATUTS_DOCTORAT_EPREUVE_CONFIRMATION_EN_COURS,
)
from osis_role.cache import predicate_cache
from osis_role.errors import predicate_failed_msg


@predicate(bind=True)
@predicate_failed_msg(message=_("Invitations must have been sent"))
def in_progress(self, user: User, obj: DoctorateAdmission):
    return obj.status == ChoixStatutPropositionDoctorale.EN_BROUILLON.name


@predicate(bind=True)
@predicate_failed_msg(message=_("Invitations have not been sent"))
def signing_in_progress(self, user: User, obj: DoctorateAdmission):
    return obj.status == ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The jury is not in progress"))
def is_jury_in_progress(self, user: User, obj: DoctorateAdmission):
    return obj.post_enrolment_status == ChoixStatutDoctorat.PASSED_CONFIRMATION.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The proposition has already been confirmed or is cancelled"))
def unconfirmed_proposition(self, user: User, obj: DoctorateAdmission):
    return obj.status in STATUTS_PROPOSITION_AVANT_SOUMISSION


@predicate(bind=True)
@predicate_failed_msg(message=_("Must be enrolled"))
def is_enrolled(self, user: User, obj: DoctorateAdmission):
    return obj.status == ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name


@predicate(bind=True)
@predicate_failed_msg(message=_("Must not be pre-admission"))
def is_pre_admission(self, user: User, obj: DoctorateAdmission):
    return obj.type == ChoixTypeAdmission.PRE_ADMISSION.name


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
@predicate_failed_msg(message=_("Complementary training not enabled"))
def complementary_training_enabled(self, user: User, obj: DoctorateAdmission):
    return (
        hasattr(obj.doctorate.management_entity, 'admission_config')
        and obj.doctorate.management_entity.admission_config.is_complementary_training_enabled
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be the request promoter to access this admission"))
def is_admission_request_promoter(self, user: User, obj: DoctorateAdmission):
    return obj.supervision_group and user.person.pk in [
        actor.person_id
        for actor in obj.supervision_group.actors.all()
        if actor.supervisionactor.type == ActorType.PROMOTER.name
    ]


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be the reference promoter to access this admission"))
def is_admission_reference_promoter(self, user: User, obj: DoctorateAdmission):
    return obj.supervision_group and user.person.pk in [
        actor.person_id
        for actor in obj.supervision_group.actors.all()
        if actor.supervisionactor.type == ActorType.PROMOTER.name and actor.supervisionactor.is_reference_promoter
    ]


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be a member of the doctoral commission to access this admission"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_part_of_doctoral_commission(self, user: User, obj: DoctorateAdmission):
    return (
        isinstance(obj, DoctorateAdmission)
        and obj.doctorate.management_entity_id in self.context['role_qs'].get_entities_ids()
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be a member of the committee to access this admission"))
def is_part_of_committee(self, user: User, obj: DoctorateAdmission):
    return obj.supervision_group and user.person.pk in [actor.person_id for actor in obj.supervision_group.actors.all()]


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be a member of the committee who has not yet given his answer"))
def is_part_of_committee_and_invited(self, user: User, obj: DoctorateAdmission):
    return obj.supervision_group and user.person.pk in [
        actor.person_id
        for actor in obj.supervision_group.actors.all()
        if actor.last_state == SignatureState.INVITED.name
    ]


@predicate(bind=True)
@predicate_failed_msg(message=_("This action is limited to a specific admission context."))
def is_doctorate(self, user: User, obj: DoctorateAdmission):
    from admission.constants import CONTEXT_DOCTORATE

    return obj.get_admission_context() == CONTEXT_DOCTORATE
