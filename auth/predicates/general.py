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
from rules import predicate

from admission.auth.predicates import not_in_general_statuses_predicate_message
from admission.models import GeneralEducationAdmission
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS,
    STATUTS_PROPOSITION_GENERALE_SOUMISE,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_OU_FRAIS_DOSSIER_EN_ATTENTE,
    STATUTS_PROPOSITION_GENERALE_ENVOYABLE_EN_FAC_POUR_DECISION,
)
from osis_role.errors import predicate_failed_msg


@predicate(bind=True)
@predicate_failed_msg(message=_('The proposition must be in draft form to realize this action.'))
def in_progress(self, user: User, obj: GeneralEducationAdmission):
    return obj.status == ChoixStatutPropositionGenerale.EN_BROUILLON.name


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be invited to complete this admission."))
def is_invited_to_complete(self, user: User, obj: GeneralEducationAdmission):
    return obj.status in {
        ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
        ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
    }


def payment_needed_after_submission(admission: GeneralEducationAdmission):
    checklist_info = admission.checklist.get('current', {}).get('frais_dossier', {})
    return (
        admission.status == ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name
        and checklist_info.get('statut') == ChoixStatutChecklist.GEST_BLOCAGE.name
        and bool(checklist_info.get('extra', {}).get('initial'))
    )


def payment_needed_after_manager_request(admission: GeneralEducationAdmission):
    checklist_info = admission.checklist.get('current', {}).get('frais_dossier', {})
    return (
        admission.status == ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name
        and checklist_info.get('statut') == ChoixStatutChecklist.GEST_BLOCAGE.name
        and not bool(checklist_info.get('extra', {}).get('initial'))
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be invited to pay the application fee by the system."))
def is_invited_to_pay_after_submission(self, user: User, obj: GeneralEducationAdmission):
    return payment_needed_after_submission(admission=obj)


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be invited to pay the application fee by a manager."))
def is_invited_to_pay_after_request(self, user: User, obj: GeneralEducationAdmission):
    return payment_needed_after_manager_request(admission=obj)


@predicate(bind=True)
@predicate_failed_msg(_("You must be invited to pay the application fee or you must have submitted your application."))
def can_view_payment(self, user: User, obj: GeneralEducationAdmission):
    return obj.status in {
        ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
        ChoixStatutPropositionGenerale.CONFIRMEE.name,
    }


@predicate(bind=True)
@predicate_failed_msg(message=_("The proposition must be submitted to realize this action."))
def is_submitted(self, user: User, obj: GeneralEducationAdmission):
    return isinstance(obj, GeneralEducationAdmission) and obj.status in STATUTS_PROPOSITION_GENERALE_SOUMISE


@predicate(bind=True)
@predicate_failed_msg(message=_('The proposition must not be cancelled to realize this action.'))
def not_cancelled(self, user: User, obj: GeneralEducationAdmission):
    return isinstance(obj, GeneralEducationAdmission) and obj.status != ChoixStatutPropositionGenerale.ANNULEE.name


@predicate(bind=True)
@predicate_failed_msg(not_in_general_statuses_predicate_message(STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC))
def in_fac_status(self, user: User, obj: GeneralEducationAdmission):
    return isinstance(obj, GeneralEducationAdmission) and obj.status in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC


@predicate(bind=True)
@predicate_failed_msg(not_in_general_statuses_predicate_message(STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS))
def in_fac_status_extended(self, user: User, obj: GeneralEducationAdmission):
    return (
        isinstance(obj, GeneralEducationAdmission)
        and obj.status in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS
    )


@predicate(bind=True)
@predicate_failed_msg(not_in_general_statuses_predicate_message(STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC))
def in_sic_status(self, user: User, obj: GeneralEducationAdmission):
    return isinstance(obj, GeneralEducationAdmission) and obj.status in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC


@predicate(bind=True)
@predicate_failed_msg(
    not_in_general_statuses_predicate_message({ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name})
)
def in_sic_document_request_status(self, user: User, obj: GeneralEducationAdmission):
    return (
        isinstance(obj, GeneralEducationAdmission)
        and obj.status == ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name
    )


@predicate(bind=True)
@predicate_failed_msg(
    not_in_general_statuses_predicate_message({ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name})
)
def in_fac_document_request_status(self, user: User, obj: GeneralEducationAdmission):
    return (
        isinstance(obj, GeneralEducationAdmission)
        and obj.status == ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name
    )


@predicate(bind=True)
@predicate_failed_msg(not_in_general_statuses_predicate_message(STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS))
def in_sic_status_extended(self, user: User, obj: GeneralEducationAdmission):
    return (
        isinstance(obj, GeneralEducationAdmission)
        and obj.status in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS
    )


@predicate(bind=True)
@predicate_failed_msg(
    not_in_general_statuses_predicate_message(STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_OU_FRAIS_DOSSIER_EN_ATTENTE)
)
def in_sic_status_or_application_fees(self, user: User, obj: GeneralEducationAdmission):
    return obj.status in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_OU_FRAIS_DOSSIER_EN_ATTENTE


@predicate(bind=True)
@predicate_failed_msg(
    not_in_general_statuses_predicate_message(STATUTS_PROPOSITION_GENERALE_ENVOYABLE_EN_FAC_POUR_DECISION)
)
def can_send_to_fac_faculty_decision(self, user: User, obj: GeneralEducationAdmission):
    return (
        isinstance(obj, GeneralEducationAdmission)
        and obj.status in STATUTS_PROPOSITION_GENERALE_ENVOYABLE_EN_FAC_POUR_DECISION
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("This action is limited to a specific admission context."))
def is_general(self, user: User, obj: GeneralEducationAdmission):
    from admission.constants import CONTEXT_GENERAL

    return obj.admission_context == CONTEXT_GENERAL
