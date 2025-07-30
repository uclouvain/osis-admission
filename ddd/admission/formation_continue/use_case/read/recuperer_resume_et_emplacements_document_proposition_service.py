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

from admission.ddd.admission.shared_kernel.domain.service.i_emplacements_documents_proposition import (
    IEmplacementsDocumentsPropositionTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.shared_kernel.dtos.resume import (
    ResumeEtEmplacementsDocumentsPropositionDTO,
)
from admission.ddd.admission.shared_kernel.enums import TypeItemFormulaire
from admission.ddd.admission.shared_kernel.enums.valorisation_experience import (
    ExperiencesCVRecuperees,
)
from admission.ddd.admission.formation_continue.commands import (
    RecupererResumeEtEmplacementsDocumentsPropositionQuery,
)
from admission.ddd.admission.formation_continue.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_continue.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.formation_continue.repository.i_proposition import (
    IPropositionRepository,
)
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import (
    IAcademicYearRepository,
)
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import (
    IPersonneConnueUclTranslator,
)


def recuperer_resume_et_emplacements_documents_proposition(
    cmd: 'RecupererResumeEtEmplacementsDocumentsPropositionQuery',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    emplacements_documents_demande_translator: 'IEmplacementsDocumentsPropositionTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    personne_connue_translator: 'IPersonneConnueUclTranslator',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
) -> ResumeEtEmplacementsDocumentsPropositionDTO:
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_dto = proposition_repository.get_dto(entity_id=proposition_id)
    questions_specifiques_dtos = question_specifique_translator.search_dto_by_proposition(
        proposition_uuid=cmd.uuid_proposition,
    )
    resume_dto = ResumeProposition.get_resume_pour_gestionnaire(
        profil_candidat_translator=profil_candidat_translator,
        academic_year_repository=academic_year_repository,
        proposition_dto=proposition_dto,
        experiences_cv_recuperees=cmd.experiences_cv_recuperees,
        questions_specifiques_dtos=questions_specifiques_dtos,
    )

    # WHEN
    emplacements_documents = emplacements_documents_demande_translator.recuperer_emplacements_dto(
        personne_connue_translator=personne_connue_translator,
        resume_dto=resume_dto,
        questions_specifiques=questions_specifiques_dtos,
        avec_documents_libres=True,
    )

    # THEN
    return ResumeEtEmplacementsDocumentsPropositionDTO(resume=resume_dto, emplacements_documents=emplacements_documents)
