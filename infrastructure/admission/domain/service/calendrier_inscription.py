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
from datetime import date
from typing import List, Tuple

from admission.ddd.admission.domain.service.i_calendrier_inscription import ICalendrierInscription
from admission.ddd.admission.enums import TypeSituationAssimilation
from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import AcademicYear
from reference.models.country import Country


class CalendrierInscription(ICalendrierInscription):
    @classmethod
    def get_annees_academiques_pour_calcul(cls) -> List[int]:
        current = AcademicYear.objects.current()
        return [current.year, current.year - 1, current.year + 1]

    @classmethod
    def get_pool_ouverts(cls) -> List[Tuple[str, int]]:
        today = date.today()
        return AcademicCalendar.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
        ).values_list('reference', 'data_year__year')

    @classmethod
    def est_ue_plus_5(
        cls,
        pays_nationalite_iso_code: str,
        situation_assimilation: TypeSituationAssimilation = None,
    ) -> bool:
        return (
            pays_nationalite_iso_code in cls.PLUS_5_ISO_CODES
            or (situation_assimilation and situation_assimilation != TypeSituationAssimilation.AUCUNE_ASSIMILATION)
            or Country.objects.get(iso_code=pays_nationalite_iso_code).european_union
        )
