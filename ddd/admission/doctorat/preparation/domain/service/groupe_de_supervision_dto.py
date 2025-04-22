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
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.dtos import (
    DetailSignatureMembreCADTO,
    DetailSignaturePromoteurDTO,
    GroupeDeSupervisionDTO,
)
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from osis_common.ddd import interface


class GroupeDeSupervisionDto(interface.DomainService):
    @classmethod
    def get(
        cls,
        uuid_proposition: str,
        repository: 'IGroupeDeSupervisionRepository',
    ) -> 'GroupeDeSupervisionDTO':
        groupe = repository.get_by_proposition_id(PropositionIdentityBuilder.build_from_uuid(uuid_proposition))
        membres_groupe = repository.get_members_by_member_id(groupe_id=groupe.entity_id)
        return GroupeDeSupervisionDTO(
            signatures_promoteurs=[
                DetailSignaturePromoteurDTO(
                    promoteur=membres_groupe.get(str(signature.promoteur_id.uuid)),
                    statut=signature.etat.name,
                    date=signature.date,
                    commentaire_externe=signature.commentaire_externe,
                    commentaire_interne=signature.commentaire_interne,
                    motif_refus=signature.motif_refus,
                    pdf=signature.pdf,
                )
                for signature in groupe.signatures_promoteurs
            ],
            signatures_membres_CA=[
                DetailSignatureMembreCADTO(
                    membre_CA=membres_groupe.get(str(signature.membre_CA_id.uuid)),
                    statut=signature.etat.name,
                    date=signature.date,
                    commentaire_externe=signature.commentaire_externe,
                    commentaire_interne=signature.commentaire_interne,
                    motif_refus=signature.motif_refus,
                    pdf=signature.pdf,
                )
                for signature in groupe.signatures_membres_CA
            ],
            promoteur_reference=groupe.promoteur_reference_id and str(groupe.promoteur_reference_id.uuid) or '',
            cotutelle=repository.get_cotutelle_dto_from_model(groupe.cotutelle),
        )
