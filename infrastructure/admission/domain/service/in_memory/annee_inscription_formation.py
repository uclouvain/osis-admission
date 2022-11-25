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
from datetime import timedelta, date
from typing import Optional

from admission.ddd.admission.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
    CalendrierAcademique,
    Date,
)
from base.models.enums.academic_calendar_type import AcademicCalendarTypes


class AnneeInscriptionFormationInMemoryTranslator(IAnneeInscriptionFormationTranslator):
    @classmethod
    def _generer_calendriers_academiques(cls, date_jour: datetime.date, date_bascule: Date):
        return [
            CalendrierAcademique(
                date_debut=datetime.date(annee + date_bascule.annee, date_bascule.mois, date_bascule.jour),
                date_fin=datetime.date(annee + 1 + date_bascule.annee, date_bascule.mois, date_bascule.jour)
                - timedelta(days=1),
                annee=annee,
            )
            for annee in range(date_jour.year - 1, date_jour.year + 2)
        ]

    @classmethod
    def recuperer(cls, type_calendrier_academique: AcademicCalendarTypes) -> Optional[int]:
        date_jour = date.today()
        calendriers = []
        if type_calendrier_academique == AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT:
            calendriers = cls._generer_calendriers_academiques(
                date_jour=date_jour,
                date_bascule=cls.DATE_BASCULE_FORMATION_GENERALE,
            )
        elif type_calendrier_academique == AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT:
            calendriers = cls._generer_calendriers_academiques(
                date_jour=date_jour,
                date_bascule=cls.DATE_BASCULE_DOCTORAT,
            )
        elif type_calendrier_academique == AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT:
            calendriers = cls._generer_calendriers_academiques(
                date_jour=date_jour,
                date_bascule=cls.DATE_BASCULE_FORMATION_CONTINUE,
            )

        return next(
            (
                calendrier.annee
                for calendrier in calendriers
                if calendrier.date_debut <= date_jour <= calendrier.date_fin
            ),
            None,
        )
