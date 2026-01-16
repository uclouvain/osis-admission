# ##############################################################################
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
# ##############################################################################
import datetime

from admission.ddd.admission.shared_kernel.commands import RechercherParcoursAnterieurQuery
from admission.ddd.admission.shared_kernel.commands import \
    RecupererInformationsValidationExperienceParcoursAnterieurQuery
from admission.ddd.admission.shared_kernel.domain.service.i_modifier_checklist_experience_parcours_anterieur import \
    IValidationExperienceParcoursAnterieurService
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import IProfilCandidatTranslator
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository


def recuperer_informations_validation_experience_parcours_anterieur(
    cmd: 'RecupererInformationsValidationExperienceParcoursAnterieurQuery',
    validation_experience_parcours_anterieur_service: 'IValidationExperienceParcoursAnterieurService',
):
    return validation_experience_parcours_anterieur_service.recuperer_information_validation(
        matricule_candidat=cmd.matricule_candidat,
        uuid_experience=cmd.uuid_experience,
        type_experience=cmd.type_experience,
    )
