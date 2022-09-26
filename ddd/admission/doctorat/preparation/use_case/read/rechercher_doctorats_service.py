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

from admission.ddd.admission.doctorat.preparation.commands import RechercherDoctoratQuery
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.doctorat.preparation.dtos import DoctoratDTO
from admission.ddd.admission.domain.service.i_annee_inscription_formation import IAnneeInscriptionFormationTranslator
from base.models.enums.academic_calendar_type import AcademicCalendarTypes


def rechercher_doctorats(
    cmd: 'RechercherDoctoratQuery',
    doctorat_translator: 'IDoctoratTranslator',
    annee_inscription_formation_translator: 'IAnneeInscriptionFormationTranslator',
) -> List['DoctoratDTO']:
    annee = annee_inscription_formation_translator.recuperer(AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT)
    return doctorat_translator.search(cmd.sigle_secteur_entite_gestion, annee, campus=cmd.campus)
