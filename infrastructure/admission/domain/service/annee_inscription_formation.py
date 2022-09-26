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
from typing import Optional

from admission.ddd.admission.domain.enums import TypeFormation

from admission.ddd.admission.domain.service.i_annee_inscription_formation import IAnneeInscriptionFormationTranslator
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType


class AnneeInscriptionFormationTranslator(IAnneeInscriptionFormationTranslator):
    OSIS_ADMISSION_EDUCATION_TYPES_MAPPING = {
        TypeFormation.BACHELIER.name: [
            TrainingType.BACHELOR.name,
        ],
        TypeFormation.MASTER.name: [
            TrainingType.MASTER_MA_120.name,
            TrainingType.MASTER_MD_120.name,
            TrainingType.MASTER_MS_120.name,
            TrainingType.MASTER_MS_180_240.name,
            TrainingType.MASTER_M1.name,
            TrainingType.MASTER_MC.name,
        ],
        TypeFormation.DOCTORAT.name: [
            TrainingType.PHD.name,
        ],
        TypeFormation.AGREGATION_CAPES.name: [
            TrainingType.AGGREGATION.name,
            TrainingType.CAPAES.name,
        ],
        TypeFormation.FORMATION_CONTINUE.name: [
            TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
            TrainingType.CERTIFICATE_OF_SUCCESS.name,
            TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
            TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name,
        ],
        TypeFormation.CERTIFICAT.name: [
            TrainingType.CERTIFICATE.name,
            TrainingType.RESEARCH_CERTIFICATE.name,
        ],
    }

    GENERAL_EDUCATION_TYPES = set(
        OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.BACHELIER.name)
        + OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.MASTER.name)
        + OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.AGREGATION_CAPES.name)
        + OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.CERTIFICAT.name)
    )

    CONTINUING_EDUCATION_TYPES = set(OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.FORMATION_CONTINUE.name))

    DOCTORATE_EDUCATION_TYPES = set(OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.DOCTORAT.name))

    ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE = {
        osis_type: admission_type
        for admission_type, osis_types in OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.items()
        for osis_type in osis_types
    }

    @classmethod
    def recuperer(cls, type_calendrier_academique: AcademicCalendarTypes) -> Optional[int]:
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
