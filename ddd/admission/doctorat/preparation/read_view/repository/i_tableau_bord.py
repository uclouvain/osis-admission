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
from typing import List

from django.utils.translation import pgettext_lazy

from osis_common.ddd import interface
from admission.ddd.admission.doctorat.preparation.read_view.domain.enums.tableau_bord import (
    CategorieTableauBordEnum,
    IndicateurTableauBordEnum,
    TypeCategorieTableauBord,
)
from admission.ddd.admission.doctorat.preparation.read_view.domain.model.tableau_bord import (
    CategorieTableauBord,
    IndicateurTableauBord,
)


class ITableauBordRepositoryAdmissionMixin(interface.ReadModelRepository, metaclass=ABCMeta):
    categories_admission: List[CategorieTableauBord] = [
        CategorieTableauBord(
            id=CategorieTableauBordEnum.PRE_ADMISSION,
            libelle=pgettext_lazy('dashboard-category', 'Pre-admission'),
            type=TypeCategorieTableauBord.ADMISSION,
            indicateurs=[
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.PRE_ADMISSION_DOSSIER_SOUMIS,
                    libelle=pgettext_lazy('dashboard-indicator pre-admission', 'Submitted dossiers'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.PRE_ADMISSION_AUTORISE_SIC,
                    libelle=pgettext_lazy('dashboard-indicator pre-admission', 'Authorized SIC'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.PRE_ADMISSION_PAS_EN_ORDRE_INSCRIPTION,
                    libelle=pgettext_lazy('dashboard-indicator pre-admission', 'Not in order of registration'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.PRE_ADMISSION_ECHEANCE_3_MOIS,
                    libelle=pgettext_lazy('dashboard-indicator pre-admission', 'Deadline 3 months'),
                ),
            ],
        ),
        CategorieTableauBord(
            id=CategorieTableauBordEnum.ADMISSION,
            libelle=pgettext_lazy('dashboard-category', 'Admission'),
            type=TypeCategorieTableauBord.ADMISSION,
            indicateurs=[
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.ADMISSION_DOSSIER_SOUMIS,
                    libelle=pgettext_lazy('dashboard-indicator admission', 'Submitted dossiers'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.ADMISSION_AUTORISE_SIC,
                    libelle=pgettext_lazy('dashboard-indicator admission', 'Authorized SIC'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.ADMISSION_PAS_EN_ORDRE_INSCRIPTION,
                    libelle=pgettext_lazy('dashboard-indicator admission', 'Not in order of registration'),
                ),
            ],
        ),
    ]

    libelles_indicateurs_admission = {
        indicateur.id.name: f'{categorie.libelle} - {indicateur.libelle}'
        for categorie in categories_admission
        for indicateur in categorie.indicateurs
    }
