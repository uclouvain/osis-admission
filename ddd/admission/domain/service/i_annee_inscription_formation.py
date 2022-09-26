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
import abc
import datetime
from dataclasses import dataclass
from typing import Optional

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from osis_common.ddd import interface


@dataclass
class Date:
    jour: int
    mois: int
    annee: int


@dataclass()
class CalendrierAcademique:
    date_debut: datetime.date
    date_fin: datetime.date
    annee: int


class IAnneeInscriptionFormationTranslator(interface.DomainService):
    # The years of the following dates corresponding to the difference between the year of the limit enrolment date and
    # the academic year of the targeted course

    # [01/01/N ; 01/07/N[ Année académique (N-1)-(N)
    # [01/07/N ; 31/12/N] Année académique (N)-(N+1)
    DATE_BASCULE_DOCTORAT = Date(jour=1, mois=7, annee=0)

    # [01/01/N ; 01/11/N[ Année académique (N)-(N+1)
    # [01/11/N ; 31/12/N] Année académique (N+1)-(N+2)
    DATE_BASCULE_FORMATION_GENERALE = Date(jour=1, mois=11, annee=-1)

    # [01/01/N ; 01/07/N[ Année académique (N-1)-(N)
    # [01/07/N ; 31/12/N] Année académique (N)-(N+1)
    DATE_BASCULE_FORMATION_CONTINUE = Date(jour=1, mois=7, annee=0)

    @classmethod
    @abc.abstractmethod
    def recuperer(cls, type_calendrier_academique: AcademicCalendarTypes) -> Optional[int]:
        raise NotImplementedError
