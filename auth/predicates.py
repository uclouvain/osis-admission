# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from rules import predicate
from waffle import switch_is_active

from admission.contrib.models import DoctorateAdmission, GeneralEducationAdmission
from admission.contrib.models.base import BaseAdmission, BaseAdmissionProxy
from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    STATUTS_PROPOSITION_AVANT_INSCRIPTION,
    STATUTS_PROPOSITION_AVANT_SOUMISSION,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS,
    STATUTS_PROPOSITION_GENERALE_SOUMISE,
)
from admission.ddd.parcours_doctoral.domain.model.enums import (
    ChoixStatutDoctorat,
    STATUTS_DOCTORAT_EPREUVE_CONFIRMATION_EN_COURS,
)
from osis_role.cache import predicate_cache
from osis_role.errors import predicate_failed_msg
from osis_signature.enums import SignatureState


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be the request author to access this admission"))
def is_admission_request_author(self, user: User, obj: BaseAdmission):
    return obj.candidate == user.person


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
@predicate_failed_msg(message=_("Another admission has been submitted."))
def does_not_have_a_submitted_admission(self, user: User, obj: DoctorateAdmission):
    return not BaseAdmissionProxy.objects.candidate_has_submission(user.person)


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
@predicate_failed_msg(message=_("You must be invited to complete this admission."))
def is_invited_to_complete(self, user: User, obj: GeneralEducationAdmission):
    return obj.status in {
        ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
        ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
    }


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be invited to pay the application fees by the system."))
def is_invited_to_pay_after_submission(self, user: User, obj: GeneralEducationAdmission):
    checklist_info = obj.checklist.get('current', {}).get('frais_dossier', {})
    return (
        obj.status == ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name
        and checklist_info.get('statut') == ChoixStatutChecklist.GEST_BLOCAGE.name
        and bool(checklist_info.get('extra', {}).get('initial'))
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be invited to pay the application fees by a manager."))
def is_invited_to_pay_after_request(self, user: User, obj: GeneralEducationAdmission):
    checklist_info = obj.checklist.get('current', {}).get('frais_dossier', {})
    return (
        obj.status == ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name
        and checklist_info.get('statut') == ChoixStatutChecklist.GEST_BLOCAGE.name
        and not bool(checklist_info.get('extra', {}).get('initial'))
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("The proposition must be submitted to realize this action."))
def is_submitted(self, user: User, obj: GeneralEducationAdmission):
    return obj.status in STATUTS_PROPOSITION_GENERALE_SOUMISE


@predicate(bind=True)
@predicate_failed_msg(
    message=_("The global status of the application must be one of the following to realize this action: %(statuses)s.")
    % {
        'statuses': STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC,
    }
)
def in_fac_status(self, user: User, obj: GeneralEducationAdmission):
    return obj.status in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC


@predicate(bind=True)
@predicate_failed_msg(
    message=_("The global status of the application must be one of the following to realize this action: %(statuses)s.")
    % {
        'statuses': STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS,
    }
)
def in_fac_status_extended(self, user: User, obj: GeneralEducationAdmission):
    return obj.status in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS


@predicate(bind=True)
@predicate_failed_msg(
    message=_("The global status of the application must be one of the following to realize this action: %(statuses)s.")
    % {
        'statuses': STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC,
    }
)
def in_sic_status(self, user: User, obj: GeneralEducationAdmission):
    return obj.status in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC


@predicate(bind=True)
@predicate_failed_msg(
    message=_("The global status of the application must be one of the following to realize this action: %(statuses)s.")
    % {
        'statuses': STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS,
    }
)
def in_sic_status_extended(self, user: User, obj: GeneralEducationAdmission):
    return obj.status in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS


@predicate
def is_debug(*args):
    return switch_is_active("debug")


def has_scope(*scopes):
    assert len(scopes) > 0, 'You must provide at least one scope name'

    name = 'has_scope:%s' % ','.join(s.name for s in scopes)

    @predicate(name, bind=True)
    def fn(self, user):
        if not hasattr(user, '_admission_scopes'):
            user._admission_scopes = set(
                scope for scope_list in self.context['role_qs'].values_list('scopes', flat=True) for scope in scope_list
            )
        return set([s.name for s in scopes]) <= user._admission_scopes

    return fn


@predicate(bind=True)
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_part_of_education_group(self, user: User, obj: BaseAdmission):
    return obj.training.education_group_id in self.context['role_qs'].get_education_groups_affected()


@predicate(bind=True)
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_entity_manager(self, user: User, obj: BaseAdmission):
    return obj.training.management_entity_id in self.context['role_qs'].get_entities_ids()


def has_education_group_of_types(*education_group_types):
    name = 'has_education_group_of_types:%s' % ','.join(education_group_types)

    @predicate(name, bind=True)
    def fn(self, user: User):
        if not hasattr(user, '_education_group_types'):
            user._education_group_types = set(
                self.context['role_qs'].values_list(
                    'education_group__educationgroupyear__education_group_type__name', flat=True
                )
            )
        return set(education_group_types) & user._education_group_types

    return fn
