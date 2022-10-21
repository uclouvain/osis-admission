##############################################################################
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
##############################################################################

from django.utils.translation import gettext_lazy as _

from osis_common.ddd.interface import BusinessException


class BourseNonTrouveeException(BusinessException):
    status_code = "ADMISSION-1"

    def __init__(self, **kwargs):
        message = _("No scholarship found.")
        super().__init__(message, **kwargs)


class ConditionsAccessNonRempliesException(BusinessException):
    status_code = "ADMISSION-2"

    def __init__(self, **kwargs):
        message = _("Admission conditions not met.")
        super().__init__(message, **kwargs)


class QuestionsSpecifiquesChoixFormationNonCompleteesException(BusinessException):
    status_code = "ADMISSION-3"

    def __init__(self, **kwargs):
        message = _("Mandatory fields are missing in the specific questions of the 'Training choice' tab")
        super().__init__(message, **kwargs)


class QuestionsSpecifiquesCurriculumNonCompleteesException(BusinessException):
    status_code = "ADMISSION-4"

    def __init__(self, **kwargs):
        message = _(
            "Mandatory fields are missing in the specific questions of the "
            "'Previous Experience > Curriculum vitae' tab."
        )
        super().__init__(message, **kwargs)


class QuestionsSpecifiquesEtudesSecondairesNonCompleteesException(BusinessException):
    status_code = "ADMISSION-5"

    def __init__(self, **kwargs):
        message = _(
            "Mandatory fields are missing in the specific questions of the "
            "'Previous experience > Secondary studies' tab"
        )
        super().__init__(message, **kwargs)
