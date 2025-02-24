# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from abc import ABCMeta

from django.db.models.query_utils import Q

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
)
from admission.ddd.admission.doctorat.preparation.read_view.domain.enums.tableau_bord import IndicateurTableauBordEnum
from admission.ddd.admission.doctorat.preparation.read_view.repository.i_tableau_bord import (
    ITableauBordRepositoryAdmissionMixin,
)


class TableauBordRepositoryAdmissionMixin(ITableauBordRepositoryAdmissionMixin, metaclass=ABCMeta):
    ADMISSION_DJANGO_FILTER_BY_INDICATOR = {
        IndicateurTableauBordEnum.PRE_ADMISSION_DOSSIER_SOUMIS.name: Q(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
        ),
        IndicateurTableauBordEnum.PRE_ADMISSION_AUTORISE_SIC.name: Q(
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
        ),
        # IndicateurTableauBordEnum.PRE_ADMISSION_PAS_EN_ORDRE_INSCRIPTION.name: Q(),
        # IndicateurTableauBordEnum.PRE_ADMISSION_ECHEANCE_3_MOIS.name: Q(),
        IndicateurTableauBordEnum.ADMISSION_DOSSIER_SOUMIS.name: Q(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            type=ChoixTypeAdmission.ADMISSION.name,
        ),
        IndicateurTableauBordEnum.ADMISSION_AUTORISE_SIC.name: Q(
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
            type=ChoixTypeAdmission.ADMISSION.name,
        ),
        # IndicateurTableauBordEnum.ADMISSION_PAS_EN_ORDRE_INSCRIPTION.name: Q(),
    }
