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
import datetime

from admission.ddd.admission.domain.service.reinitialiser_emplacements_documents_non_libres_proposition import (
    ReinitialiserEmplacementsDocumentsNonLibresPropositionService,
)
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.ddd.admission.formation_continue.commands import (
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_continue.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.formation_continue.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository


def recalculer_emplacements_documents_non_libres_proposition(
    cmd: 'RecalculerEmplacementsDocumentsNonLibresPropositionCommand',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_dto = proposition_repository.get_dto(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))
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
        experiences_cv_recuperees=ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION,
    )
    questions_specifiques_dtos = question_specifique_translator.search_dto_by_proposition(
        proposition_uuid=cmd.uuid_proposition,
        type=TypeItemFormulaire.DOCUMENT.name,
    )

    # WHEN
    ReinitialiserEmplacementsDocumentsNonLibresPropositionService.reinitialiser_emplacements(
        resume_dto=resume_dto,
        questions_specifiques=questions_specifiques_dtos,
        emplacement_document_repository=emplacement_document_repository,
    )

    # THEN
    return PropositionIdentity(uuid=cmd.uuid_proposition)
