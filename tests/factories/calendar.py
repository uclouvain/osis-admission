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
import datetime
from math import ceil, floor

import factory

from admission.calendar.admission_calendar import *
from admission.calendar.admission_digit_ticket_submission import (
    AdmissionDigitTicketSubmissionCalendar,
)
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year


class AdmissionAcademicCalendarFactory(AcademicCalendarFactory):
    @staticmethod
    def produce_all_required(current_year=None, quantity=3):
        """Produce the required academic years (future first) along with the calendars required for admission"""
        current_year = current_year or get_current_year()
        [
            AcademicYearFactory(year=current_year + i)
            for i in range(-floor((quantity - 1) / 2), ceil((quantity + 1) / 2))
        ]
        return [
            calendar.ensure_consistency_until_n_plus_6()
            for calendar in [
                DoctorateAdmissionCalendar,
                ContinuingEducationAdmissionCalendar,
                AdmissionPoolExternalEnrollmentChangeCalendar,
                AdmissionPoolExternalReorientationCalendar,
                AdmissionPoolVipCalendar,
                AdmissionPoolHueUclPathwayChangeCalendar,
                AdmissionPoolInstituteChangeCalendar,
                AdmissionPoolUe5BelgianCalendar,
                AdmissionPoolUe5NonBelgianCalendar,
                AdmissionPoolHue5BelgiumResidencyCalendar,
                AdmissionPoolHue5ForeignResidencyCalendar,
                AdmissionPoolNonResidentQuotaCalendar,
                AdmissionAccessConditionsUrl,
                GeneralEducationAdmissionCalendar,
                AdmissionDigitTicketSubmissionCalendar,
            ]
        ]


class AdmissionMedDentEnrollmentAcademicCalendarFactory(AcademicCalendarFactory):
    reference = AcademicCalendarTypes.ADMISSION_MEDICINE_DENTISTRY_BACHELOR_ENROLLMENT.name
    start_date = factory.LazyAttribute(lambda obj: datetime.date(obj.data_year.year, 9, 6))
    end_date = factory.LazyAttribute(lambda obj: datetime.date(obj.data_year.year + 1, 2, 15))
