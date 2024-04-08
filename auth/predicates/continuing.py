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

from admission.contrib.models import ContinuingEducationAdmission
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    STATUTS_PROPOSITION_CONTINUE_SOUMISE,
)
from osis_role.errors import predicate_failed_msg


@predicate(bind=True)
@predicate_failed_msg(message=_("The proposition must be submitted to realize this action."))
def is_continuing(self, user: User, obj: ContinuingEducationAdmission):
    from admission.templatetags.admission import CONTEXT_CONTINUING

    return obj.get_admission_context() == CONTEXT_CONTINUING


@predicate(bind=True)
@predicate_failed_msg(message=_('The proposition must be in draft form to realize this action.'))
def in_progress(self, user: User, obj: ContinuingEducationAdmission):
    return obj.status == ChoixStatutPropositionContinue.EN_BROUILLON.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The proposition must be submitted to realize this action."))
def is_submitted(self, user: User, obj: ContinuingEducationAdmission):
    return obj.status in STATUTS_PROPOSITION_CONTINUE_SOUMISE
