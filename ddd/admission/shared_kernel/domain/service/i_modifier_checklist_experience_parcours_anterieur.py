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

from admission.ddd.admission.shared_kernel.dtos.validation_experience_parcours_anterieur import \
    ValidationExperienceParcoursAnterieurDTO
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


class IValidationExperienceParcoursAnterieurService(interface.DomainService):
    @classmethod
    @abstractmethod
    def modifier_statut(
        cls,
        matricule_candidat: str,
        uuid_experience: str,
        type_experience: str,
        statut: str,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def modifier_authentification(
        cls,
        matricule_candidat: str,
        uuid_experience: str,
        type_experience: str,
        etat_authentification: str,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def recuperer_information_validation(
        cls,
        matricule_candidat: str,
        uuid_experience: str,
        type_experience: str,
    ) -> ValidationExperienceParcoursAnterieurDTO:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def passer_experiences_en_brouillon_en_a_traiter(
        cls,
        proposition: PropositionContinue | PropositionDoctorale | PropositionGenerale,
    ):
        raise NotImplementedError
