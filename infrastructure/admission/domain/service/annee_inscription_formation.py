##############################################################################
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
##############################################################################
import datetime
from typing import Optional

from admission.ddd.admission.domain.enums import TypeFormation

from admission.ddd.admission.domain.service.i_annee_inscription_formation import IAnneeInscriptionFormationTranslator
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType


ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT = {
    'general-education': {
        TypeFormation.BACHELIER.name,
        TypeFormation.MASTER.name,
        TypeFormation.AGREGATION_CAPES.name,
        TypeFormation.CERTIFICAT.name,
    },
    'continuing-education': {TypeFormation.FORMATION_CONTINUE.name},
    'doctorate': {TypeFormation.DOCTORAT.name},
}


class AnneeInscriptionFormationTranslator(IAnneeInscriptionFormationTranslator):
    OSIS_ADMISSION_EDUCATION_TYPES_MAPPING = {
        TypeFormation.BACHELIER.name: [
            TrainingType.BACHELOR.name,
        ],
        TypeFormation.MASTER.name: [
            TrainingType.MASTER_MC.name,
            TrainingType.MASTER_MA_120.name,
            TrainingType.MASTER_MD_120.name,
            TrainingType.MASTER_MS_120.name,
            TrainingType.MASTER_MS_180_240.name,
            TrainingType.MASTER_M1.name,
            TrainingType.MASTER_M4.name,
            TrainingType.MASTER_M5.name,
        ],
        TypeFormation.AGREGATION_CAPES.name: [
            TrainingType.AGGREGATION.name,
            TrainingType.CAPAES.name,
        ],
        TypeFormation.CERTIFICAT.name: [
            # TrainingType.RESEARCH_CERTIFICATE.name,
            TrainingType.CERTIFICATE.name,
        ],
        TypeFormation.FORMATION_CONTINUE.name: [
            TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
            TrainingType.CERTIFICATE_OF_SUCCESS.name,
            TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
            TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name,
        ],
        TypeFormation.DOCTORAT.name: [
            TrainingType.PHD.name,
        ],
    }

    ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE = {
        osis_type: admission_type
        for admission_type, osis_types in OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.items()
        for osis_type in osis_types
    }

    ADMISSION_CALENDAR_TYPE_BY_ADMISSION_EDUCATION_TYPE = {
        TypeFormation.BACHELIER.name: AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT,
        TypeFormation.MASTER.name: AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT,
        TypeFormation.AGREGATION_CAPES.name: AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT,
        TypeFormation.CERTIFICAT.name: AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT,
        TypeFormation.FORMATION_CONTINUE.name: AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT,
        TypeFormation.DOCTORAT.name: AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT,
    }

    GENERAL_EDUCATION_TYPES = set(
        osis_type
        for osis_type, admission_type in ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.items()
        if admission_type in ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT['general-education']
    )

    CONTINUING_EDUCATION_TYPES = set(
        osis_type
        for osis_type, admission_type in ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.items()
        if admission_type in ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT['continuing-education']
    )

    DOCTORATE_EDUCATION_TYPES = set(
        osis_type
        for osis_type, admission_type in ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.items()
        if admission_type in ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT['doctorate']
    )

    @classmethod
    def recuperer(cls, type_calendrier_academique: AcademicCalendarTypes, annee: Optional[int] = None) -> Optional[int]:
        if annee is not None:
            return annee
        date_jour = datetime.date.today()

        academic_calendar_year = (
            AcademicCalendar.objects.filter(
                start_date__lte=date_jour,
                end_date__gte=date_jour,
                reference=type_calendrier_academique.name,
            )
            .values('data_year__year')
            .first()
        )

        if academic_calendar_year:
            return academic_calendar_year.get('data_year__year')

    @classmethod
    def recuperer_annee_selon_type_formation(cls, type_formation: TrainingType) -> Optional[int]:
        return cls.recuperer(
            cls.ADMISSION_CALENDAR_TYPE_BY_ADMISSION_EDUCATION_TYPE[
                cls.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE[type_formation.name]
            ]
        )


ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE = {
    osis_type: context
    for context, admission_types in ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT.items()
    for admission_type in admission_types
    for osis_type in AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING[admission_type]
}
