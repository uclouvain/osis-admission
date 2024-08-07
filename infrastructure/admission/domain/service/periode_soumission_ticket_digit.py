##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from typing import List

from admission.calendar.admission_digit_ticket_submission import AdmissionDigitTicketSubmissionCalendar
from admission.ddd.admission.domain.model.periode_soumission_ticket_digit import PeriodeSoumissionTicketDigit
from admission.ddd.admission.domain.service.i_periode_soumission_ticket_digit import \
    IPeriodeSoumissionTicketDigitTranslator


class PeriodeSoumissionTicketDigitTranslator(IPeriodeSoumissionTicketDigitTranslator):

    @classmethod
    def get_periodes_actives(cls) -> List['PeriodeSoumissionTicketDigit']:
        calendar = AdmissionDigitTicketSubmissionCalendar()
        events = calendar.get_opened_academic_events()

        return [
            PeriodeSoumissionTicketDigit(
                annee=event.authorized_target_year,
                date_debut=event.start_date,
                date_fin=event.end_date,
            ) for event in events
        ]
