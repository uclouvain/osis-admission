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
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.doctorat.preparation.commands import ModifierChoixFormationParGestionnaireCommand
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository


def modifier_choix_formation_par_gestionnaire(
    cmd: 'ModifierChoixFormationParGestionnaireCommand',
    proposition_repository: 'IPropositionRepository',
    doctorat_translator: 'IDoctoratTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    proposition = proposition_repository.get(PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition))
    doctorat = doctorat_translator.get(proposition.formation_id.sigle, proposition.formation_id.annee)

    # WHEN
    proposition.modifier_choix_formation_gestionnaire(
        doctorat=doctorat,
        type_admission=cmd.type_admission,
        justification=cmd.justification,
        reponses_questions_specifiques=cmd.reponses_questions_specifiques,
        commission_proximite=cmd.commission_proximite,
        auteur=cmd.auteur,
    )

    # THEN
    proposition_repository.save(proposition)

    return proposition.entity_id
