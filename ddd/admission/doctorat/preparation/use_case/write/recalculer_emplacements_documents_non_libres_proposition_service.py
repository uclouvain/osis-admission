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
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand,
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
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.reinitialiser_emplacements_documents_non_libres_proposition import (
    ReinitialiserEmplacementsDocumentsNonLibresPropositionService,
)
from admission.ddd.admission.shared_kernel.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.shared_kernel.enums import TypeItemFormulaire
from admission.ddd.admission.shared_kernel.repository.i_emplacement_document import (
    IEmplacementDocumentRepository,
)
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import (
    IAcademicYearRepository,
)


def recalculer_emplacements_documents_non_libres_proposition(
    cmd: 'RecalculerEmplacementsDocumentsNonLibresPropositionCommand',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    comptabilite_translator: 'IComptabiliteTranslator',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
    academic_year_repository: 'IAcademicYearRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
) -> PropositionIdentity:
    # GIVEN
    resume_dto = ResumeProposition.get_resume_demande_doctorat(
        uuid_proposition=cmd.uuid_proposition,
        proposition_repository=proposition_repository,
        comptabilite_translator=comptabilite_translator,
        profil_candidat_translator=profil_candidat_translator,
        academic_year_repository=academic_year_repository,
        groupe_supervision_repository=groupe_supervision_repository,
        question_specifique_translator=question_specifique_translator,
    )

    # WHEN
    ReinitialiserEmplacementsDocumentsNonLibresPropositionService.reinitialiser_emplacements(
        resume_dto=resume_dto,
        questions_specifiques=resume_dto.questions_specifiques_dtos,
        emplacement_document_repository=emplacement_document_repository,
    )

    return PropositionIdentity(uuid=cmd.uuid_proposition)
