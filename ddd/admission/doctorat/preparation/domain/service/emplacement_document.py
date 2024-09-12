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
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.enums.emplacement_document import (
    OngletsDemande,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository
from osis_common.ddd import interface


class EmplacementDocumentService(interface.DomainService):
    @classmethod
    def initier_emplacements_documents_approbation_sic(
        cls,
        proposition: Proposition,
        emplacement_document_repository: IEmplacementDocumentRepository,
        auteur: str,
    ):
        proposition_identity = PropositionIdentity(uuid=proposition.entity_id.uuid)

        emplacements_documents_a_initier = [
            emplacement_document_repository.get(
                entity_id=EmplacementDocumentIdentity(
                    identifiant=f'{OngletsDemande.SUITE_AUTORISATION.name}.AUTORISATION_PDF_SIGNEE',
                    proposition_id=proposition_identity,
                )
            )
        ]

        if proposition.doit_fournir_visa_etudes:
            emplacements_documents_a_initier.append(
                emplacement_document_repository.get(
                    entity_id=EmplacementDocumentIdentity(
                        identifiant=f'{OngletsDemande.SUITE_AUTORISATION.name}.VISA_ETUDES',
                        proposition_id=proposition_identity,
                    )
                )
            )

        for emplacement_document in emplacements_documents_a_initier:
            emplacement_document.specifier_reclamation(
                raison='',
                acteur=auteur,
                statut=StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT.name,
            )

        emplacement_document_repository.save_multiple(entities=emplacements_documents_a_initier, auteur=auteur)
