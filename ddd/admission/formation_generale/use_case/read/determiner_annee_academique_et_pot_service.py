# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Union

from admission.ddd.admission.domain.service.i_calendrier_inscription import (
    ICalendrierInscription,
)
from admission.ddd.admission.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.domain.service.i_titres_acces import ITitresAcces
from admission.ddd.admission.dtos.conditions import InfosDetermineesDTO
from admission.ddd.admission.formation_generale.commands import (
    DeterminerAnneeAcademiqueEtPotQuery,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.service.i_formation import (
    IFormationGeneraleTranslator,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import (
    IPropositionRepository,
)


def determiner_annee_academique_et_pot(
    cmd: 'DeterminerAnneeAcademiqueEtPotQuery',
    proposition_repository: Union['IPropositionRepository'],
    formation_translator: Union['IFormationGeneraleTranslator'],
    titres_acces: 'ITitresAcces',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    calendrier_inscription: 'ICalendrierInscription',
) -> 'InfosDetermineesDTO':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    # THEN
    formation = formation_translator.get(proposition.formation_id)
    type_formation = formation.type
    titres = titres_acces.recuperer_titres_access(
        proposition.matricule_candidat,
        type_formation,
        proposition.equivalence_diplome,
    )
    return calendrier_inscription.determiner_annee_academique_et_pot(
        formation_id=proposition.formation_id,
        proposition=proposition,
        matricule_candidat=proposition.matricule_candidat,
        titres_acces=titres,
        profil_candidat_translator=profil_candidat_translator,
        formation=formation,
    )
