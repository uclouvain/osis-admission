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
    ARC = _("ARC - Action de Recherche Concertee")
    ARES = _("ARES - Cooperation au developpement")
    CSC = _("CSC - China Scholarship Council")
    FSR = _("FSR - Fonds Speciaux de Recherche")
    ERC = _("ERC - European Research Council")
    FNRS = _("FNRS")
    FONDATION_ST_LUC = _("Fondation St Luc")
    FONDATION_MONT_GODINNE = _("Fondation Mont Godinne")
    FRC = _("FRC - Fonds de recherche clinique")
    FRIA = _("FRIA")
    FRESH = _("FRESH")
    WBI = _("WBI - Wallonie Bruxelles International")
    OTHER = _('OTHER')


class ChoixTypeFinancement(ChoiceEnum):
    WORK_CONTRACT = _('WORK_CONTRACT')
    SEARCH_SCHOLARSHIP = _('SEARCH_SCHOLARSHIP')
    SELF_FUNDING = _('SELF_FUNDING')
