# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional

from admission.ddd.admission.doctorat.preparation.dtos import (
    GroupeDeSupervisionDTO,
    PropositionDTO as PropositionDoctoraleDTO,
)
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.dtos.resume import ResumePropositionDTO, AdmissionPropositionDTO, AdmissionComptabiliteDTO
from osis_common.ddd import interface


class ResumeProposition(interface.DomainService):
    @classmethod
    def get_resume(
        cls,
        profil_candidat_translator: IProfilCandidatTranslator,
        annee_courante: int,
        proposition_dto: AdmissionPropositionDTO,
        comptabilite_dto: Optional[AdmissionComptabiliteDTO] = None,
        groupe_supervision_dto: Optional[GroupeDeSupervisionDTO] = None,
    ) -> 'ResumePropositionDTO':

        resume_candidat_dto = profil_candidat_translator.recuperer_toutes_informations_candidat(
            matricule=proposition_dto.matricule_candidat,
            formation=proposition_dto.doctorat.type
            if isinstance(proposition_dto, PropositionDoctoraleDTO)
            else proposition_dto.formation.type,
            annee_courante=annee_courante,
        )

        return ResumePropositionDTO(
            proposition=proposition_dto,
            comptabilite=comptabilite_dto,
            identification=resume_candidat_dto.identification,
            coordonnees=resume_candidat_dto.coordonnees,
            curriculum=resume_candidat_dto.curriculum,
            etudes_secondaires=resume_candidat_dto.etudes_secondaires,
            connaissances_langues=resume_candidat_dto.connaissances_langues,
            groupe_supervision=groupe_supervision_dto,
        )
