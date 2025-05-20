##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################

from admission.ddd.admission.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums.valorisation_experience import (
    ExperiencesCVRecuperees,
)
from admission.ddd.admission.formation_generale.commands import (
    RecupererResumePropositionQuery,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.service.i_comptabilite import (
    IComptabiliteTranslator,
)
from admission.ddd.admission.formation_generale.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import (
    IPropositionRepository,
)
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import (
    IAcademicYearRepository,
)


def recuperer_resume_proposition(
    cmd: 'RecupererResumePropositionQuery',
    proposition_repository: 'IPropositionRepository',
    i_profil_candidat_translator: 'IProfilCandidatTranslator',
    i_comptabilite_translator: 'IComptabiliteTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
) -> 'ResumePropositionDTO':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_dto = proposition_repository.get_dto(entity_id=proposition_id)
    comptabilite_dto = i_comptabilite_translator.get_comptabilite_dto(proposition_uuid=cmd.uuid_proposition)
    questions_specifiques_dtos = question_specifique_translator.search_dto_by_proposition(
        proposition_uuid=cmd.uuid_proposition,
    )

    # WHEN
    resume_dto = ResumeProposition.get_resume(
        profil_candidat_translator=i_profil_candidat_translator,
        academic_year_repository=academic_year_repository,
        proposition_dto=proposition_dto,
        comptabilite_dto=comptabilite_dto,
        questions_specifiques_dtos=questions_specifiques_dtos,
        experiences_cv_recuperees=(
            ExperiencesCVRecuperees.TOUTES
            if proposition_dto.est_non_soumise
            else ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION
        ),
    )

    # THEN
    return resume_dto
