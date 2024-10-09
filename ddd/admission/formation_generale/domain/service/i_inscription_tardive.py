# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from abc import abstractmethod
from typing import Optional

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from osis_common.ddd import interface


class IInscriptionTardive(interface.DomainService):
    POTS_INSCRIPTION_TARDIVE = [
        AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE,
        AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN,
    ]
    SEUIL_JOURS_INSCRIPTION_TARDIVE = 31

    @classmethod
    @abstractmethod
    def _recuperer_date_fin_pot(cls, pot: AcademicCalendarTypes, today: datetime.date) -> Optional[datetime.date]:
        raise NotImplementedError

    @classmethod
    def est_inscription_tardive(cls, pot: AcademicCalendarTypes) -> bool:
        if pot not in cls.POTS_INSCRIPTION_TARDIVE:
            return False

        today = datetime.date.today()
        date_fin_pot = cls._recuperer_date_fin_pot(pot, today)

        return date_fin_pot is not None and (date_fin_pot - today).days < cls.SEUIL_JOURS_INSCRIPTION_TARDIVE
