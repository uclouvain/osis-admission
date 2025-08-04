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

from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.ddd.admission.enums.valorisation_experience import (
    ExperiencesCVRecuperees,
)
from admission.ddd.admission.formation_generale.commands import (
    ApprouverInscriptionParSicCommand,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.formation_generale.domain.service.i_historique import (
    IHistorique,
)
from admission.ddd.admission.formation_generale.events import (
    InscriptionApprouveeParSicEvent,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import (
    IPropositionRepository,
)
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import (
    IExperienceParcoursInterneTranslator,
)


def approuver_inscription_par_sic(
    message_bus,
    cmd: ApprouverInscriptionParSicCommand,
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    comptabilite_translator: 'IComptabiliteTranslator',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
    emplacements_documents_demande_translator: 'IEmplacementsDocumentsPropositionTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    personne_connue_translator: 'IPersonneConnueUclTranslator',
    experience_parcours_interne_translator: 'IExperienceParcoursInterneTranslator',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    proposition_dto = proposition_repository.get_dto(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))
    comptabilite_dto = comptabilite_translator.get_comptabilite_dto(proposition_uuid=cmd.uuid_proposition)
    resume_dto = ResumeProposition.get_resume(
        profil_candidat_translator=profil_candidat_translator,
        academic_year_repository=academic_year_repository,
        proposition_dto=proposition_dto,
        comptabilite_dto=comptabilite_dto,
        experiences_cv_recuperees=ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION,
    )
    questions_specifiques_dtos = question_specifique_translator.search_dto_by_proposition(
        proposition_uuid=cmd.uuid_proposition,
        type=TypeItemFormulaire.DOCUMENT.name,
    )
    documents_dto = emplacements_documents_demande_translator.recuperer_emplacements_dto(
        personne_connue_translator=personne_connue_translator,
        resume_dto=resume_dto,
        questions_specifiques=questions_specifiques_dtos,
        avec_documents_libres=False,
    )

    # WHEN
    proposition.approuver_par_sic(
        auteur_modification=cmd.auteur,
        documents_dto=documents_dto,
        curriculum_dto=resume_dto.curriculum,
        profil_candidat_translator=profil_candidat_translator,
        experience_parcours_interne_translator=experience_parcours_interne_translator,
        grade_academique_formation_proposition=proposition_dto.formation.grade_academique,
    )

    # THEN
    proposition_repository.save(entity=proposition)
    historique.historiser_acceptation_sic(
        proposition=proposition,
        gestionnaire=cmd.auteur,
    )

    message_bus.publish(
        InscriptionApprouveeParSicEvent(
            entity_id=proposition.entity_id,
            matricule=proposition.matricule_candidat,
            auteur=cmd.auteur,
            objet_message=cmd.objet_message,
            corps_message=cmd.corps_message,
        )
    )
    return proposition.entity_id
