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
from admission.ddd.admission.domain.service.i_poste_diplomatique import IPosteDiplomatiqueTranslator
from admission.ddd.admission.formation_generale.commands import CompleterQuestionsSpecifiquesParGestionnaireCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def completer_questions_specifiques_par_gestionnaire(
    cmd: 'CompleterQuestionsSpecifiquesParGestionnaireCommand',
    proposition_repository: 'IPropositionRepository',
    poste_diplomatique_translator: 'IPosteDiplomatiqueTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_entity_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_candidat = proposition_repository.get(entity_id=proposition_entity_id)

    poste_diplomatique = poste_diplomatique_translator.get(cmd.poste_diplomatique)

    # WHEN
    proposition_candidat.completer_informations_complementaires_par_gestionnaire(
        reponses_questions_specifiques=cmd.reponses_questions_specifiques,
        documents_additionnels=cmd.documents_additionnels,
        poste_diplomatique=poste_diplomatique,
        est_non_resident_au_sens_decret=cmd.est_non_resident_au_sens_decret,
        est_bachelier_belge=cmd.est_bachelier_belge,
        est_reorientation_inscription_externe=cmd.est_reorientation_inscription_externe,
        attestation_inscription_reguliere=cmd.attestation_inscription_reguliere,
        est_modification_inscription_externe=cmd.est_modification_inscription_externe,
        formulaire_modification_inscription=cmd.formulaire_modification_inscription,
    )

    # THEN
    proposition_repository.save(proposition_candidat)

    return proposition_entity_id
