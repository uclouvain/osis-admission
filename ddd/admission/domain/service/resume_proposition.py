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
from typing import Optional, List

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity as PropositionDoctoraleIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.groupe_de_supervision_dto import GroupeDeSupervisionDto
from admission.ddd.admission.doctorat.preparation.domain.service.i_comptabilite import (
    IComptabiliteTranslator as IComptabiliteDoctoraleTranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_membre_CA import IMembreCATranslator
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.admission.doctorat.preparation.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.doctorat.preparation.dtos import (
    GroupeDeSupervisionDTO,
    PropositionDTO as PropositionDoctoraleDTO,
)
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository as IPropositionDoctoraleRepository,
)
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO, AdmissionPropositionDTO, AdmissionComptabiliteDTO
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository
from osis_common.ddd import interface


class ResumeProposition(interface.DomainService):
    @classmethod
    def get_resume(
        cls,
        profil_candidat_translator: IProfilCandidatTranslator,
        academic_year_repository: 'IAcademicYearRepository',
        proposition_dto: AdmissionPropositionDTO,
        comptabilite_dto: Optional[AdmissionComptabiliteDTO] = None,
        groupe_supervision_dto: Optional[GroupeDeSupervisionDTO] = None,
        experiences_cv_recuperees: ExperiencesCVRecuperees = ExperiencesCVRecuperees.TOUTES,
        questions_specifiques_dtos: Optional[List[QuestionSpecifiqueDTO]] = None,
    ) -> 'ResumePropositionDTO':
        annee_courante = (
            GetCurrentAcademicYear()
            .get_starting_academic_year(
                datetime.date.today(),
                academic_year_repository,
            )
            .year
        )

        resume_candidat_dto = profil_candidat_translator.recuperer_toutes_informations_candidat(
            matricule=proposition_dto.matricule_candidat,
            formation=proposition_dto.doctorat.type
            if isinstance(proposition_dto, PropositionDoctoraleDTO)
            else proposition_dto.formation.type,
            annee_courante=annee_courante,
            uuid_proposition=proposition_dto.uuid,
            experiences_cv_recuperees=experiences_cv_recuperees,
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
            questions_specifiques_dtos=questions_specifiques_dtos,
        )

    @classmethod
    def get_resume_demande_doctorat(
        cls,
        uuid_proposition: str,
        proposition_repository: 'IPropositionDoctoraleRepository',
        comptabilite_translator: 'IComptabiliteDoctoraleTranslator',
        profil_candidat_translator: IProfilCandidatTranslator,
        academic_year_repository: 'IAcademicYearRepository',
        groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
        promoteur_translator: 'IPromoteurTranslator',
        membre_ca_translator: 'IMembreCATranslator',
        question_specifique_translator: 'IQuestionSpecifiqueTranslator',
        experiences_cv_recuperees: Optional[ExperiencesCVRecuperees] = None,
    ) -> 'ResumePropositionDTO':
        proposition_dto = proposition_repository.get_dto(entity_id=PropositionDoctoraleIdentity(uuid=uuid_proposition))
        comptabilite_dto = comptabilite_translator.get_comptabilite_dto(proposition_uuid=uuid_proposition)
        groupe_supervision_dto = GroupeDeSupervisionDto().get(
            uuid_proposition=uuid_proposition,
            repository=groupe_supervision_repository,
            promoteur_translator=promoteur_translator,
            membre_ca_translator=membre_ca_translator,
        )
        questions_specifiques_dtos = question_specifique_translator.search_dto_by_proposition(
            proposition_uuid=uuid_proposition,
        )
        return cls.get_resume(
            profil_candidat_translator=profil_candidat_translator,
            proposition_dto=proposition_dto,
            comptabilite_dto=comptabilite_dto,
            groupe_supervision_dto=groupe_supervision_dto,
            academic_year_repository=academic_year_repository,
            experiences_cv_recuperees=experiences_cv_recuperees
            or (
                ExperiencesCVRecuperees.TOUTES
                if proposition_dto.est_non_soumise
                else ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION
            ),
            questions_specifiques_dtos=questions_specifiques_dtos,
        )
