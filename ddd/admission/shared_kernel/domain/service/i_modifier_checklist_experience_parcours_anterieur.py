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
from abc import abstractmethod

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition as PropositionDoctorale
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition as PropositionContinue
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition as PropositionGenerale
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.shared_kernel.domain.service.profil_candidat import ProfilCandidat
from ddd.logic.shared_kernel.profil.dtos.validation_experience import ValidationExperienceParcoursAnterieurDTO
from osis_common.ddd import interface
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience


class IValidationExperienceParcoursAnterieurService(interface.DomainService):
    @classmethod
    @abstractmethod
    def recuperer_information_validation_experience_academique(
        cls,
        uuid_experience: str,
    ) -> ValidationExperienceParcoursAnterieurDTO:
        raise NotImplementedError

    @classmethod
    def modifier_statut_experience_academique(
        cls,
        proposition_id,
        matricule_candidat: str,
        uuid_experience: str,
        statut: str,
        profil_candidat_translator: IProfilCandidatTranslator,
        grade_academique_formation_proposition: str,
    ):
        if statut == ChoixStatutValidationExperience.VALIDEE.name:
            # Une expérience académique ne peut passer à l'état "Validé" que si elle est complète
            ProfilCandidat.verifier_experience_academique_curriculum_apres_soumission(
                proposition_id=proposition_id,
                matricule_candidat=matricule_candidat,
                uuid_experience=uuid_experience,
                profil_candidat_translator=profil_candidat_translator,
                grade_academique_formation_proposition=grade_academique_formation_proposition,
            )

    @classmethod
    @abstractmethod
    def modifier_authentification_experience_academique(
        cls,
        uuid_experience: str,
        etat_authentification: str,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def recuperer_information_validation_experience_non_academique(
        cls,
        uuid_experience: str,
    ) -> ValidationExperienceParcoursAnterieurDTO:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def modifier_statut_experience_non_academique(
        cls,
        uuid_experience: str,
        statut: str,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def modifier_authentification_experience_non_academique(
        cls,
        uuid_experience: str,
        etat_authentification: str,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def recuperer_information_validation_etudes_secondaires(
        cls,
        uuid_experience: str,
    ) -> ValidationExperienceParcoursAnterieurDTO:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def modifier_statut_etudes_secondaires(
        cls,
        uuid_experience: str,
        statut: str,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def modifier_authentification_etudes_secondaires(
        cls,
        uuid_experience: str,
        etat_authentification: str,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def recuperer_information_validation_examen(
        cls,
        uuid_experience: str,
    ) -> ValidationExperienceParcoursAnterieurDTO:
        raise NotImplementedError

    @classmethod
    def modifier_statut_examen(
        cls,
        proposition_id,
        sigle_formation: str,
        annee_formation: int,
        matricule_candidat: str,
        uuid_experience: str,
        statut: str,
        profil_candidat_translator: IProfilCandidatTranslator,
    ):
        if statut == ChoixStatutValidationExperience.VALIDEE.name:
            # Un examen ne peut passer à l'état "Validé" que s'il est complet
            ProfilCandidat.verifier_examens(
                uuid_proposition=proposition_id.uuid,
                matricule=matricule_candidat,
                sigle_formation=sigle_formation,
                annee_formation=annee_formation,
                profil_candidat_translator=profil_candidat_translator,
            )

    @classmethod
    @abstractmethod
    def modifier_authentification_examen(
        cls,
        uuid_experience: str,
        etat_authentification: str,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def passer_experiences_en_brouillon_en_a_traiter(
        cls,
        proposition: PropositionContinue | PropositionDoctorale | PropositionGenerale,
    ):
        raise NotImplementedError
