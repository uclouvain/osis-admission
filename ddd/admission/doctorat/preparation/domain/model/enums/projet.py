# ##############################################################################
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
# ##############################################################################
import itertools
from typing import Iterable

from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class ChoixStatutPropositionDoctorale(ChoiceEnum):
    EN_BROUILLON = _('In draft form')
    EN_ATTENTE_DE_SIGNATURE = _('Waiting for signature')
    CONFIRMEE = _('Application confirmed')
    ANNULEE = _('Cancelled application')

    TRAITEMENT_FAC = _('Processing by Fac')
    A_COMPLETER_POUR_FAC = _('To be completed for Fac')
    COMPLETEE_POUR_FAC = _('Completed for Fac')
    RETOUR_DE_FAC = _('Feedback from Fac')

    A_COMPLETER_POUR_SIC = _('To be completed for the Enrolment Office (SIC)')
    COMPLETEE_POUR_SIC = _('Completed for SIC')
    ATTENTE_VALIDATION_DIRECTION = _('Awaiting management approval')

    CLOTUREE = _('Closed')
    INSCRIPTION_AUTORISEE = _('Application accepted')
    INSCRIPTION_REFUSEE = _('Application denied')

    @classmethod
    def get_specific_values(cls, keys: Iterable[str]):
        return ', '.join([str(getattr(cls, key).value) for key in keys])


STATUTS_PROPOSITION_AVANT_SOUMISSION = {
    ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
    ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
}

STATUTS_PROPOSITION_AVANT_INSCRIPTION = STATUTS_PROPOSITION_AVANT_SOUMISSION | {
    ChoixStatutPropositionDoctorale.CONFIRMEE.name,
    ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
    ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name,
    ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC.name,
    ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name,
    ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC.name,
    ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name,
    ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION.name,
}

STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE = STATUTS_PROPOSITION_AVANT_SOUMISSION | {
    ChoixStatutPropositionDoctorale.ANNULEE.name,
}

STATUTS_PROPOSITION_DOCTORALE_SOUMISE = (
    set(ChoixStatutPropositionDoctorale.get_names()) - STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE
)

STATUTS_PROPOSITION_DOCTORALE_PEU_AVANCEE = {
    ChoixStatutPropositionDoctorale.ANNULEE.name,
    ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
}

# Le gestionnaire FAC a la main
STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC = {
    ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC.name,
    ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
}

# Le gestionnaire FAC a la main ou attend une réponse du candidat
STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC_ETENDUS = STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC | {
    ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name,
}

# Le gestionnaire SIC a la main
STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC = {
    ChoixStatutPropositionDoctorale.CONFIRMEE.name,
    ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name,
    ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name,
    ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION.name,
    ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
    ChoixStatutPropositionDoctorale.INSCRIPTION_REFUSEE.name,
    ChoixStatutPropositionDoctorale.CLOTUREE.name,
}

# Le gestionnaire SIC a la main et peut envoyer le dossier à la faculté pour que celle-ci donne sa décision
STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_FAC_POUR_DECISION = {
    ChoixStatutPropositionDoctorale.CONFIRMEE.name,
    ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name,
    ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name,
}


# Le gestionnaire SIC a la main ou attend une réponse du candidat
STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC_ETENDUS = STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC | {
    ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC.name,
}

# Le candidat doit répondre à une demande du système ou d'un gestionnaire
STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CANDIDAT = {
    ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC.name,
    ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name,
}


class ChoixCommissionProximiteCDEouCLSM(ChoiceEnum):
    ECONOMY = _('ECONOMY')
    MANAGEMENT = _('MANAGEMENT')


class ChoixCommissionProximiteCDSS(ChoiceEnum):
    ECLI = _("Proximity commission for experimental and clinical research (ECLI)")
    GIM = _("Proximity Commission for Genetics and Immunology (GIM)")
    NRSC = _("Proximity Commission for Neuroscience (NRSC)")
    BCM = _("Proximity commission for cellular and molecular biology, biochemistry (BCM)")
    SPSS = _("Proximity commission for public health, health and society (SPSS)")
    DENT = _("Proximity Commission for Dental Sciences (DENT)")
    DFAR = _("Proximity Commission for Pharmaceutical Sciences (DFAR)")
    MOTR = _("Proximity Commission for Motricity Sciences (MOTR)")


class ChoixSousDomaineSciences(ChoiceEnum):
    PHYSICS = _("PHYSICS")
    CHEMISTRY = _("CHEMISTRY")
    MATHEMATICS = _("MATHEMATICS")
    STATISTICS = _("STATISTICS")
    BIOLOGY = _("BIOLOGY")
    GEOGRAPHY = _("GEOGRAPHY")


TOUS_CHOIX_COMMISSION_PROXIMITE = {
    enum_item.name: enum_item.value
    for enum_item in itertools.chain(
        ChoixCommissionProximiteCDEouCLSM,
        ChoixCommissionProximiteCDSS,
        ChoixSousDomaineSciences,
    )
}


class ChoixTypeAdmission(ChoiceEnum):
    ADMISSION = _('ADMISSION')
    PRE_ADMISSION = _('PRE_ADMISSION')


class ChoixLangueRedactionThese(ChoiceEnum):
    FRENCH = _('French')
    ENGLISH = _('English')
    OTHER = _('Other')
    UNDECIDED = _('Undecided')


class ChoixDoctoratDejaRealise(ChoiceEnum):
    YES = _('YES')
    NO = _('NO')
    PARTIAL = _('PARTIAL')
