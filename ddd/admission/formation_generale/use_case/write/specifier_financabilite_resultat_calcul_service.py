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
from admission.ddd.admission.formation_generale.commands import SpecifierFinancabiliteResultatCalculCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from ddd.logic.financabilite.domain.model.enums.situation import SituationFinancabilite


def specifier_financabilite_resultat_calcul(
    cmd: 'SpecifierFinancabiliteResultatCalculCommand',
    proposition_repository: 'IPropositionRepository',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    # THEN
    proposition.specifier_financabilite_resultat_calcul(
        financabilite_regle_calcule=EtatFinancabilite[cmd.financabilite_regle_calcule],
        financabilite_regle_calcule_situation=cmd.financabilite_regle_calcule_situation,
    )
    proposition_repository.save(proposition)

    return proposition_id
