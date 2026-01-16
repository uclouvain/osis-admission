# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from abc import abstractmethod

from admission.ddd.admission.shared_kernel.domain.service.i_modifier_checklist_experience_parcours_anterieur import \
    IModifierChecklistExperienceParcoursAnterieur
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import ExperienceNonTrouveeException
from ddd.logic.shared_kernel.profil.domain.enums import TypeExperience
from osis_common.ddd import interface
from osis_profile.models import ProfessionalExperience, EducationalExperience
from osis_profile.models.education import SecondaryStudies


class ModifierChecklistExperienceParcoursAnterieur(IModifierChecklistExperienceParcoursAnterieur):
    @classmethod
    def _get_experience_qs(
            cls,
            matricule_candidat: str,
            uuid_experience: str,
            type_experience: str,
    ):
        if type_experience == TypeExperience.ACTIVITE_NON_ACADEMIQUE.name:
            return ProfessionalExperience.objects.filter(
                uuid=uuid_experience,
                person__global_id=matricule_candidat,
            )
        elif type_experience == TypeExperience.ETUDES_SECONDAIRES.name:
            return SecondaryStudies.objects.filter(
                # uuid=uuid_experience,
                person__global_id=matricule_candidat,
            )
        elif type_experience == TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name:
            return EducationalExperience.objects.filter(
                uuid=uuid_experience,
                person__global_id=matricule_candidat,
            )
        raise NotImplementedError

    @classmethod
    def modifier_statut(
        cls,
        matricule_candidat: str,
        uuid_experience: str,
        type_experience: str,
        statut: str,
        statut_authentification: str,
    ):
        updates_number = cls._get_experience_qs(
            matricule_candidat=matricule_candidat, uuid_experience=uuid_experience, type_experience=type_experience,).update(
            validation_status=statut,
            authentication_status=statut_authentification,
        )

        if not updates_number:
            raise ExperienceNonTrouveeException

    @classmethod
    def modifier_authentification(
        cls,
        matricule_candidat: str,
        uuid_experience: str,
        type_experience: str,
        statut_authentification: str,
    ):
        updates_number = cls._get_experience_qs(matricule_candidat=matricule_candidat, uuid_experience=uuid_experience, type_experience=type_experience,).update(authentication_status=statut_authentification)

        if not updates_number:
            raise ExperienceNonTrouveeException
