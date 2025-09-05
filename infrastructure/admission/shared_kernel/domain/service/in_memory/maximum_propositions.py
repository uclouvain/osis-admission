##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from typing import Optional

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    STATUTS_PROPOSITION_AVANT_SOUMISSION,
    STATUTS_PROPOSITION_DOCTORALE_TERMINEE,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.shared_kernel.domain.service.i_maximum_propositions import (
    IMaximumPropositionsAutorisees,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository as PropositionDoctoraleInMemoryRepository,
)
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository as PropositionContinueInMemoryRepository,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository as PropositionGeneraleInMemoryRepository,
)


class MaximumPropositionsAutoriseesInMemory(IMaximumPropositionsAutorisees):
    @classmethod
    def nb_propositions_envoyees_formation_generale(cls, matricule: str, annee_cible: int) -> int:
        propositions_candidat = PropositionGeneraleInMemoryRepository.search(matricule_candidat=matricule)
        return sum(
            proposition.statut.name == ChoixStatutPropositionGenerale.CONFIRMEE.name
            for proposition in propositions_candidat
        )

    @classmethod
    def nb_propositions_envoyees_formation_continue(cls, matricule: str) -> int:
        propositions_candidat = PropositionContinueInMemoryRepository.search(matricule_candidat=matricule)
        return sum(
            proposition.statut.name == ChoixStatutPropositionContinue.CONFIRMEE.name
            for proposition in propositions_candidat
        )

    @classmethod
    def nb_propositions_en_cours(cls, matricule: str) -> int:
        propositions_generales_candidat = PropositionGeneraleInMemoryRepository.search(matricule_candidat=matricule)
        propositions_continues_candidat = PropositionContinueInMemoryRepository.search(matricule_candidat=matricule)
        propositions_doctorales_candidat = PropositionDoctoraleInMemoryRepository.search(matricule_candidat=matricule)

        return (
            sum(
                proposition.statut.name == ChoixStatutPropositionGenerale.EN_BROUILLON.name
                for proposition in propositions_generales_candidat
            )
            + sum(
                proposition.statut.name == ChoixStatutPropositionContinue.EN_BROUILLON.name
                for proposition in propositions_continues_candidat
            )
            + sum(
                proposition.statut.name in STATUTS_PROPOSITION_AVANT_SOUMISSION
                for proposition in propositions_doctorales_candidat
            )
        )

    @classmethod
    def nb_propositions_en_cours_formation_doctorale(
        cls,
        matricule: str,
        proposition_identity: Optional[PropositionIdentity] = None,
    ) -> int:
        propositions_candidat = PropositionDoctoraleInMemoryRepository.search(matricule_candidat=matricule)
        return sum(
            proposition.statut.name not in STATUTS_PROPOSITION_DOCTORALE_TERMINEE
            and proposition.entity_id != proposition_identity
            for proposition in propositions_candidat
        )
