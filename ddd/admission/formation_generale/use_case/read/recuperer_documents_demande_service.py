# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from typing import List

from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.i_recuperer_documents_demande import IRecupererDocumentsDemandeTranslator
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.dtos.document import DocumentDTO
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.ddd.admission.formation_generale.commands import RecupererDocumentsDemandeQuery
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.service.i_comptabilite import IComptabiliteTranslator
from admission.ddd.admission.formation_generale.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository


def recuperer_documents_demande(
    cmd: 'RecupererDocumentsDemandeQuery',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    comptabilite_translator: 'IComptabiliteTranslator',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
    recuperer_documents_demande_translator: 'IRecupererDocumentsDemandeTranslator',
    academic_year_repository: 'IAcademicYearRepository',
) -> 'List[DocumentDTO]':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_demande)
    proposition_dto = proposition_repository.get_dto(entity_id=proposition_id)
    comptabilite_dto = comptabilite_translator.get_comptabilite_dto(proposition_uuid=cmd.uuid_demande)
    annee_courante = (
        GetCurrentAcademicYear()
        .get_starting_academic_year(
            datetime.date.today(),
            academic_year_repository,
        )
        .year
    )
    resume_dto = ResumeProposition.get_resume(
        profil_candidat_translator=profil_candidat_translator,
        annee_courante=annee_courante,
        proposition_dto=proposition_dto,
        comptabilite_dto=comptabilite_dto,
    )
    questions_specifiques_dtos = question_specifique_translator.search_dto_by_proposition(
        proposition_uuid=cmd.uuid_demande,
        type=TypeItemFormulaire.DOCUMENT.name,
    )

    # WHEN
    documents_dto = recuperer_documents_demande_translator.recuperer(
        resume_dto=resume_dto,
        questions_specifiques=questions_specifiques_dtos,
    )

    # THEN
    return documents_dto
