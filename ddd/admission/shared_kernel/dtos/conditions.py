# ##############################################################################
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
# ##############################################################################
import attr

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from osis_common.ddd import interface


@attr.dataclass
class AdmissionConditionsDTO(interface.DTO):
    diplomation_secondaire_belge: bool
    diplomation_secondaire_etranger: bool
    alternative_etudes_secondaires: bool
    potentiel_bachelier_belge_sans_diplomation: bool
    diplomation_academique_belge: bool
    diplomation_academique_etranger: bool
    potentiel_master_belge_sans_diplomation: bool
    diplomation_potentiel_master_belge: bool
    diplomation_potentiel_master_etranger: bool
    diplomation_potentiel_doctorat_belge: bool
    potentiel_acces_vae: bool


@attr.dataclass
class InfosDetermineesDTO(interface.DTO):
    annee: int
    pool: 'AcademicCalendarTypes'
