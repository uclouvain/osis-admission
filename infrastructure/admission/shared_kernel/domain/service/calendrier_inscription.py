# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from datetime import date
from typing import List, Optional, Tuple

from django.db.models import Q

from admission.ddd.admission.shared_kernel.domain.model.periode import Periode
from admission.ddd.admission.shared_kernel.domain.service.i_calendrier_inscription import (
    ICalendrierInscription,
)
from admission.ddd.admission.shared_kernel.dtos import IdentificationDTO
from admission.ddd.admission.shared_kernel.dtos.periode import PeriodeDTO
from admission.infrastructure.admission.shared_kernel.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from osis_profile import PLUS_5_ISO_CODES


class CalendrierInscription(ICalendrierInscription):
    @classmethod
    def get_annees_academiques_pour_calcul(cls, type_formation: TrainingType) -> Tuple[List[int], List[int]]:
        year = AnneeInscriptionFormationTranslator().recuperer_annee_selon_type_formation(type_formation)
        return ([year - 1, year], [year, year - 1, year + 1, year + 2])

    @classmethod
    def get_pool_ouverts(cls) -> List[Tuple[str, int]]:
        today = date.today()
        return AcademicCalendar.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
        ).values_list('reference', 'data_year__year')

    @classmethod
    def recuperer_periode_inscription_specifique_medecine_dentisterie(
        cls,
        annee: Optional[int],
    ) -> Optional[PeriodeDTO]:
        qs = AcademicCalendar.objects.filter(
            reference=AcademicCalendarTypes.ADMISSION_MEDICINE_DENTISTRY_BACHELOR_ENROLLMENT.name,
        )

        if annee:
            # Récupération de la période de l'année en question
            qs = qs.filter(data_year__year=annee)
        else:
            # Récupération de la période courante si existante, sinon de la prochaine
            today = date.today()
            qs = qs.filter(Q(start_date__lte=today, end_date__gte=today) | Q(start_date__gt=today))

        academic_calendar = qs.order_by('start_date')[:1]

        if academic_calendar:
            return PeriodeDTO(date_debut=academic_calendar[0].start_date, date_fin=academic_calendar[0].end_date)

    @classmethod
    def recuperer_periode_du_pot(
        cls,
        annee_formation: int,
        pot: AcademicCalendarTypes,
    ) -> Periode:
        academic_calendar = AcademicCalendar.objects.get(
            reference=pot.name,
            data_year__year=annee_formation,
        )
        return Periode(
            date_debut=academic_calendar.start_date,
            date_fin=academic_calendar.end_date,
            type=pot.name,
        )

    @classmethod
    def est_ue_plus_5(
        cls,
        identification: 'IdentificationDTO',
    ) -> bool:
        return identification.pays_nationalite_europeen or identification.pays_nationalite in PLUS_5_ISO_CODES
