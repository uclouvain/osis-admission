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
from admission.models.enums.actor_type import ActorType
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import IdentifierPromoteurCommand
from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.admission.doctorat.preparation.domain.service.membres_groupe_de_supervision import (
    MembresGroupeDeSupervision,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.validator_by_business_action import (
    IdentifierPromoteurValidatorList,
)
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository


def identifier_promoteur(
    cmd: 'IdentifierPromoteurCommand',
    proposition_repository: 'IPropositionRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    promoteur_translator: 'IPromoteurTranslator',
    historique: 'IHistorique',
) -> 'PromoteurIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    groupe_de_supervision = groupe_supervision_repository.get_by_proposition_id(proposition_id)
    proposition = proposition_repository.get(proposition_id)

    # WHEN
    IdentifierPromoteurValidatorList(
        groupe_de_supervision=groupe_de_supervision,
        matricule=cmd.matricule,
        prenom=cmd.prenom,
        nom=cmd.nom,
        email=cmd.email,
        institution=cmd.institution,
        ville=cmd.ville,
        pays=cmd.pays,
        langue=cmd.langue,
    ).validate()
    promoteur_translator.verifier_existence(cmd.matricule)
    MembresGroupeDeSupervision.verifier_pas_deja_present(
        groupe_de_supervision.entity_id,
        groupe_supervision_repository,
        matricule=cmd.matricule,
        email=cmd.email,
    )

    # THEN
    promoteur_id = groupe_supervision_repository.add_member(
        groupe_id=groupe_de_supervision.entity_id,
        type=ActorType.PROMOTER,
        matricule=cmd.matricule,
        first_name=cmd.prenom,
        last_name=cmd.nom,
        email=cmd.email,
        is_doctor=cmd.est_docteur,
        institute=cmd.institution,
        city=cmd.ville,
        country_code=cmd.pays,
        language=cmd.langue,
    )
    historique.historiser_ajout_membre(proposition, groupe_de_supervision, promoteur_id)

    return promoteur_id  # type: ignore[return-value]
