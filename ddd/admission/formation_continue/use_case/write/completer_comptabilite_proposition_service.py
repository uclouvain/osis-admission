# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.formation_continue.commands import CompleterComptabilitePropositionCommand
from admission.ddd.admission.formation_continue.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_continue.repository.i_proposition import IPropositionRepository


def completer_comptabilite_proposition(
    cmd: 'CompleterComptabilitePropositionCommand',
    proposition_repository: 'IPropositionRepository',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_entity_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_candidat = proposition_repository.get(entity_id=proposition_entity_id)

    # WHEN
    proposition_candidat.completer_comptabilite(
        etudiant_solidaire=cmd.etudiant_solidaire,
        type_numero_compte=cmd.type_numero_compte,
        numero_compte_iban=cmd.numero_compte_iban,
        iban_valide=cmd.iban_valide,
        numero_compte_autre_format=cmd.numero_compte_autre_format,
        code_bic_swift_banque=cmd.code_bic_swift_banque,
        prenom_titulaire_compte=cmd.prenom_titulaire_compte,
        nom_titulaire_compte=cmd.nom_titulaire_compte,
    )

    # THEN
    proposition_repository.save(proposition_candidat)

    return proposition_entity_id
