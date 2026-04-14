# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition as PropositionDoctorale,
    PropositionIdentity,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition as PropositionContinue
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition as PropositionGenerale
from admission.ddd.admission.shared_kernel.domain.service.i_modifier_checklist_experience_parcours_anterieur import (
    IValidationExperienceParcoursAnterieurService,
)
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import AdmissionExperienceNonTrouveeException
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience


class ValidationExperienceParcoursAnterieurInMemoryService(IValidationExperienceParcoursAnterieurService):
    @classmethod
    def _recuperer_experience_academique(cls, uuid_experience: str):
        try:
            return next(
                experience
                for experience in ProfilCandidatInMemoryTranslator.experiences_academiques
                if experience.uuid == uuid_experience
            )
        except StopIteration:
            raise AdmissionExperienceNonTrouveeException

    @classmethod
    def _recuperer_experience_non_academique(cls, uuid_experience: str):
        try:
            return next(
                experience
                for experience in ProfilCandidatInMemoryTranslator.experiences_non_academiques
                if experience.uuid == uuid_experience
            )
        except StopIteration:
            raise AdmissionExperienceNonTrouveeException

    @classmethod
    def _recuperer_etudes_secondaires(cls, uuid_experience: str):
        try:
            return next(
                experience
                for experience in ProfilCandidatInMemoryTranslator.etudes_secondaires.values()
                if experience.uuid == uuid_experience
            )
        except StopIteration:
            raise AdmissionExperienceNonTrouveeException

    @classmethod
    def modifier_statut_experience_academique(
        cls,
        uuid_experience: str,
        statut: str,
        profil_candidat_translator: IProfilCandidatTranslator,
        proposition_id: PropositionIdentity = None,
        matricule_candidat: str = None,
        grade_academique_formation_proposition: str = None,
    ):
        super().modifier_statut_experience_academique(
            proposition_id=proposition_id,
            matricule_candidat=matricule_candidat,
            uuid_experience=uuid_experience,
            statut=statut,
            profil_candidat_translator=profil_candidat_translator,
            grade_academique_formation_proposition=grade_academique_formation_proposition,
        )
        experience = cls._recuperer_experience_academique(uuid_experience=uuid_experience)
        experience.statut_validation = statut

    @classmethod
    def modifier_authentification_experience_academique(
        cls,
        uuid_experience: str,
        etat_authentification: str,
    ):
        experience = cls._recuperer_experience_academique(uuid_experience=uuid_experience)
        experience.statut_authentification = etat_authentification

    @classmethod
    def modifier_authentification_experience_non_academique(cls, uuid_experience: str, etat_authentification: str):
        experience = cls._recuperer_experience_non_academique(uuid_experience=uuid_experience)
        experience.statut_authentification = etat_authentification

    @classmethod
    def modifier_authentification_etudes_secondaires(cls, uuid_experience: str, etat_authentification: str):
        pass

    @classmethod
    def modifier_authentification_examen(cls, uuid_experience: str, etat_authentification: str):
        pass

    @classmethod
    def passer_experiences_en_brouillon_en_a_traiter(
        cls,
        proposition: PropositionContinue | PropositionDoctorale | PropositionGenerale,
    ):
        for experience in itertools.chain(
            ProfilCandidatInMemoryTranslator.experiences_academiques,
            ProfilCandidatInMemoryTranslator.experiences_non_academiques,
        ):
            if (
                experience.personne == proposition.matricule_candidat
                and experience.statut_validation == ChoixStatutValidationExperience.EN_BROUILLON.name
            ):
                experience.statut_validation = ChoixStatutValidationExperience.A_TRAITER.name

        etudes_secondaires = ProfilCandidatInMemoryTranslator.etudes_secondaires.get(proposition.matricule_candidat)

        if etudes_secondaires.statut_validation == ChoixStatutValidationExperience.EN_BROUILLON.name:
            etudes_secondaires.statut_validation = ChoixStatutValidationExperience.A_TRAITER.name
