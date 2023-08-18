# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.formation_continue.commands import CompleterQuestionsSpecifiquesCommand
from admission.ddd.admission.formation_continue.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_continue.repository.i_proposition import IPropositionRepository


def completer_questions_specifiques(
    cmd: 'CompleterQuestionsSpecifiquesCommand',
    proposition_repository: 'IPropositionRepository',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_entity_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_candidat = proposition_repository.get(entity_id=proposition_entity_id)

    # WHEN
    proposition_candidat.completer_informations_complementaires(
        inscription_a_titre=cmd.inscription_a_titre,
        nom_siege_social=cmd.nom_siege_social,
        numero_unique_entreprise=cmd.numero_unique_entreprise,
        numero_tva_entreprise=cmd.numero_tva_entreprise,
        adresse_mail_professionnelle=cmd.adresse_mail_professionnelle,
        type_adresse_facturation=cmd.type_adresse_facturation,
        adresse_facturation_rue=cmd.adresse_facturation_rue,
        adresse_facturation_numero_rue=cmd.adresse_facturation_numero_rue,
        adresse_facturation_code_postal=cmd.adresse_facturation_code_postal,
        adresse_facturation_ville=cmd.adresse_facturation_ville,
        adresse_facturation_pays=cmd.adresse_facturation_pays,
        adresse_facturation_destinataire=cmd.adresse_facturation_destinataire,
        adresse_facturation_boite_postale=cmd.adresse_facturation_boite_postale,
        reponses_questions_specifiques=cmd.reponses_questions_specifiques,
        copie_titre_sejour=cmd.copie_titre_sejour,
        documents_additionnels=cmd.documents_additionnels,
    )

    # THEN
    proposition_repository.save(proposition_candidat)

    return proposition_entity_id
