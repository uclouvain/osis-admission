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
from datetime import date, timedelta
from typing import List, Tuple, Optional

from admission.constants import CONTEXT_GENERAL, CONTEXT_DOCTORATE, CONTEXT_CONTINUING
from admission.ddd.admission.domain.service.i_annee_inscription_formation import IAnneeInscriptionFormationTranslator
from admission.ddd.admission.domain.service.i_calendrier_inscription import ICalendrierInscription
from admission.ddd.admission.dtos import IdentificationDTO
from admission.ddd.admission.enums import TypeSituationAssimilation
from admission.infrastructure.admission.domain.service.in_memory.annee_inscription_formation import (
    AnneeInscriptionFormationInMemoryTranslator,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import get_current_year
from osis_profile import PLUS_5_ISO_CODES


class CalendrierInscriptionInMemory(ICalendrierInscription):
    periodes_ouvertes = {
        pool.event_reference: (
            pool.cutover_date,
            getattr(pool, 'end_date', None),
        )
        for pool in ICalendrierInscription.all_pools
    }

    @classmethod
    def get_annees_academiques_pour_calcul(cls, type_formation: TrainingType) -> Tuple[List[int], List[int]]:
        from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
            ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE,
        )

        current_year = AnneeInscriptionFormationInMemoryTranslator.recuperer(
            {
                CONTEXT_GENERAL: AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT,
                CONTEXT_DOCTORATE: AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT,
                CONTEXT_CONTINUING: AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT,
            }[ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE[type_formation.name]]
        )

        return (
            [current_year - 1, current_year],
            [current_year, current_year - 1, current_year + 1, current_year + 2],
        )

    @classmethod
    def get_pool_ouverts(cls) -> List[Tuple[str, int]]:
        opened = []
        today = date.today()
        annees = [today.year, today.year - 1, today.year + 1, today.year + 2]
        for pool_name, dates in cls.periodes_ouvertes.items():
            for annee in annees:
                date_debut, date_fin = cls._get_dates_completes(annee, dates[0], dates[1])
                if date_debut <= today <= date_fin:
                    opened.append((pool_name, annee))
        return opened

    @classmethod
    def get_dates_pool(cls, pool_name, annee) -> Tuple[date, date]:
        debut, fin = cls.periodes_ouvertes.get(pool_name)
        return cls._get_dates_completes(annee, debut, fin)

    @classmethod
    def _get_dates_completes(cls, annee, debut, fin):
        date_debut = date(annee + debut.annee, debut.mois, debut.jour)
        if fin is None:
            date_fin = date_debut.replace(year=date_debut.year + 1) - timedelta(days=1)
        else:
            date_fin = date(annee + fin.annee, fin.mois, fin.jour)
        return date_debut, date_fin

    @classmethod
    def est_ue_plus_5(
        cls,
        identification: 'IdentificationDTO',
        situation_assimilation: TypeSituationAssimilation = None,
    ) -> bool:
        return identification.pays_nationalite in (
            ProfilCandidatInMemoryTranslator.pays_union_europeenne | PLUS_5_ISO_CODES
        ) or (situation_assimilation and situation_assimilation != TypeSituationAssimilation.AUCUNE_ASSIMILATION)
