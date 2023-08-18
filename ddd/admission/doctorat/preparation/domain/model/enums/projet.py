# ##############################################################################
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
# ##############################################################################

from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class ChoixStatutPropositionDoctorale(ChoiceEnum):
    EN_BROUILLON = _('In draft form')
    EN_ATTENTE_DE_SIGNATURE = _('Waiting for signature')
    CONFIRMEE = _('Application confirmed (by student)')
    ANNULEE = _('Cancelled application')
    INSCRIPTION_AUTORISEE = _('Application accepted')


STATUTS_PROPOSITION_AVANT_SOUMISSION = {
    ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
    ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
}
STATUTS_PROPOSITION_AVANT_INSCRIPTION = STATUTS_PROPOSITION_AVANT_SOUMISSION | {
    ChoixStatutPropositionDoctorale.CONFIRMEE.name,
}

STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE = STATUTS_PROPOSITION_AVANT_SOUMISSION | {
    ChoixStatutPropositionDoctorale.ANNULEE.name,
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
