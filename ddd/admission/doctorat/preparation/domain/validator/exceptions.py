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
from django.utils import formats
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from osis_common.ddd.interface import BusinessException


class MaximumPropositionsAtteintException(BusinessException):
    status_code = "PROPOSITION-1"

    def __init__(self, maximum, **kwargs):
        message = _("You cannot have more than %(max)s applications in progress at the same time.") % {'max': maximum}
        super().__init__(message, **kwargs)


class DoctoratNonTrouveException(BusinessException):
    status_code = "PROPOSITION-2"

    def __init__(self, **kwargs):
        message = _("No PhD found.")
        super().__init__(message, **kwargs)


class PropositionNonTrouveeException(BusinessException):
    status_code = "PROPOSITION-3"

    def __init__(self, **kwargs):
        message = _("Proposition not found.")
        super().__init__(message, **kwargs)


class GroupeDeSupervisionNonTrouveException(BusinessException):
    status_code = "PROPOSITION-4"

    def __init__(self, **kwargs):
        message = _("Supervision group not found.")
        super().__init__(message, **kwargs)


class CommissionProximiteInconsistantException(BusinessException):
    status_code = "PROPOSITION-5"

    def __init__(self, **kwargs):
        message = _("Proximity commission should be filled in only if the doctorate's entity is CDE, CLSM or CDSS")
        super().__init__(message, **kwargs)


class ContratTravailInconsistantException(BusinessException):
    status_code = "PROPOSITION-6"

    def __init__(self, **kwargs):
        message = _("Work contract should be set when funding type is set to work contract")
        super().__init__(message, **kwargs)


class InstitutionInconsistanteException(BusinessException):
    status_code = "PROPOSITION-7"

    def __init__(self, **kwargs):
        message = _("Institution should be set when PhD has been set to yes or partial")
        super().__init__(message, **kwargs)


class DomaineTheseInconsistantException(BusinessException):
    status_code = "PROPOSITION-8"

    def __init__(self, **kwargs):
        message = _("Thesis field should be set when PhD has been set to yes or partial")
        super().__init__(message, **kwargs)


class PromoteurNonTrouveException(BusinessException):
    status_code = "PROPOSITION-9"

    def __init__(self, **kwargs):
        message = _("Supervisor not found.")
        super().__init__(message, **kwargs)


class MembreCANonTrouveException(BusinessException):
    status_code = "PROPOSITION-10"

    def __init__(self, **kwargs):
        message = _("Membre CA not found.")
        super().__init__(message, **kwargs)


class SignataireNonTrouveException(BusinessException):
    status_code = "PROPOSITION-11"

    def __init__(self, **kwargs):
        message = _("Member of supervision group not found.")
        super().__init__(message, **kwargs)


class SignataireDejaInviteException(BusinessException):
    status_code = "PROPOSITION-12"

    def __init__(self, **kwargs):  # pragma: no cover
        message = _("Member of supervision group already invited.")
        super().__init__(message, **kwargs)


class SignatairePasInviteException(BusinessException):
    status_code = "PROPOSITION-13"

    def __init__(self, **kwargs):
        message = _("Member of supervision group not invited.")
        super().__init__(message, **kwargs)


class MembreSoitInterneSoitExterneException(BusinessException):
    status_code = "PROPOSITION-14"

    def __init__(self, **kwargs):
        message = _("A member should be either internal or external, please check the fields.")
        super().__init__(message, **kwargs)


class DejaMembreException(BusinessException):
    status_code = "PROPOSITION-15"

    def __init__(self, **kwargs):
        message = _("Already a member.")
        super().__init__(message, **kwargs)


class JustificationRequiseException(BusinessException):
    status_code = "PROPOSITION-16"

    def __init__(self, **kwargs):
        message = _("A justification is needed when creating a pre-admission.")
        super().__init__(message, **kwargs)


class DetailProjetNonCompleteException(BusinessException):
    status_code = "PROPOSITION-17"

    def __init__(self, **kwargs):
        message = _("Mandatory fields are missing in the project details of the proposition.")
        super().__init__(message, **kwargs)


class CotutelleNonCompleteException(BusinessException):
    status_code = "PROPOSITION-18"

    def __init__(self, **kwargs):
        message = _("Mandatory fields are missing in the cotutelle.")
        super().__init__(message, **kwargs)


class PromoteurManquantException(BusinessException):
    status_code = "PROPOSITION-19"

    def __init__(self, **kwargs):
        message = _("You must add at least one UCLouvain supervisor in order to request signatures.")
        super().__init__(message, **kwargs)


