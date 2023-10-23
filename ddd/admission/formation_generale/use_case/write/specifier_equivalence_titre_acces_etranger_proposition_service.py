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
from admission.ddd.admission.formation_generale.commands import SpecifierEquivalenceTitreAccesEtrangerPropositionCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def specifier_equivalence_titre_acces_etranger_proposition(
    cmd: 'SpecifierEquivalenceTitreAccesEtrangerPropositionCommand',
    proposition_repository: 'IPropositionRepository',
) -> 'PropositionIdentity':
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    proposition.specifier_equivalence_titre_acces(
        type_equivalence_titre_acces=cmd.type_equivalence_titre_acces,
        statut_equivalence_titre_acces=cmd.statut_equivalence_titre_acces,
        etat_equivalence_titre_acces=cmd.etat_equivalence_titre_acces,
        date_prise_effet_equivalence_titre_acces=cmd.date_prise_effet_equivalence_titre_acces,
    )

    proposition_repository.save(proposition)

    return proposition_id
