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
from typing import List

from admission.ddd.admission.domain.service.i_annee_inscription_formation import IAnneeInscriptionFormationTranslator
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_generale.commands import RechercherFormationGeneraleQuery
from admission.ddd.admission.formation_generale.domain.service.i_formation import IFormationGeneraleTranslator
from base.models.enums.academic_calendar_type import AcademicCalendarTypes


def rechercher_formations(
    cmd: 'RechercherFormationGeneraleQuery',
    formation_generale_translator: 'IFormationGeneraleTranslator',
    annee_inscription_formation_translator: 'IAnneeInscriptionFormationTranslator',
) -> List['FormationDTO']:
    # GIVEN
    annee_inscription = annee_inscription_formation_translator.recuperer(
        AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT,
    )

    # THEN
    return formation_generale_translator.search(
        type=cmd.type_formation,
        annee=annee_inscription,
        intitule=cmd.intitule_formation,
        campus=cmd.campus,
    )
