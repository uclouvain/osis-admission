##############################################################################
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
##############################################################################
import datetime

from admission.ddd.admission.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
    Date,
)
from base.business.academic_calendar import AcademicEventSessionCalendarHelper
from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import AcademicYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes


def ensure_consistency_until_n_plus_6(event_reference: str, cutover_date: Date, title: str):
    current_academic_year = AcademicYear.objects.current()
    academic_years = AcademicYear.objects.min_max_years(current_academic_year.year - 1, current_academic_year.year + 6)

    for ac_year in academic_years:
        AcademicCalendar.objects.get_or_create(
            reference=event_reference,
            data_year=ac_year,
            defaults={
                'start_date': datetime.date(ac_year.year + cutover_date.annee, cutover_date.mois, cutover_date.jour),
                'end_date': datetime.date(ac_year.year + 1 + cutover_date.annee, cutover_date.mois, cutover_date.jour)
                - datetime.timedelta(days=1),
                'title': title,
            },
        )


class DoctorateAdmissionCalendar(AcademicEventSessionCalendarHelper):
    event_reference = AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT.name

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=IAnneeInscriptionFormationTranslator.DATE_BASCULE_DOCTORAT,
            title='Admission - Doctorat',
        )


class GeneralEducationAdmissionCalendar(AcademicEventSessionCalendarHelper):
    event_reference = AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=IAnneeInscriptionFormationTranslator.DATE_BASCULE_FORMATION_GENERALE,
            title='Admission - Formation générale',
        )


class ContinuingEducationAdmissionCalendar(AcademicEventSessionCalendarHelper):
    event_reference = AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=IAnneeInscriptionFormationTranslator.DATE_BASCULE_FORMATION_CONTINUE,
            title='Admission - Formation continue',
        )
