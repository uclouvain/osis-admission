##############################################################################
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
##############################################################################
from admission.ddd.admission.formation_continue.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_continue.domain.service.i_comptabilite import IComptabiliteTranslator
from admission.ddd.admission.formation_continue.dtos import ComptabiliteDTO
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)


class ComptabiliteInMemoryTranslator(IComptabiliteTranslator):
    @classmethod
    def get_comptabilite_dto(cls, proposition_uuid: str) -> ComptabiliteDTO:
        comptabilite = PropositionInMemoryRepository.get(
            entity_id=PropositionIdentityBuilder.build_from_uuid(uuid=proposition_uuid)
        ).comptabilite

        return ComptabiliteDTO(
            etudiant_solidaire=comptabilite.etudiant_solidaire,
            type_numero_compte=comptabilite.type_numero_compte.name if comptabilite.type_numero_compte else '',
            numero_compte_iban=comptabilite.numero_compte_iban,
            iban_valide=comptabilite.iban_valide,
            numero_compte_autre_format=comptabilite.numero_compte_autre_format,
            code_bic_swift_banque=comptabilite.code_bic_swift_banque,
            prenom_titulaire_compte=comptabilite.prenom_titulaire_compte,
            nom_titulaire_compte=comptabilite.nom_titulaire_compte,
        )
