# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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


class ChoixStatutProposition(ChoiceEnum):
    CANCELLED = _('CANCELLED')
    # During the enrolment step
    IN_PROGRESS = _('IN_PROGRESS')
    SUBMITTED = _('SUBMITTED')
    SIGNING_IN_PROGRESS = _('SIGNING_IN_PROGRESS')
    # After the enrolment step
    ENROLLED = _('ENROLLED')


STATUTS_PROPOSITION_AVANT_SOUMISSION = {
    ChoixStatutProposition.IN_PROGRESS.name,
    ChoixStatutProposition.SIGNING_IN_PROGRESS.name,
}

STATUTS_PROPOSITION_AVANT_INSCRIPTION = STATUTS_PROPOSITION_AVANT_SOUMISSION | {
    ChoixStatutProposition.SUBMITTED.name,
}


class ChoixStatutSignatureGroupeDeSupervision(ChoiceEnum):
    IN_PROGRESS = _('IN_PROGRESS')
    SIGNING_IN_PROGRESS = _('SIGNING_IN_PROGRESS')


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


class TypeItemFormulaire(ChoiceEnum):
    MESSAGE = _('Message')
    TEXTE = _('Text')
    DOCUMENT = _('Document')


TYPES_ITEMS_LECTURE_SEULE = {
    TypeItemFormulaire.MESSAGE.name,
}


class TypeChampTexteFormulaire(ChoiceEnum):
    COURT = _('Short')
    LONG = _('Long')


VALID_FORM_ITEM_TEXT_TYPES = {
    TypeChampTexteFormulaire.COURT.name,
    TypeChampTexteFormulaire.LONG.name,
}


class CleConfigurationItemFormulaire(ChoiceEnum):
    TAILLE_TEXTE = _('Text size')
    CLASSE_CSS = _('CSS class')
    TYPES_MIME_FICHIER = _('File MIME types')
    NOMBRE_MAX_DOCUMENTS = _('Maximum number of documents')
