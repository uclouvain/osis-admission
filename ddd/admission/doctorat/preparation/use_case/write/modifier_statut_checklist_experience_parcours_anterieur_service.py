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
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    ModifierStatutChecklistExperienceParcoursAnterieurCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import (
    IDoctoratTranslator,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)


def modifier_statut_checklist_experience_parcours_anterieur(
    cmd: 'ModifierStatutChecklistExperienceParcoursAnterieurCommand',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    doctorat_translator: 'IDoctoratTranslator',
) -> 'PropositionIdentity':
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    formation = doctorat_translator.get(sigle=proposition.formation_id.sigle, annee=proposition.formation_id.annee)

    proposition.specifier_statut_checklist_experience_parcours_anterieur(
        statut_checklist_cible=cmd.statut,
        statut_checklist_authentification=cmd.statut_authentification,
        uuid_experience=cmd.uuid_experience,
        auteur_modification=cmd.gestionnaire,
        type_experience=cmd.type_experience,
        profil_candidat_translator=profil_candidat_translator,
        grade_academique_formation_proposition=formation.grade_academique,
    )

    proposition_repository.save(proposition)

    return proposition_id
