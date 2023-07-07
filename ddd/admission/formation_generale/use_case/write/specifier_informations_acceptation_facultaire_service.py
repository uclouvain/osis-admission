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
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.commands import (
    SpecifierInformationsAcceptationFacultairePropositionCommand,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def specifier_informations_acceptation_facultaire(
    cmd: SpecifierInformationsAcceptationFacultairePropositionCommand,
    proposition_repository: 'IPropositionRepository',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    # WHEN
    Checklist.verifier_fac_peut_modifier_informations_decision_facultaire(proposition=proposition)

    # THEN
    proposition.specifier_informations_acceptation_par_fac(
        sigle_autre_formation=cmd.sigle_autre_formation,
        avec_conditions_complementaires=cmd.avec_conditions_complementaires,
        uuids_conditions_complementaires_existantes=cmd.uuids_conditions_complementaires_existantes,
        conditions_complementaires_libres=cmd.conditions_complementaires_libres,
        avec_complements_formation=cmd.avec_complements_formation,
        uuids_complements_formation=cmd.uuids_complements_formation,
        commentaire_complements_formation=cmd.commentaire_complements_formation,
        nombre_annees_prevoir_programme=cmd.nombre_annees_prevoir_programme,
        nom_personne_contact_programme_annuel=cmd.nom_personne_contact_programme_annuel,
        email_personne_contact_programme_annuel=cmd.email_personne_contact_programme_annuel,
        commentaire_programme_conjoint=cmd.commentaire_programme_conjoint,
    )

    proposition_repository.save(entity=proposition)

    return proposition.entity_id
