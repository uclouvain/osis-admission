# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from typing import List

from admission.ddd.admission.projet_doctoral.preparation.commands import RechercherDoctoratCommand
from admission.ddd.admission.projet_doctoral.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.projet_doctoral.preparation.dtos import DoctoratDTO
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from infrastructure.shared_kernel.academic_year.repository import academic_year as academic_year_repository


def rechercher_doctorats(
    cmd: 'RechercherDoctoratCommand',
    doctorat_translator: 'IDoctoratTranslator',
) -> List['DoctoratDTO']:
    # TODO :: comment déterminer l'année concernée pour la formation ? Sur base d'un calendrier ?
    annee = (
        GetCurrentAcademicYear()
        .get_starting_academic_year(datetime.date.today(), academic_year_repository.AcademicYearRepository())
        .year
    )
    return doctorat_translator.search(cmd.sigle_secteur_entite_gestion, annee)
