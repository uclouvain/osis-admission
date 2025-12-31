# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.shared_kernel.commands import SpecifierExperienceEnTantQueTitreAccesCommand
from admission.ddd.admission.shared_kernel.domain.builder.titre_acces_selectionnable_builder import (
    TitreAccesSelectionnableBuilder,
)
from admission.ddd.admission.shared_kernel.domain.model.titre_acces_selectionnable import (
    TitreAccesSelectionnableIdentity,
)
from admission.ddd.admission.shared_kernel.domain.validator.validator_by_business_action import (
    SpecifierExperienceCommeTitreAccesValidatorList,
)
from admission.ddd.admission.shared_kernel.repository.i_titre_acces_selectionnable import (
    ITitreAccesSelectionnableRepository,
)
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import IExperienceParcoursInterneTranslator


def specifier_experience_en_tant_que_titre_acces(
    cmd: 'SpecifierExperienceEnTantQueTitreAccesCommand',
    titre_acces_selectionnable_repository: 'ITitreAccesSelectionnableRepository',
    experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
) -> 'TitreAccesSelectionnableIdentity':
    proposition_identity = PropositionIdentity(uuid=cmd.uuid_proposition)

    titres_acces_selectionnes = titre_acces_selectionnable_repository.search_by_proposition(
        proposition_identity=proposition_identity,
        experience_parcours_interne_translator=experience_parcours_interne_translator,
        seulement_selectionnes=True,
    )

    titre_acces = TitreAccesSelectionnableBuilder.build_from_command(cmd=cmd)

    SpecifierExperienceCommeTitreAccesValidatorList(
        titre_acces_modifie=titre_acces,
        titres_acces_deja_selectionnes=titres_acces_selectionnes,
    ).validate()

    titre_acces_selectionnable_repository.save(titre_acces)

    return titre_acces.entity_id
