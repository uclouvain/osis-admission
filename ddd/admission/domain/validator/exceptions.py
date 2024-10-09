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
from typing import Optional

from django.utils.translation import gettext_lazy as _

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
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
        message = _("Mandatory fields are missing in the specific questions of the 'Course choice' tab")
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
        message = _("You must answer the question about external enrollment change.")
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


class PoolOuAnneeDifferentException(BusinessException):
    status_code = "ADMISSION-13"

    def __init__(
        self,
        annee_calculee: Optional[int],
        pool_calcule: Optional['AcademicCalendarTypes'],
        annee_soumise: int,
        pool_soumis: 'AcademicCalendarTypes',
        **kwargs,
    ):
        message = _("The resulting calculated academic year or pool is not consistent.")
        self.annee_calculee = annee_calculee
        self.pool_calcule = pool_calcule
        self.annee_soumise = annee_soumise
        self.pool_soumis = pool_soumis
        super().__init__(message, **kwargs)


class ElementsConfirmationNonConcordants(BusinessException):
    status_code = "ADMISSION-14"

    def __init__(self, **kwargs):
        message = _("The submitted information is not consistent with information requested.")
        super().__init__(message, **kwargs)


class NombrePropositionsSoumisesDepasseException(BusinessException):
    status_code = "ADMISSION-15"


class PropositionNonTrouveeException(BusinessException):
    status_code = "ADMISSION-16"

    def __init__(self, **kwargs):
        message = _("Proposition not found.")
        super().__init__(message, **kwargs)


class EmplacementDocumentNonTrouveException(BusinessException):
    status_code = "ADMISSION-17"

    def __init__(self, **kwargs):
        message = _("Document not found.")
        super().__init__(message, **kwargs)


class DocumentsCompletesDifferentsDesReclamesException(BusinessException):
    status_code = "ADMISSION-18"

    def __init__(self, **kwargs):
        message = _("The completed documents are different from the ones that are requested.")
        super().__init__(message, **kwargs)


class PosteDiplomatiqueNonTrouveException(BusinessException):
    status_code = "ADMISSION-19"

    def __init__(self, **kwargs):
        message = _("No diplomatic post found.")
        super().__init__(message, **kwargs)


class ResidenceAuSensDuDecretNonDisponiblePourInscriptionException(BusinessException):
    status_code = "ADMISSION-20"
    message = _(
        'As you are applying for a limited course as a non-resident (as defined by government decree) candidate, '
        'applications for the 2024-2025 academic year must be submitted via this '
        '<a href="https://uclouvain.be/fr/etudier/inscriptions/demande-en-ligne" target="_blank">'
        'specific platform</a>.'
    )

    def __init__(self, **kwargs):
        super().__init__(self.message, **kwargs)


class DocumentsReclamesImmediatementNonCompletesException(BusinessException):
    status_code = "ADMISSION-21"

    def __init__(self, **kwargs):
        message = _("The requested documents immediately are not completed.")
        super().__init__(message, **kwargs)


class ExperienceNonTrouveeException(BusinessException):
    status_code = "ADMISSION-22"
    message = _("Experience not found.")

    def __init__(self, **kwargs):
        super().__init__(self.message, **kwargs)


class NotInAccountCreationPeriodException(BusinessException):
    status_code = "FUSION-DIGIT-4"

    def __init__(self, matricule_candidat, **kwargs):
        message = _("[%(matricule_candidat)s] Account creation period calendar is closed") % {
            "matricule_candidat": matricule_candidat
        }
        super().__init__(message, **kwargs)


class AdmissionDansUnStatutPasAutoriseASInscrireException(BusinessException):
    status_code = "FUSION-DIGIT-5"

    def __init__(self, matricule_candidat, **kwargs):
        message = _("[%(matricule_candidat)s] Type is admission and application is not accepted") % {
            "matricule_candidat": matricule_candidat
        }
        super().__init__(message, **kwargs)


class PropositionFusionATraiterException(BusinessException):
    status_code = "FUSION-DIGIT-6"

    def __init__(self, merge_status, matricule_candidat, **kwargs):
        message = _("[%(matricule_candidat)s] Candidate has pending merge proposal: status %(merge_status)s") % {
            "merge_status": merge_status,
            "matricule_candidat": matricule_candidat,
        }
        super().__init__(message, **kwargs)


class ValidationTicketCreationDigitEchoueeException(BusinessException):
    status_code = "FUSION-DIGIT-7"
    message = _("An error occured during digit ticket creation validation")

    def __init__(self, **kwargs):
        super().__init__(self.message, **kwargs)


class PasDePropositionDeFusionTrouveeException(BusinessException):
    status_code = "FUSION-DIGIT-10"

    def __init__(self, **kwargs):
        message = _("Ressource not found.")
        super().__init__(message, **kwargs)


class PropositionDeFusionAvecValidationSyntaxiqueInvalideException(BusinessException):
    status_code = "FUSION-DIGIT-11"

    def __init__(self, matricule_candidat, **kwargs):
        message = _("[%(matricule_candidat)s] Candidate has merge proposal with error in syntax validation") % {
            "matricule_candidat": matricule_candidat,
        }
        super().__init__(message, **kwargs)


class PasDePropositionFusionPersonneTrouveeException(BusinessException):
    status_code = "FUSION-DIGIT-12"

    def __init__(self, **kwargs):
        message = _("Ressource not found.")
        super().__init__(message, **kwargs)


class EnQuarantaineException(BusinessException):
    status_code = "ADMISSION-23"
    message = _("The person is in quarantine.")

    def __init__(self, **kwargs):
        super().__init__(self.message, **kwargs)
