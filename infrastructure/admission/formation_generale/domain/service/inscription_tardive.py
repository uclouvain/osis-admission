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
from typing import Optional

from admission.ddd.admission.formation_generale.domain.service.i_inscription_tardive import IInscriptionTardive
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes


class InscriptionTardive(IInscriptionTardive):
    @classmethod
    def _recuperer_date_fin_pot(cls, pot: AcademicCalendarTypes, today: datetime.date) -> Optional[datetime.date]:
        calendar = AcademicCalendar.objects.filter(
            reference=pot.name,
            start_date__lte=today,
            end_date__gte=today,
        ).only('end_date').first()

        return calendar.end_date if calendar else None
