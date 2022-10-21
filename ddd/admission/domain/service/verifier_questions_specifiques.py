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
from typing import Union, List

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition as PropositionDoctorale
from admission.ddd.admission.domain.model.question_specifique import QuestionSpecifique
from admission.ddd.admission.domain.validator.exceptions import (
    QuestionsSpecifiquesCurriculumNonCompleteesException,
    QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
    QuestionsSpecifiquesChoixFormationNonCompleteesException,
)
from admission.ddd.admission.enums.question_specifique import Onglets
from admission.ddd.admission.formation_continue.domain.model.proposition import (
    Proposition as PropositionFormationContinue,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition as PropositionFormationGenerale,
)

from osis_common.ddd import interface


class VerifierQuestionsSpecifiques(interface.DomainService):
    @classmethod
    def _questions_requises_bien_specifiees(
        cls,
        proposition: Union['PropositionDoctorale', 'PropositionFormationContinue', 'PropositionFormationGenerale'],
        questions_specifiques: List['QuestionSpecifique'],
        onglet: Onglets,
    ) -> bool:
        return all(
            proposition.reponses_questions_specifiques.get(str(question.entity_id.uuid))
            for question in questions_specifiques
            if question.requis and question.onglet == onglet
        )

    @classmethod
    def verifier_onglet_curriculum(
        cls,
        proposition: Union['PropositionDoctorale', 'PropositionFormationContinue', 'PropositionFormationGenerale'],
        questions_specifiques: List['QuestionSpecifique'],
    ):
        if not cls._questions_requises_bien_specifiees(proposition, questions_specifiques, Onglets.CURRICULUM):
            raise QuestionsSpecifiquesCurriculumNonCompleteesException

    @classmethod
    def verifier_onglet_etudes_secondaires(
        cls,
        proposition: Union['PropositionDoctorale', 'PropositionFormationContinue', 'PropositionFormationGenerale'],
        questions_specifiques: List['QuestionSpecifique'],
    ):
        if not cls._questions_requises_bien_specifiees(proposition, questions_specifiques, Onglets.ETUDES_SECONDAIRES):
            raise QuestionsSpecifiquesEtudesSecondairesNonCompleteesException

    @classmethod
    def verifier_onglet_choix_formation(
        cls,
        proposition: Union['PropositionDoctorale', 'PropositionFormationContinue', 'PropositionFormationGenerale'],
        questions_specifiques: List['QuestionSpecifique'],
    ):
        if not cls._questions_requises_bien_specifiees(proposition, questions_specifiques, Onglets.CHOIX_FORMATION):
            raise QuestionsSpecifiquesChoixFormationNonCompleteesException
