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

from admission.ddd.admission.doctorat.preparation.commands import (
    CompleterEmplacementsDocumentsParCandidatCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_comptabilite import (
    IComptabiliteTranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_membre_CA import (
    IMembreCATranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import (
    INotification,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import (
    IPromoteurTranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.domain.builder.emplacement_document_identity_builder import (
    EmplacementDocumentIdentityBuilder,
)
from admission.ddd.admission.domain.service.i_emplacements_documents_proposition import (
    IEmplacementsDocumentsPropositionTranslator,
)
from admission.ddd.admission.domain.service.i_historique import IHistorique
from admission.ddd.admission.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.domain.validator.validator_by_business_action import (
    DocumentsDemandesCompletesValidatorList,
)
from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument
from admission.ddd.admission.repository.i_emplacement_document import (
    IEmplacementDocumentRepository,
)
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import (
    IAcademicYearRepository,
)
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import (
    IPersonneConnueUclTranslator,
)


def completer_emplacements_documents_par_candidat(
    cmd: 'CompleterEmplacementsDocumentsParCandidatCommand',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    comptabilite_translator: 'IComptabiliteTranslator',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
    emplacements_documents_demande_translator: 'IEmplacementsDocumentsPropositionTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    personne_connue_translator: 'IPersonneConnueUclTranslator',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    notification: 'INotification',
    historique: 'IHistorique',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))
    resume_dto = ResumeProposition.get_resume_demande_doctorat(
        uuid_proposition=cmd.uuid_proposition,
        proposition_repository=proposition_repository,
        comptabilite_translator=comptabilite_translator,
        profil_candidat_translator=profil_candidat_translator,
        academic_year_repository=academic_year_repository,
        groupe_supervision_repository=groupe_supervision_repository,
        question_specifique_translator=question_specifique_translator,
    )

    documents_reclames_dtos = emplacements_documents_demande_translator.recuperer_emplacements_reclames_dto(
        personne_connue_translator=personne_connue_translator,
        resume_dto=resume_dto,
        questions_specifiques=resume_dto.questions_specifiques_dtos,
    )

    identifiants_documents_demandes = EmplacementDocumentIdentityBuilder.build_list(
        [document_dto.identifiant for document_dto in documents_reclames_dtos],
        cmd.uuid_proposition,
    )

    documents_reclames = emplacement_document_repository.search(
        entity_ids=identifiants_documents_demandes,
        statut=StatutEmplacementDocument.RECLAME,
    )

    # WHEN
    DocumentsDemandesCompletesValidatorList(
        documents_reclames=documents_reclames,
        reponses_documents_a_completer=cmd.reponses_documents_a_completer,
    ).validate()

    # THEN
    emplacement_document_repository.completer_documents_par_candidat(
        documents_completes=documents_reclames,
        reponses_documents_a_completer=cmd.reponses_documents_a_completer,
        auteur=proposition.matricule_candidat,
    )

    proposition.completer_documents_par_candidat()

    proposition_repository.save(proposition)
    emplacement_document_repository.save_multiple(entities=documents_reclames, auteur=proposition.matricule_candidat)

    message = notification.confirmer_reception_documents_envoyes_par_candidat(
        proposition=resume_dto.proposition,
        liste_documents_reclames=documents_reclames,
        liste_documents_dto=documents_reclames_dtos,
    )

    historique.historiser_completion_documents_par_candidat(proposition=proposition)

    return proposition.entity_id
