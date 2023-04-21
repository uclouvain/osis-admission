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

from admission.ddd.admission.domain.model.demande import DemandeIdentity
from admission.ddd.admission.domain.service.i_emplacements_documents_demande import (
    IEmplacementsDocumentsDemandeTranslator,
)
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.ddd.admission.formation_generale.commands import DeterminerEmplacementsDocumentsDemandeCommand
from admission.ddd.admission.formation_generale.commands import RecupererDocumentsDemandeQuery
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_comptabilite import IComptabiliteTranslator
from admission.ddd.admission.formation_generale.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository


def determiner_emplacements_documents_demande(
    cmd: 'DeterminerEmplacementsDocumentsDemandeCommand',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    comptabilite_translator: 'IComptabiliteTranslator',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
) -> 'DemandeIdentity':
    # GIVEN
    proposition_dto = proposition_repository.get_dto(entity_id=PropositionIdentity(uuid=cmd.uuid_demande))
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
    IEmplacementsDocumentsDemandeTranslator.reinitialiser_emplacements(
        resume_dto=resume_dto,
        questions_specifiques=questions_specifiques_dtos,
        emplacement_document_repository=emplacement_document_repository,
    )

    # THEN
    return DemandeIdentity(uuid=cmd.uuid_demande)