class MembreCAManquantException(BusinessException):
    status_code = "PROPOSITION-20"

    def __init__(self, **kwargs):
        message = _("You must add at least one CA member in order to request signatures.")
        super().__init__(message, **kwargs)


class CotutelleDoitAvoirAuMoinsUnPromoteurExterneException(BusinessException):
    status_code = "PROPOSITION-21"

    def __init__(self, **kwargs):
        message = _("You must add at least one external supervisor in order to request signatures.")
        super().__init__(message, **kwargs)


class GroupeSupervisionCompletPourPromoteursException(BusinessException):
    status_code = "PROPOSITION-22"

    def __init__(self, **kwargs):
        message = _("There can be no more promoters in the supervision group.")
        super().__init__(message, **kwargs)


class GroupeSupervisionCompletPourMembresCAException(BusinessException):
    status_code = "PROPOSITION-23"

    def __init__(self, **kwargs):
        message = _("There can be no more CA members in the supervision group.")
        super().__init__(message, **kwargs)


class CandidatNonTrouveException(BusinessException):
    status_code = "PROPOSITION-24"

    def __init__(self, **kwargs):
        message = _("Candidate not found.")
        super().__init__(message, **kwargs)


class IdentificationNonCompleteeException(BusinessException):
    status_code = "PROPOSITION-25"

    def __init__(self, **kwargs):
        message = _("Please fill in all the required information in the 'Personal Data > Identification' tab.")
        super().__init__(message, **kwargs)


class NumeroIdentiteNonSpecifieException(BusinessException):
    status_code = "PROPOSITION-26"

    def __init__(self, **kwargs):
        message = _("Please specify at least one identity number.")
        super().__init__(message, **kwargs)


class NumeroIdentiteBelgeNonSpecifieException(BusinessException):
    status_code = "PROPOSITION-27"

    def __init__(self, **kwargs):
        message = _("Please specify your Belgian national register number.")
        super().__init__(message, **kwargs)


class DateOuAnneeNaissanceNonSpecifieeException(BusinessException):
    status_code = "PROPOSITION-28"

    def __init__(self, **kwargs):
        message = _("Please specify either your date of birth or your year of birth.")
        super().__init__(message, **kwargs)


class DetailsPasseportNonSpecifiesException(BusinessException):
    status_code = "PROPOSITION-29"

    def __init__(self, **kwargs):
        message = _("Please provide a copy of your passport.")
        super().__init__(message, **kwargs)


class CarteIdentiteeNonSpecifieeException(BusinessException):
    status_code = "PROPOSITION-30"

    def __init__(self, **kwargs):
        message = _("Please provide a copy of your identity card.")
        super().__init__(message, **kwargs)


class AdresseDomicileLegalNonCompleteeException(BusinessException):
    status_code = "PROPOSITION-31"

    def __init__(self, **kwargs):
        message = _("Please fill in all the required information in the 'Personal Data > Coordinates' tab.")
        super().__init__(message, **kwargs)


class AdresseCorrespondanceNonCompleteeException(BusinessException):
    status_code = "PROPOSITION-32"

    def __init__(self, **kwargs):
        message = _("Please fill in all the required information related to your contact address.")
        super().__init__(message, **kwargs)


class LanguesConnuesNonSpecifieesException(BusinessException):
    status_code = "PROPOSITION-33"

    def __init__(self, **kwargs):
        message = _(
            "Please fill in all the required information in the 'Previous experience > Knowledge of languages' tab.",
        )
        super().__init__(message, **kwargs)


class FichierCurriculumNonRenseigneException(BusinessException):
    status_code = "PROPOSITION-34"

    def __init__(self, **kwargs):
        message = _("Please provide a copy of your curriculum.")
        super().__init__(message, **kwargs)


class AnneesCurriculumNonSpecifieesException(BusinessException):
    status_code = "PROPOSITION-35"

    def __init__(self, periode_manquante, **kwargs):
        self.periode = periode_manquante
        message = (
            _("From %(debut_periode)s to %(fin_periode)s")
            % {
                'debut_periode': capfirst(formats.date_format(periode_manquante[0], 'YEAR_MONTH_FORMAT')),
                'fin_periode': capfirst(formats.date_format(periode_manquante[1], 'YEAR_MONTH_FORMAT')),
            }
            if periode_manquante[0] != periode_manquante[1]
            else capfirst(formats.date_format(periode_manquante[0], "YEAR_MONTH_FORMAT"))
        )
        super().__init__(message, **kwargs)


class ProcedureDemandeSignatureNonLanceeException(BusinessException):
    status_code = "PROPOSITION-36"

    def __init__(self, **kwargs):
        message = _("The signature request procedure isn't in progress.")
        super().__init__(message, **kwargs)


