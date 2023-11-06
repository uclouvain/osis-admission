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

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.domain.service.groupe_de_supervision_dto import GroupeDeSupervisionDto
from admission.ddd.admission.doctorat.preparation.domain.service.i_membre_CA import IMembreCATranslator
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.domain.service.i_emplacements_documents_proposition import (
    IEmplacementsDocumentsPropositionTranslator,
)
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.ddd.admission.doctorat.preparation.commands import RecupererDocumentsPropositionQuery
from admission.ddd.admission.doctorat.preparation.domain.service.i_comptabilite import IComptabiliteTranslator
from admission.ddd.admission.doctorat.preparation.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator


def recuperer_documents_proposition(
    cmd: 'RecupererDocumentsPropositionQuery',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    comptabilite_translator: 'IComptabiliteTranslator',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
    emplacements_documents_demande_translator: 'IEmplacementsDocumentsPropositionTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    personne_connue_translator: 'IPersonneConnueUclTranslator',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    promoteur_translator: 'IPromoteurTranslator',
    membre_ca_translator: 'IMembreCATranslator',
) -> 'List[EmplacementDocumentDTO]':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_dto = proposition_repository.get_dto(entity_id=proposition_id)
    comptabilite_dto = comptabilite_translator.get_comptabilite_dto(proposition_uuid=cmd.uuid_proposition)
    groupe_supervision_dto = GroupeDeSupervisionDto().get(
        uuid_proposition=cmd.uuid_proposition,
        repository=groupe_supervision_repository,
        promoteur_translator=promoteur_translator,
        membre_ca_translator=membre_ca_translator,
    )
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
        proposition_dto=proposition_dto,
        comptabilite_dto=comptabilite_dto,
        groupe_supervision_dto=groupe_supervision_dto,
        annee_courante=annee_courante,
    )
    questions_specifiques_dtos = question_specifique_translator.search_dto_by_proposition(
        proposition_uuid=cmd.uuid_proposition,
        type=TypeItemFormulaire.DOCUMENT.name,
    )

    # WHEN
    documents_dto = emplacements_documents_demande_translator.recuperer_emplacements_dto_proposition_doctorale(
        personne_connue_translator=personne_connue_translator,
        resume_dto=resume_dto,
        questions_specifiques=questions_specifiques_dtos,
    )

    # THEN
    return documents_dto
