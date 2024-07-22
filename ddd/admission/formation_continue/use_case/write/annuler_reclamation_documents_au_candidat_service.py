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

from admission.ddd.admission.domain.builder.emplacement_document_identity_builder import (
    EmplacementDocumentIdentityBuilder,
)
from admission.ddd.admission.domain.service.i_emplacements_documents_proposition import (
    IEmplacementsDocumentsPropositionTranslator,
)
from admission.ddd.admission.domain.service.i_historique import IHistorique
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from admission.ddd.admission.formation_continue.commands import AnnulerReclamationDocumentsAuCandidatCommand
from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_continue.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.formation_continue.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator


def annuler_reclamation_documents_au_candidat(
    cmd: 'AnnulerReclamationDocumentsAuCandidatCommand',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    personne_connue_translator: 'IPersonneConnueUclTranslator',
    emplacements_documents_demande_translator: 'IEmplacementsDocumentsPropositionTranslator',
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
) -> PropositionIdentity:
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))
    proposition_dto = proposition_repository.get_dto(entity_id=proposition.entity_id)
    resume_dto = ResumeProposition.get_resume(
        profil_candidat_translator=profil_candidat_translator,
        academic_year_repository=academic_year_repository,
        proposition_dto=proposition_dto,
        experiences_cv_recuperees=ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION,
    )
    questions_specifiques_dtos = question_specifique_translator.search_dto_by_proposition(
        proposition_uuid=cmd.uuid_proposition,
        type=TypeItemFormulaire.DOCUMENT.name,
    )

    documents_reclames_dtos = emplacements_documents_demande_translator.recuperer_emplacements_reclames_dto(
        personne_connue_translator=personne_connue_translator,
        resume_dto=resume_dto,
        questions_specifiques=questions_specifiques_dtos,
    )

    identifiants_documents_demandes = EmplacementDocumentIdentityBuilder.build_list(
        [document_dto.identifiant for document_dto in documents_reclames_dtos],
        cmd.uuid_proposition,
    )

    documents_reclames = emplacement_document_repository.search(
        entity_ids=identifiants_documents_demandes,
        statut=StatutEmplacementDocument.RECLAME,
    )

    emplacement_document_repository.annuler_reclamation_documents_au_candidat(
        documents_reclames=documents_reclames,
        auteur=cmd.auteur,
    )

    proposition.annuler_reclamation_documents(auteur_modification=cmd.auteur)

    proposition_repository.save(proposition)
    emplacement_document_repository.save_multiple(entities=documents_reclames, auteur=cmd.auteur)

    historique.historiser_annulation_reclamation_documents(
        proposition=proposition,
        acteur=cmd.auteur,
        par_fac=True,
    )

    return proposition.entity_id
