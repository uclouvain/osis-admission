# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.projet_doctoral.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.projet_doctoral.preparation.commands import VerifierProjetCommand
from admission.ddd.projet_doctoral.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.projet_doctoral.preparation.domain.model.question_specifique import \
    ListeDesQuestionsSpecifiquesDeLaFormationIdentity
from admission.ddd.projet_doctoral.preparation.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.projet_doctoral.preparation.domain.service.verifier_projet_doctoral import VerifierProjetDoctoral
from admission.ddd.projet_doctoral.preparation.repository.i_groupe_de_supervision import IGroupeDeSupervisionRepository
from admission.ddd.projet_doctoral.preparation.repository.i_liste_questions_specifiques import \
    IListeQuestionsSpecifiquesRepository
from admission.ddd.projet_doctoral.preparation.repository.i_proposition import IPropositionRepository


def verifier_projet(
    cmd: 'VerifierProjetCommand',
    proposition_repository: 'IPropositionRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    promoteur_translator: 'IPromoteurTranslator',
    liste_questions_specifiques_repository: 'IListeQuestionsSpecifiquesRepository',
) -> 'PropositionIdentity':
    # GIVEN
    entity_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_candidat = proposition_repository.get(entity_id=entity_id)
    groupe_de_supervision = groupe_supervision_repository.get_by_proposition_id(entity_id)
    liste_questions_specifiques = liste_questions_specifiques_repository.get(
        ListeDesQuestionsSpecifiquesDeLaFormationIdentity(
            annee=proposition_candidat.annee,
            sigle=proposition_candidat.sigle_formation,
        )
    )

    # WHEN
    VerifierProjetDoctoral.verifier(
        proposition_candidat,
        groupe_de_supervision,
        liste_questions_specifiques,
        promoteur_translator,
    )

    # THEN
    return entity_id
