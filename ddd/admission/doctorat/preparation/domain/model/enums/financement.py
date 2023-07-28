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


class ChoixTypeContratTravail(ChoiceEnum):
    UCLOUVAIN_SCIENTIFIC_STAFF = _('UCLOUVAIN_SCIENTIFIC_STAFF')
    OTHER = _('OTHER')


class BourseRecherche(ChoiceEnum):
    ARC = _("Joint research project (ARC)")
    ARES = _("Development cooperation (ARES)")
    CSC = _("China Scholarship Council (CSC)")
    FSR = _("Fonds Speciaux de Recherche (FSR)")
    ERC = _("European Research Council (ERC)")
    FNRS = _("FNRS")
    FONDATION_ST_LUC = _("Fondation Saint-Luc")
    FONDATION_MONT_GODINNE = _("Fondation Mont-Godinne")
    FRC = _("Clinical Research Fund (FRC)")
    FRIA = _("FRIA")
    FRESH = _("FRESH")
    WBI = _("Wallonie Bruxelles International (WBI)")
    OTHER = _('OTHER')


class ChoixTypeFinancement(ChoiceEnum):
    WORK_CONTRACT = _('WORK_CONTRACT')
    SEARCH_SCHOLARSHIP = _('SEARCH_SCHOLARSHIP')
    SELF_FUNDING = _('SELF_FUNDING')
