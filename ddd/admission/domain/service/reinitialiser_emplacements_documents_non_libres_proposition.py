# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
# ##############################################################################
from typing import List

from admission.ddd.admission.domain.builder.emplacement_document_builder import EmplacementDocumentBuilder
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository
from admission.exports.admission_recap.section import get_sections
from osis_common.ddd import interface


class ReinitialiserEmplacementsDocumentsNonLibresPropositionService(interface.DomainService):
    @classmethod
    def reinitialiser_emplacements(
        cls,
        resume_dto: ResumePropositionDTO,
        questions_specifiques: List[QuestionSpecifiqueDTO],
        emplacement_document_repository: IEmplacementDocumentRepository,
    ):
        # Récupérer la liste des emplacements de documents par onglet
        onglets = get_sections(
            context=resume_dto,
            specific_questions=questions_specifiques,
            with_free_requestable_documents=False,
        )

        documents = []

        proposition_identity = PropositionIdentity(uuid=resume_dto.proposition.uuid)

        # Création d'un nouvel emplacement de document pour les documents catégorisés obligatoires à remplir
        for onglet in onglets:
            for document in onglet.attachments:
                if document.required and not document.uuids:
                    documents.append(
                        EmplacementDocumentBuilder.initialiser_emplacement_document_a_reclamer(
                            identifiant_emplacement=f'{onglet.identifier}.{document.identifier}',
                            uuid_proposition=proposition_identity.uuid,
                            auteur='',
                            raison='',
                        )
                    )

        emplacement_document_repository.reinitialiser_emplacements_documents_non_libres(
            proposition_identity=proposition_identity,
            entities=documents,
        )
