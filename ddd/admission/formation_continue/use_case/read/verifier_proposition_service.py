# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.domain.service.i_calendrier_inscription import ICalendrierInscription
from admission.ddd.admission.domain.service.i_maximum_propositions import IMaximumPropositionsAutorisees
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.i_titres_acces import ITitresAcces
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_continue.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from ...commands import VerifierPropositionQuery
from ...domain.builder.proposition_identity_builder import PropositionIdentityBuilder
from ...domain.model.proposition import PropositionIdentity
from ...domain.service.i_formation import IFormationContinueTranslator
from ...domain.service.verifier_proposition import VerifierProposition
from ...repository.i_proposition import IPropositionRepository


def verifier_proposition(
    cmd: 'VerifierPropositionQuery',
    proposition_repository: 'IPropositionRepository',
    formation_translator: 'IFormationContinueTranslator',
    titres_acces: 'ITitresAcces',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    calendrier_inscription: 'ICalendrierInscription',
    maximum_propositions_service: 'IMaximumPropositionsAutorisees',
    questions_specifiques_translator: 'IQuestionSpecifiqueTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)
    questions_specifiques = questions_specifiques_translator.search_by_proposition(
        cmd.uuid_proposition,
        onglets=Onglets.get_names(),
    )

    # WHEN
    VerifierProposition.verifier(
        proposition,
        formation_translator,
        titres_acces,
        profil_candidat_translator,
        calendrier_inscription,
        maximum_propositions_service,
        questions_specifiques,
    )

    # THEN
    return proposition_id
