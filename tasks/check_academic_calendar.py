##############################################################################
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
##############################################################################
from admission.calendar.admission_calendar import *
from admission.calendar.admission_digit_ticket_submission import (
    AdmissionDigitTicketSubmissionCalendar,
)
from backoffice.celery import app as celery_app


@celery_app.task
def run() -> dict:  # pragma: no cover
    DoctorateAdmissionCalendar.ensure_consistency_until_n_plus_6()
    GeneralEducationAdmissionCalendar.ensure_consistency_until_n_plus_6()
    ContinuingEducationAdmissionCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolExternalEnrollmentChangeCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolExternalReorientationCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolVipCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolHueUclPathwayChangeCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolInstituteChangeCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolUe5BelgianCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolUe5NonBelgianCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolHue5BelgiumResidencyCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolHue5ForeignResidencyCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolNonResidentQuotaCalendar.ensure_consistency_until_n_plus_6()
    AdmissionAccessConditionsUrl.ensure_consistency_until_n_plus_6()
    AdmissionDigitTicketSubmissionCalendar.ensure_consistency_until_n_plus_6()
    AdmissionMedicineDentistryEnrollmentCalendar.ensure_consistency_until_n_plus_6()
    return {}
