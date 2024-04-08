##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################

from django.utils.translation import gettext_lazy as _

from osis_common.ddd.interface import BusinessException


class FormationNonTrouveeException(BusinessException):
    status_code = "FORMATION-CONTINUE-1"

    def __init__(self, **kwargs):
        message = _("No training found.")
        super().__init__(message, **kwargs)


class PropositionNonTrouveeException(BusinessException):
    status_code = "FORMATION-CONTINUE-2"

    def __init__(self, **kwargs):
        message = _("Proposition not found.")
        super().__init__(message, **kwargs)


class ExperiencesCurriculumNonRenseigneesException(BusinessException):
    status_code = "FORMATION-CONTINUE-3"

    def __init__(self, **kwargs):
        message = _(
            "Please specify the details of your most recent academic training "
            "and your most recent non-academic experience."
        )
        super().__init__(message, **kwargs)


class InformationsComplementairesNonRenseigneesException(BusinessException):
    status_code = "FORMATION-CONTINUE-4"

    def __init__(self, **kwargs):
        message = _("Mandatory fields are missing in the 'Additional information > Specific questions' tab.")
        super().__init__(message, **kwargs)


class MettreEnAttenteTransitionStatutException(BusinessException):
    status_code = "FORMATION-CONTINUE-5"

    def __init__(self, **kwargs):
        message = _('You can not transition to the "Hold on" status from the "Closed" status.')
        super().__init__(message, **kwargs)


class ApprouverParFacTransitionStatutException(BusinessException):
    status_code = "FORMATION-CONTINUE-6"

    def __init__(self, **kwargs):
        message = _('You can not transition to the "Approved" status from the "Validated" or "Closed" status.')
        super().__init__(message, **kwargs)


class RefuserPropositionTransitionStatutException(BusinessException):
    status_code = "FORMATION-CONTINUE-7"

    def __init__(self, **kwargs):
        message = _('You can not transition to the "Denied" status from the "Validated" or "Closed" status.')
        super().__init__(message, **kwargs)


class AnnulerPropositionTransitionStatutException(BusinessException):
    status_code = "FORMATION-CONTINUE-8"

    def __init__(self, **kwargs):
        message = _('You can not transition to the "Canceled" status from the "Closed" status.')
        super().__init__(message, **kwargs)


class ApprouverPropositionTransitionStatutException(BusinessException):
    status_code = "FORMATION-CONTINUE-9"

    def __init__(self, **kwargs):
        message = _('You can only transition to the "Validated" status from the "Approved" status.')
        super().__init__(message, **kwargs)