class PropositionNonApprouveeParPromoteurException(BusinessException):
    status_code = "PROPOSITION-37"

    def __init__(self, **kwargs):
        message = _("All supervisors must have approved the proposition.")
        super().__init__(message, **kwargs)


class PropositionNonApprouveeParMembresCAException(BusinessException):
    status_code = "PROPOSITION-38"

    def __init__(self, **kwargs):
        message = _("All CA members must have approved the proposition.")
        super().__init__(message, **kwargs)


class InstitutTheseObligatoireException(BusinessException):
    status_code = "PROPOSITION-39"

    def __init__(self, **kwargs):
        message = _("Thesis institute must be set.")
        super().__init__(message, **kwargs)


class NomEtPrenomNonSpecifiesException(BusinessException):
    status_code = "PROPOSITION-40"

    def __init__(self, **kwargs):
        message = _("Please fill in at least your last or first name.")
        super().__init__(message, **kwargs)


class SpecifierNOMASiDejaInscritException(BusinessException):
    status_code = "PROPOSITION-41"

    def __init__(self, **kwargs):
        message = _("Please specify your old NOMA (matriculation number).")
        super().__init__(message, **kwargs)


class PromoteurDeReferenceManquantException(BusinessException):
    status_code = "PROPOSITION-42"

    def __init__(self, **kwargs):
        message = _("You must set a lead supervisor.")
        super().__init__(message, **kwargs)


class AbsenceDeDetteNonCompleteeException(BusinessException):
    status_code = "PROPOSITION-43"

    def __init__(self, **kwargs):
        message = _(
            "Some fields are missing in the 'Absence of debt' block in the 'Additional information > Accounting' tab."
        )
        super().__init__(message, **kwargs)


class ReductionDesDroitsInscriptionNonCompleteeException(BusinessException):
    status_code = "PROPOSITION-44"

    def __init__(self, **kwargs):
        message = _(
            "Some fields are missing in the 'Reduced tuition fee' block in the 'Additional information > "
            "Accounting' tab."
        )
        super().__init__(message, **kwargs)


class AssimilationNonCompleteeException(BusinessException):
    status_code = "PROPOSITION-45"

    def __init__(self, **kwargs):
        message = _(
            "Some fields are missing in the 'Belgian student status' block in the 'Additional information > Accounting'"
            " tab.",
        )
        super().__init__(message, **kwargs)


class AffiliationsNonCompleteesException(BusinessException):
    status_code = "PROPOSITION-46"

    def __init__(self, **kwargs):
        message = _(
            "Some fields are missing in the 'Memberships' block in the 'Additional information > Accounting' tab."
        )
        super().__init__(message, **kwargs)


class CarteBancaireRemboursementIbanNonCompleteException(BusinessException):
    status_code = "PROPOSITION-47"

    def __init__(self, **kwargs):
        message = _(
            "Some fields related to the bank account number in IBAN format are missing in the 'Additional "
            "information > Accounting' tab."
        )
        super().__init__(message, **kwargs)


class CarteBancaireRemboursementAutreFormatNonCompleteException(BusinessException):
    status_code = "PROPOSITION-48"

    def __init__(self, **kwargs):
        message = _(
            "Some fields related to the bank account are missing in the 'Additional information > Accounting' tab."
        )
        super().__init__(message, **kwargs)


class ExperiencesAcademiquesNonCompleteesException(BusinessException):
    status_code = "PROPOSITION-49"

    def __init__(self, reference, name, **kwargs):
        self.reference = reference
        message = _("The educational experience '%(education_name)s' is not completed.") % {'education_name': name}
        super().__init__(message, **kwargs)


class TypeCompteBancaireRemboursementNonCompleteException(BusinessException):
    status_code = "PROPOSITION-50"

    def __init__(self, **kwargs):
        message = _(
            "You haven't answered to the question about your bank account in the 'Additional information > "
            "Accounting' tab."
        )
        super().__init__(message, **kwargs)


class CoordonneesNonCompleteesException(BusinessException):
    status_code = "PROPOSITION-51"

    def __init__(self, **kwargs):
        message = _("Please fill in all the required information in the 'Personal Data > Coordinates' tab.")
        super().__init__(message, **kwargs)


class ProcedureDemandeSignatureLanceeException(BusinessException):
    status_code = "PROPOSITION-52"

    def __init__(self, **kwargs):
        message = _("The signature request procedure is already in progress.")
        super().__init__(message, **kwargs)


class MembreNonExterneException(BusinessException):
    status_code = "PROPOSITION-14"

    def __init__(self, **kwargs):
        message = _("The member is not external.")
        super().__init__(message, **kwargs)
