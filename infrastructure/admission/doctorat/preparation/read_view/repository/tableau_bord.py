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

from django.db.models import Exists, F, OuterRef
from django.db.models.functions import Now
from django.db.models.lookups import GreaterThanOrEqual
from django.db.models.query_utils import Q

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
)
from admission.ddd.admission.doctorat.preparation.read_view.domain.enums.tableau_bord import (
    IndicateurTableauBordEnum,
)
from admission.ddd.admission.doctorat.preparation.read_view.repository.i_tableau_bord import (
    ITableauBordRepositoryAdmissionMixin,
)
from admission.models import DoctorateAdmission
from admission.models.functions import AddMonths
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.inscription_programme_annuel import InscriptionProgrammeAnnuel


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
        IndicateurTableauBordEnum.PRE_ADMISSION_PAS_EN_ORDRE_INSCRIPTION.name: Q(
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
        )
        & Q(
            ~Exists(
                InscriptionProgrammeAnnuel.objects.filter(
                    admission_uuid=OuterRef('uuid'),
                    etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
                )
            ),
        ),
        IndicateurTableauBordEnum.PRE_ADMISSION_ECHEANCE_3_MOIS.name: Q(
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            approved_by_cdd_at__isnull=False,
        )
        & Q(
            GreaterThanOrEqual(
                Now(),
                AddMonths(F('approved_by_cdd_at'), months=9),
            ),
            ~Exists(
                DoctorateAdmission.objects.filter(
                    related_pre_admission_id=OuterRef('pk'),
                    status__in=STATUTS_PROPOSITION_DOCTORALE_SOUMISE,
                )
            ),
        ),
        IndicateurTableauBordEnum.ADMISSION_DOSSIER_SOUMIS.name: Q(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            type=ChoixTypeAdmission.ADMISSION.name,
        ),
        IndicateurTableauBordEnum.ADMISSION_AUTORISE_SIC.name: Q(
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
            type=ChoixTypeAdmission.ADMISSION.name,
        ),
        IndicateurTableauBordEnum.ADMISSION_PAS_EN_ORDRE_INSCRIPTION.name: Q(
            type=ChoixTypeAdmission.ADMISSION.name,
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
        )
        & Q(
            ~Exists(
                InscriptionProgrammeAnnuel.objects.filter(
                    admission_uuid=OuterRef('uuid'),
                    etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
                )
            ),
        ),
    }
