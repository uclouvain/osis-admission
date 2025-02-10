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

from admission.auth.predicates import not_in_continuing_statuses_predicate_message
from admission.models import ContinuingEducationAdmission
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    STATUTS_PROPOSITION_CONTINUE_SOUMISE,
    STATUTS_PROPOSITION_CONTINUE_SOUMISE_POUR_GESTIONNAIRE,
    STATUTS_PROPOSITION_CONTINUE_SOUMISE_POUR_CANDIDAT,
)
from osis_role.errors import predicate_failed_msg


@predicate(bind=True)
@predicate_failed_msg(message=_("This action is limited to a specific admission context."))
def is_continuing(self, user: User, obj: ContinuingEducationAdmission):
    from admission.constants import CONTEXT_CONTINUING

    return obj.admission_context == CONTEXT_CONTINUING


@predicate(bind=True)
@predicate_failed_msg(message=_('The proposition must be in draft form to realize this action.'))
def in_progress(self, user: User, obj: ContinuingEducationAdmission):
    return (
        isinstance(obj, ContinuingEducationAdmission) and obj.status == ChoixStatutPropositionContinue.EN_BROUILLON.name
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("The proposition must be submitted to realize this action."))
def is_submitted(self, user: User, obj: ContinuingEducationAdmission):
    return isinstance(obj, ContinuingEducationAdmission) and bool(obj.submitted_at)


@predicate(bind=True)
@predicate_failed_msg(
    not_in_continuing_statuses_predicate_message(STATUTS_PROPOSITION_CONTINUE_SOUMISE_POUR_GESTIONNAIRE),
)
def in_manager_status(self, user: User, obj: ContinuingEducationAdmission):
    return (
        isinstance(obj, ContinuingEducationAdmission)
        and obj.status in STATUTS_PROPOSITION_CONTINUE_SOUMISE_POUR_GESTIONNAIRE
    )


@predicate(bind=True)
@predicate_failed_msg(message=_('The proposition must not be cancelled to realize this action.'))
def not_cancelled(self, user: User, obj: ContinuingEducationAdmission):
    return isinstance(obj, ContinuingEducationAdmission) and obj.status != ChoixStatutPropositionContinue.ANNULEE.name


@predicate(bind=True)
@predicate_failed_msg(message=_('The proposition must not be cancelled to realize this action.'))
def is_submitted_or_not_cancelled(self, user: User, obj: ContinuingEducationAdmission):
    return isinstance(obj, ContinuingEducationAdmission) and (
        obj.status != ChoixStatutPropositionContinue.ANNULEE.name or bool(obj.submitted_at)
    )


@predicate(bind=True)
@predicate_failed_msg(
    not_in_continuing_statuses_predicate_message({ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name})
)
def in_document_request_status(self, user: User, obj: ContinuingEducationAdmission):
    return (
        isinstance(obj, ContinuingEducationAdmission)
        and obj.status in STATUTS_PROPOSITION_CONTINUE_SOUMISE_POUR_CANDIDAT
    )


@predicate(bind=True)
@predicate_failed_msg(
    not_in_continuing_statuses_predicate_message(
        {
            ChoixStatutPropositionContinue.CONFIRMEE.name,
            ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name,
        }
    )
)
def can_request_documents(self, user: User, obj: ContinuingEducationAdmission):
    return isinstance(obj, ContinuingEducationAdmission) and obj.status in {
        ChoixStatutPropositionContinue.CONFIRMEE.name,
        ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name,
    }


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be invited to complete this admission."))
def is_invited_to_complete(self, user: User, obj: ContinuingEducationAdmission):
    return obj.status in STATUTS_PROPOSITION_CONTINUE_SOUMISE_POUR_CANDIDAT
