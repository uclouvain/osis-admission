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

from admission.auth.predicates import not_in_doctorate_statuses_predicate_message
from admission.models import DoctorateAdmission
from admission.models.enums.actor_type import ActorType
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    STATUTS_PROPOSITION_AVANT_SOUMISSION,
    ChoixTypeAdmission,
    STATUTS_PROPOSITION_AVANT_INSCRIPTION,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD_ETENDUS,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC_ETENDUS,
    STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_CDD_POUR_DECISION,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CANDIDAT,
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
    return obj.status in [
        ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
        ChoixStatutPropositionDoctorale.CA_EN_ATTENTE_DE_SIGNATURE.name,
    ]


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be invited to complete this admission."))
def is_invited_to_complete(self, user: User, obj: DoctorateAdmission):
    return obj.status in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CANDIDAT

@predicate(bind=True)
@predicate_failed_msg(message=_("The proposition has already been confirmed or is cancelled"))
def unconfirmed_proposition(self, user: User, obj: DoctorateAdmission):
    return obj.status in STATUTS_PROPOSITION_AVANT_SOUMISSION


@predicate(bind=True)
@predicate_failed_msg(message=_("The CA is not currently to be completed"))
def ca_to_be_completed(self, user: User, obj: DoctorateAdmission):
    return obj.status == ChoixStatutPropositionDoctorale.CA_A_COMPLETER.name


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


@predicate(bind=True)
@predicate_failed_msg(message=_("The proposition must be submitted to realize this action."))
def is_draft(self, user: User, obj: DoctorateAdmission):
    return isinstance(obj, DoctorateAdmission) and obj.status == ChoixStatutPropositionDoctorale.EN_BROUILLON.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The proposition must be submitted to realize this action."))
def is_submitted(self, user: User, obj: DoctorateAdmission):
    return isinstance(obj, DoctorateAdmission) and obj.status in STATUTS_PROPOSITION_DOCTORALE_SOUMISE


@predicate(bind=True)
@predicate_failed_msg(message=_("The proposition must be an admission to realize this action."))
def is_admission(self, user: User, obj: DoctorateAdmission):
    return obj.type == ChoixTypeAdmission.ADMISSION.name


@predicate(bind=True)
@predicate_failed_msg(message=_('The proposition must not be cancelled to realize this action.'))
def not_cancelled(self, user: User, obj: DoctorateAdmission):
    return isinstance(obj, DoctorateAdmission) and obj.status != ChoixStatutPropositionDoctorale.ANNULEE.name


@predicate(bind=True)
@predicate_failed_msg(not_in_doctorate_statuses_predicate_message(STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD))
def in_fac_status(self, user: User, obj: DoctorateAdmission):
    return isinstance(obj, DoctorateAdmission) and obj.status in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD


@predicate(bind=True)
@predicate_failed_msg(
    not_in_doctorate_statuses_predicate_message(STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD_ETENDUS)
)
def in_fac_status_extended(self, user: User, obj: DoctorateAdmission):
    return isinstance(obj, DoctorateAdmission) and obj.status in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD_ETENDUS


@predicate(bind=True)
@predicate_failed_msg(not_in_doctorate_statuses_predicate_message(STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC))
def in_sic_status(self, user: User, obj: DoctorateAdmission):
    return isinstance(obj, DoctorateAdmission) and obj.status in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC


@predicate(bind=True)
@predicate_failed_msg(
    not_in_doctorate_statuses_predicate_message({ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC.name})
)
def in_sic_document_request_status(self, user: User, obj: DoctorateAdmission):
    return (
        isinstance(obj, DoctorateAdmission) and obj.status == ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC.name
    )


@predicate(bind=True)
@predicate_failed_msg(
    not_in_doctorate_statuses_predicate_message({ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name})
)
def in_fac_document_request_status(self, user: User, obj: DoctorateAdmission):
    return (
        isinstance(obj, DoctorateAdmission) and obj.status == ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name
    )


@predicate(bind=True)
@predicate_failed_msg(
    not_in_doctorate_statuses_predicate_message(STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC_ETENDUS)
)
def in_sic_status_extended(self, user: User, obj: DoctorateAdmission):
    return isinstance(obj, DoctorateAdmission) and obj.status in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC_ETENDUS


@predicate(bind=True)
@predicate_failed_msg(
    not_in_doctorate_statuses_predicate_message(STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_CDD_POUR_DECISION)
)
def can_send_to_fac_faculty_decision(self, user: User, obj: DoctorateAdmission):
    return (
        isinstance(obj, DoctorateAdmission)
        and obj.status in STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_CDD_POUR_DECISION
    )
