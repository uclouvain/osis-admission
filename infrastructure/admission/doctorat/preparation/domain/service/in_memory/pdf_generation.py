# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional, List

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.doctorat.preparation.domain.service.i_pdf_generation import IPDFGeneration
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.domain.model.titre_acces_selectionnable import TitreAccesSelectionnable
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.i_unites_enseignement_translator import IUnitesEnseignementTranslator
from ddd.logic.shared_kernel.campus.repository.i_uclouvain_campus import IUclouvainCampusRepository
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import IExperienceParcoursInterneTranslator


class PDFGenerationInMemory(IPDFGeneration):
    @classmethod
    def generer_attestation_accord_facultaire(
        cls,
        proposition: Proposition,
        gestionnaire: PersonneConnueUclDTO,
        proposition_repository: IPropositionRepository,
        unites_enseignement_translator: IUnitesEnseignementTranslator,
        profil_candidat_translator: IProfilCandidatTranslator,
        titres_selectionnes: List[TitreAccesSelectionnable],
        annee_courante: int,
        experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
    ) -> None:
        pass

    @classmethod
    def generer_attestation_refus_facultaire(
        cls,
        proposition: Proposition,
        gestionnaire: PersonneConnueUclDTO,
        proposition_repository: IPropositionRepository,
        unites_enseignement_translator: IUnitesEnseignementTranslator,
    ) -> None:
        pass

    @classmethod
    def generer_sic_temporaire(
        cls,
        proposition_repository: IPropositionRepository,
        profil_candidat_translator: IProfilCandidatTranslator,
        campus_repository: IUclouvainCampusRepository,
        proposition: Proposition,
        gestionnaire: str,
        pdf: str,
    ) -> Optional[str]:
        return 'token-pdf'

    @classmethod
    def generer_attestation_accord_sic(
        cls,
        proposition_repository: IPropositionRepository,
        profil_candidat_translator: IProfilCandidatTranslator,
        proposition: Proposition,
        gestionnaire: str,
        temporaire: bool = False,
    ) -> Optional[str]:
        pass

    @classmethod
    def generer_attestation_accord_annexe_sic(
        cls,
        proposition_repository: IPropositionRepository,
        profil_candidat_translator: IProfilCandidatTranslator,
        proposition: Proposition,
        gestionnaire: str,
        temporaire: bool = False,
    ) -> Optional[str]:
        pass

    @classmethod
    def generer_attestation_refus_sic(
        cls,
        proposition_repository: IPropositionRepository,
        profil_candidat_translator: IProfilCandidatTranslator,
        campus_repository: IUclouvainCampusRepository,
        proposition: Proposition,
        gestionnaire: str,
        temporaire: bool = False,
    ) -> Optional[str]:
        pass
