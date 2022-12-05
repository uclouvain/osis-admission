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


class QuestionsSpecifiquesInformationsComplementairesNonCompleteesException(BusinessException):
    status_code = "ADMISSION-6"

    def __init__(self, **kwargs):
        message = _(
            "Mandatory fields are missing in the specific questions of the "
            "'Additional information > Specific questions' tab"
        )
        super().__init__(message, **kwargs)


class FormationNonTrouveeException(BusinessException):
    status_code = "ADMISSION-7"

    def __init__(self, sigle: str = None, annee: int = None, **kwargs):
        message = _("Formation is not available for this year.")
        if sigle and annee:
            message = _("Formation is not available for this year (%(sigle)s in %(annee)s).") % {
                'annee': annee,
                'sigle': sigle,
            }
        super().__init__(message)


class ReorientationInscriptionExterneNonConfirmeeException(BusinessException):
    status_code = "ADMISSION-8"

    def __init__(self, **kwargs):
        message = _("You must answer the question about reorientation.")
        super().__init__(message, **kwargs)


class ModificationInscriptionExterneNonConfirmeeException(BusinessException):
    status_code = "ADMISSION-9"

    def __init__(self, **kwargs):
        message = _("You must answer the question about external enrollement change.")
        super().__init__(message, **kwargs)


class PoolNonResidentContingenteNonOuvertException(BusinessException):
    status_code = "ADMISSION-10"

    def __init__(self, **kwargs):
        message = _("The limited training you are enrolling into is not opened yet.")
        super().__init__(message, **kwargs)


class ResidenceAuSensDuDecretNonRenseigneeException(BusinessException):
    status_code = "ADMISSION-11"

    def __init__(self, **kwargs):
        message = _("You must answer the question about residency.")
        super().__init__(message, **kwargs)


class AucunPoolCorrespondantException(BusinessException):
    status_code = "ADMISSION-12"

    def __init__(self, **kwargs):  # pragma: no cover
        message = _("No pool was found to match.")
        super().__init__(message, **kwargs)
