# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class ChoixStatutDoctorat(ChoiceEnum):
    # Before enrolment
    ADMISSION_IN_PROGRESS = _('ADMISSION_IN_PROGRESS')
    # After enrolment
    ADMITTED = _('ADMITTED')
    # Confirmation exam
    SUBMITTED_CONFIRMATION = _('SUBMITTED_CONFIRMATION')
    PASSED_CONFIRMATION = _('PASSED_CONFIRMATION')
    NOT_ALLOWED_TO_CONTINUE = _('NOT_ALLOWED_TO_CONTINUE')
    CONFIRMATION_TO_BE_REPEATED = _('CONFIRMATION_TO_BE_REPEATED')
    # Jury
    JURY_SOUMIS = _('JURY_SOUMIS')
    JURY_APPROUVE_CA = _('JURY_APPROUVE_CA')
    JURY_APPROUVE_CDD = _('JURY_APPROUVE_CDD')
    JURY_REFUSE_CDD = _('JURY_REFUSE_CDD')
    JURY_APPROUVE_ADRE = _('JURY_APPROUVE_ADRE')
    JURY_REFUSE_ADRE = _('JURY_REFUSE_ADRE')


STATUTS_DOCTORAT_EPREUVE_CONFIRMATION_EN_COURS = {
    ChoixStatutDoctorat.ADMITTED.name,
    ChoixStatutDoctorat.SUBMITTED_CONFIRMATION.name,
    ChoixStatutDoctorat.CONFIRMATION_TO_BE_REPEATED.name,
}
