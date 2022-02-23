# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.preparation.projet_doctoral.repository.i_proposition import IPropositionRepository
from admission.ddd.validation.projet_doctoral.domain.model.demande import DemandeIdentity
from admission.ddd.validation.projet_doctoral.domain.service.proposition_identity import PropositionIdentityTranslator
from admission.ddd.validation.projet_doctoral.dtos import RecupererDemandeDTO
from admission.ddd.validation.projet_doctoral.repository.i_demande import IDemandeRepository
from osis_common.ddd import interface


class DemandeService(interface.DomainService):
    @classmethod
    def recuperer(
        cls,
        demande_id: DemandeIdentity,
        demande_repository: IDemandeRepository,
        proposition_repository: IPropositionRepository,
    ) -> RecupererDemandeDTO:
        proposition_id = PropositionIdentityTranslator.convertir_depuis_demande(demande_id)
        proposition_dto = proposition_repository.get_dto(proposition_id)
        demande_dto = demande_repository.get_dto(demande_id)
        # TODO
        return RecupererDemandeDTO(
            statut_cdd="",
            statut_sic="",
            derniere_modification=None,
        )
