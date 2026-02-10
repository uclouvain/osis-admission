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
import itertools
from abc import abstractmethod

import attr

from admission.ddd.admission.shared_kernel.domain.service.i_modifier_checklist_experience_parcours_anterieur import \
    IValidationExperienceParcoursAnterieurService
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import ExperienceNonTrouveeException
from admission.ddd.admission.shared_kernel.dtos.validation_experience_parcours_anterieur import \
    ValidationExperienceParcoursAnterieurDTO
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.profil_candidat import \
    ProfilCandidatInMemoryTranslator
from ddd.logic.shared_kernel.profil.domain.enums import TypeExperience
from osis_common.ddd import interface
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition as PropositionDoctorale,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import (
    Proposition as PropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition as PropositionGenerale,
)
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience


class ValidationExperienceParcoursAnterieurInMemoryService(IValidationExperienceParcoursAnterieurService):
    @classmethod
    def _recuperer_experience(cls, uuid_experience: str, type_experience: str):
        experiences = {
            TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name: ProfilCandidatInMemoryTranslator.experiences_academiques,
            TypeExperience.ACTIVITE_NON_ACADEMIQUE.name: ProfilCandidatInMemoryTranslator.experiences_non_academiques,
            TypeExperience.ETUDES_SECONDAIRES.name: ProfilCandidatInMemoryTranslator.etudes_secondaires.values(),
        }.get(type_experience, [])

        try:
            return next(experience for experience in experiences if experience.uuid == uuid_experience)
        except StopIteration:
            raise ExperienceNonTrouveeException

    @classmethod
    def modifier_statut(
        cls,
        matricule_candidat: str,
        uuid_experience: str,
        type_experience: str,
        statut: str,
    ):
        experience = cls._recuperer_experience(uuid_experience=uuid_experience, type_experience=type_experience)
        experience.statut_validation = statut

    @classmethod
    def modifier_authentification(
        cls,
        matricule_candidat: str,
        uuid_experience: str,
        type_experience: str,
        etat_authentification: str,
    ):
        experience = cls._recuperer_experience(uuid_experience=uuid_experience, type_experience=type_experience)
        experience.statut_authentification = etat_authentification

    @classmethod
    def recuperer_information_validation(
        cls,
        matricule_candidat: str,
        uuid_experience: str,
        type_experience: str,
    ) -> ValidationExperienceParcoursAnterieurDTO:
        experience = cls._recuperer_experience(uuid_experience=uuid_experience, type_experience=type_experience)

        return ValidationExperienceParcoursAnterieurDTO(
            uuid=uuid_experience,
            type_experience=type_experience,
            statut_validation=experience.statut_validation,
            statut_authentification=experience.statut_authentification,
        )

    @classmethod
    def passer_experiences_en_brouillon_en_a_traiter(
        cls,
        proposition: PropositionContinue | PropositionDoctorale | PropositionGenerale,
    ):
        for experience in itertools.chain(
            ProfilCandidatInMemoryTranslator.experiences_academiques,
            ProfilCandidatInMemoryTranslator.experiences_non_academiques,
        ):
            if experience.personne == proposition.matricule_candidat and experience.statut_validation == ChoixStatutValidationExperience.EN_BROUILLON.name:
                experience.statut_validation = ChoixStatutValidationExperience.A_TRAITER.name

        etudes_secondaires = ProfilCandidatInMemoryTranslator.etudes_secondaires.get(proposition.matricule_candidat)

        if etudes_secondaires.statut_validation == ChoixStatutValidationExperience.EN_BROUILLON.name:
            etudes_secondaires.statut_validation = ChoixStatutValidationExperience.A_TRAITER.name
