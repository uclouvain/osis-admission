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

from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from osis_common.ddd.interface import BusinessException


class FormationNonTrouveeException(BusinessException):
    status_code = "FORMATION-GENERALE-1"

    def __init__(self, **kwargs):
        message = _("No training found.")
        super().__init__(message, **kwargs)


class PropositionNonTrouveeException(BusinessException):
    status_code = "FORMATION-GENERALE-2"

    def __init__(self, **kwargs):
        message = _("Proposition not found.")
        super().__init__(message, **kwargs)


class EtudesSecondairesNonCompleteesException(BusinessException):
    status_code = "FORMATION-GENERALE-3"

    def __init__(self, **kwargs):
        message = _("Secondary studies must be completed.")
        super().__init__(message, **kwargs)


class FichierCurriculumNonRenseigneException(BusinessException):
    status_code = "FORMATION-GENERALE-4"

    def __init__(self, **kwargs):
        message = _("Please provide a copy of your curriculum.")
        super().__init__(message, **kwargs)


class EquivalenceNonRenseigneeException(BusinessException):
    status_code = "FORMATION-GENERALE-5"

    def __init__(self, **kwargs):
        message = _(
            "Please provide a copy of your decision of equivalence for your diploma(s) giving access to the training."
        )
        super().__init__(message, **kwargs)


class EtudesSecondairesNonCompleteesPourDiplomeBelgeException(BusinessException):
    status_code = "FORMATION-GENERALE-8"

    def __init__(self, **kwargs):
        message = _("Some information about the Belgian diploma of the secondary studies are missing.")
        super().__init__(message, **kwargs)


class EtudesSecondairesNonCompleteesPourDiplomeEtrangerException(BusinessException):
    status_code = "FORMATION-GENERALE-9"

    def __init__(self, **kwargs):
        message = _("Some information about the foreign diploma of the secondary studies are missing.")
        super().__init__(message, **kwargs)


class EtudesSecondairesNonCompleteesPourAlternativeException(BusinessException):
    status_code = "FORMATION-GENERALE-10"

    def __init__(self, **kwargs):
        message = _("Some information about the alternative to the secondary studies are missing.")
        super().__init__(message, **kwargs)


class PropositionPourPaiementInvalideException(BusinessException):
    status_code = "FORMATION-GENERALE-11"

    def __init__(self, **kwargs):
        message = _("The proposition must not be concerned by the payment.")
        super().__init__(message, **kwargs)


class PropositionDoitEtreEnAttenteDePaiementException(BusinessException):
    status_code = "FORMATION-GENERALE-12"

    def __init__(self, **kwargs):
        message = _("The proposition must be concerned by the payment.")
        super().__init__(message, **kwargs)


class StatutPropositionInvalidePourPaiementInscriptionException(BusinessException):
    status_code = "FORMATION-GENERALE-13"

    def __init__(self, current_status, **kwargs):
        message = _(
            'The status of the request is currently "{current_status}". Only the status "{from_status}" allows you '
            'to move to the "{to_status}" status for the application fees.'
        ).format(
            current_status=current_status,
            from_status=ChoixStatutPropositionGenerale.CONFIRMEE.value,
            to_status=_("Must pay"),
        )
        super().__init__(message, **kwargs)


class PaiementNonRealiseException(BusinessException):
    status_code = "FORMATION-GENERALE-14"

    def __init__(self, **kwargs):
        message = _("The payment has not been made.")
        super().__init__(message, **kwargs)
