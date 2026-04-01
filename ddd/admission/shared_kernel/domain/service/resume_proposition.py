# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity as PropositionDoctoraleIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.groupe_de_supervision_dto import (
    GroupeDeSupervisionDto,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_comptabilite import (
    IComptabiliteTranslator as IComptabiliteDoctoraleTranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.doctorat.preparation.dtos import GroupeDeSupervisionDTO
from admission.ddd.admission.doctorat.preparation.dtos import (
    PropositionDTO as PropositionDoctoraleDTO,
)
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository as IPropositionDoctoraleRepository,
)
from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_translator import (
    IInscriptionsTranslatorService,
)
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_unites_enseignement_translator import (
    IUnitesEnseignementTranslator,
)
from admission.ddd.admission.shared_kernel.dtos.question_specifique import (
    QuestionSpecifiqueDTO,
)
from admission.ddd.admission.shared_kernel.dtos.resume import (
    AdmissionComptabiliteDTO,
    AdmissionPropositionDTO,
    AdmissionPropositionGestionnaireDTO,
    ResumePropositionDTO,
    ResumePropositionGestionnaireDTO,
)
from admission.ddd.admission.shared_kernel.enums.valorisation_experience import (
    ExperiencesCVRecuperees,
)
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import (
    GetCurrentAcademicYear,
)
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import (
    IAcademicYearRepository,
)
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
        pour_candidat: bool = False,
        inscriptions_translator: 'IInscriptionsTranslatorService' = None,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator = None,
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
            formation=proposition_dto.formation,
            annee_courante=annee_courante,
            uuid_proposition=proposition_dto.uuid,
            experiences_cv_recuperees=experiences_cv_recuperees,
        )

        parametres_additionnels = {}

        if pour_candidat:
            if not inscriptions_translator or not annee_inscription_formation_translator:
                raise NotImplementedError

            parametres_additionnels['candidat_est_etudiant_recent_ucl'] = inscriptions_translator.est_inscrit_recemment(
                matricule_candidat=proposition_dto.matricule_candidat,
                annee_inscription_formation_translator=annee_inscription_formation_translator,
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
            examen_formation=resume_candidat_dto.examen_formation,
            pour_candidat=pour_candidat,
            **parametres_additionnels,
        )

    @classmethod
    def get_resume_pour_gestionnaire(
        cls,
        profil_candidat_translator: IProfilCandidatTranslator,
        academic_year_repository: 'IAcademicYearRepository',
        proposition_dto: AdmissionPropositionGestionnaireDTO,
        comptabilite_dto: Optional[AdmissionComptabiliteDTO] = None,
        groupe_supervision_dto: Optional[GroupeDeSupervisionDTO] = None,
        experiences_cv_recuperees: ExperiencesCVRecuperees = ExperiencesCVRecuperees.TOUTES,
        questions_specifiques_dtos: Optional[List[QuestionSpecifiqueDTO]] = None,
    ) -> 'ResumePropositionGestionnaireDTO':
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
            formation=(
                proposition_dto.doctorat
                if isinstance(proposition_dto, PropositionDoctoraleDTO)
                else proposition_dto.formation
            ),
            annee_courante=annee_courante,
            uuid_proposition=proposition_dto.uuid,
            experiences_cv_recuperees=experiences_cv_recuperees,
        )

        examen_dto = profil_candidat_translator.get_examen(
            uuid_proposition=proposition_dto.uuid,
            matricule=proposition_dto.matricule_candidat,
            formation_sigle=(
                proposition_dto.doctorat.sigle
                if isinstance(proposition_dto, PropositionDoctoraleDTO)
                else proposition_dto.formation.sigle
            ),
            formation_annee=(
                proposition_dto.doctorat.annee
                if isinstance(proposition_dto, PropositionDoctoraleDTO)
                else proposition_dto.formation.annee
            ),
        )

        return ResumePropositionGestionnaireDTO(
            proposition=proposition_dto,
            comptabilite=comptabilite_dto,
            identification=resume_candidat_dto.identification,
            coordonnees=resume_candidat_dto.coordonnees,
            curriculum=resume_candidat_dto.curriculum,
            etudes_secondaires=resume_candidat_dto.etudes_secondaires,
            connaissances_langues=resume_candidat_dto.connaissances_langues,
            groupe_supervision=groupe_supervision_dto,
            questions_specifiques_dtos=questions_specifiques_dtos,
            examen_formation=examen_dto,
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
        question_specifique_translator: 'IQuestionSpecifiqueTranslator',
        experiences_cv_recuperees: Optional[ExperiencesCVRecuperees] = None,
        pour_candidat: bool = False,
        inscriptions_translator: 'IInscriptionsTranslatorService' = None,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator = None,
    ) -> 'ResumePropositionDTO':
        proposition_dto = proposition_repository.get_dto(entity_id=PropositionDoctoraleIdentity(uuid=uuid_proposition))
        comptabilite_dto = comptabilite_translator.get_comptabilite_dto(proposition_uuid=uuid_proposition)
        groupe_supervision_dto = GroupeDeSupervisionDto().get(
            uuid_proposition=uuid_proposition,
            repository=groupe_supervision_repository,
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
            pour_candidat=pour_candidat,
            annee_inscription_formation_translator=annee_inscription_formation_translator,
            inscriptions_translator=inscriptions_translator,
        )

    @classmethod
    def get_resume_demande_doctorat_pour_gestionnaire(
        cls,
        uuid_proposition: str,
        proposition_repository: 'IPropositionDoctoraleRepository',
        comptabilite_translator: 'IComptabiliteDoctoraleTranslator',
        profil_candidat_translator: IProfilCandidatTranslator,
        academic_year_repository: 'IAcademicYearRepository',
        groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
        question_specifique_translator: 'IQuestionSpecifiqueTranslator',
        unites_enseignement_translator: 'IUnitesEnseignementTranslator',
        experiences_cv_recuperees: Optional[ExperiencesCVRecuperees] = None,
    ) -> 'ResumePropositionGestionnaireDTO':
        proposition_dto = proposition_repository.get_dto_for_gestionnaire(
            entity_id=PropositionDoctoraleIdentity(uuid=uuid_proposition),
            unites_enseignement_translator=unites_enseignement_translator,
        )
        comptabilite_dto = comptabilite_translator.get_comptabilite_dto(proposition_uuid=uuid_proposition)
        groupe_supervision_dto = GroupeDeSupervisionDto().get(
            uuid_proposition=uuid_proposition,
            repository=groupe_supervision_repository,
        )
        questions_specifiques_dtos = question_specifique_translator.search_dto_by_proposition(
            proposition_uuid=uuid_proposition,
        )
        return cls.get_resume_pour_gestionnaire(
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
