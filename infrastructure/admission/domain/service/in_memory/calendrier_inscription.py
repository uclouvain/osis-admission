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
from datetime import date, timedelta
from typing import List, Tuple

from admission.ddd.admission.domain.service.i_calendrier_inscription import ICalendrierInscription
from admission.ddd.admission.dtos import IdentificationDTO
from admission.ddd.admission.enums import TypeSituationAssimilation
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from base.tests.factories.academic_year import get_current_year


class CalendrierInscriptionInMemory(ICalendrierInscription):
    periodes_ouvertes = {
        pool.event_reference: (
            pool.cutover_date,
            getattr(pool, 'end_date', None),
        )
        for pool in ICalendrierInscription.pools
    }

    @classmethod
    def get_annees_academiques_pour_calcul(cls) -> List[int]:
        current_year = get_current_year()
        return [current_year, current_year - 1, current_year + 1]

    @classmethod
    def get_pool_ouverts(cls) -> List[Tuple[str, int]]:
        opened = []
        today = date.today()
        for pool_name, dates in cls.periodes_ouvertes.items():
            for annee in cls.get_annees_academiques_pour_calcul():
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
            ProfilCandidatInMemoryTranslator.pays_union_europeenne | cls.PLUS_5_ISO_CODES
        ) or (situation_assimilation and situation_assimilation != TypeSituationAssimilation.AUCUNE_ASSIMILATION)
