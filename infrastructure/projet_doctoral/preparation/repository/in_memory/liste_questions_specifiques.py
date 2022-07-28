##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from admission.ddd.projet_doctoral.preparation.domain.model._enums import TypeItemFormulaire
from admission.ddd.projet_doctoral.preparation.domain.model.question_specifique import (
    ListeDesQuestionsSpecifiquesDeLaFormation,
    ListeDesQuestionsSpecifiquesDeLaFormationIdentity,
    QuestionSpecifique,
    QuestionSpecifiqueIdentity,
)
from admission.ddd.projet_doctoral.preparation.repository.i_liste_questions_specifiques import (
    IListeQuestionsSpecifiquesRepository,
)
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class ListeQuestionsSpecifiquesInMemoryRepository(InMemoryGenericRepository, IListeQuestionsSpecifiquesRepository):
    entities = [
        ListeDesQuestionsSpecifiquesDeLaFormation(
            entity_id=ListeDesQuestionsSpecifiquesDeLaFormationIdentity(sigle="SC3DP", annee=2020),
            questions=[
                QuestionSpecifique(
                    entity_id=QuestionSpecifiqueIdentity(uuid='06de0c3d-3c06-4c93-8eb4-c8648f04f140'),
                    type=TypeItemFormulaire.TEXTE,
                    poids=1,
                    supprimee=False,
                    label_interne='text_1',
                    requis=True,
                    titre={'en': 'Field 1', 'fr-be': 'Champ 1'},
                    texte={'en': 'Details', 'fr-be': 'Détails'},
                    texte_aide={'en': 'Write here', 'fr-be': 'Ecrivez ici'},
                    configuration={},
                ),
                QuestionSpecifique(
                    entity_id=QuestionSpecifiqueIdentity(uuid="06de0c3d-3c06-4c93-8eb4-c8648f04f141"),
                    type=TypeItemFormulaire.TEXTE,
                    poids=2,
                    supprimee=False,
                    label_interne='document_1',
                    requis=False,
                    titre={'en': 'Field 2', 'fr-be': 'Champ 2'},
                    texte={'en': 'Details', 'fr-be': 'Détails'},
                    texte_aide={},
                    configuration={},
                ),
                QuestionSpecifique(
                    entity_id=QuestionSpecifiqueIdentity(uuid="06de0c3d-3c06-4c93-8eb4-c8648f04f142"),
                    type=TypeItemFormulaire.TEXTE,
                    poids=3,
                    supprimee=True,
                    label_interne='text_2',
                    requis=True,
                    titre={'en': 'Field 3', 'fr-be': 'Champ 3'},
                    texte={'en': 'Details', 'fr-be': 'Détails'},
                    texte_aide={'en': 'Write here', 'fr-be': 'Ecrivez ici'},
                    configuration={},
                ),
            ],
        ),
        ListeDesQuestionsSpecifiquesDeLaFormation(
            entity_id=ListeDesQuestionsSpecifiquesDeLaFormationIdentity(sigle="ECGE3DP", annee=2020),
            questions=[
                QuestionSpecifique(
                    entity_id=QuestionSpecifiqueIdentity(uuid="06de0c3d-3c06-4c93-8eb4-c8648f04f143"),
                    type=TypeItemFormulaire.TEXTE,
                    poids=1,
                    supprimee=False,
                    label_interne='text_2',
                    requis=False,
                    titre={'en': 'Field 1', 'fr-be': 'Champ 1'},
                    texte={'en': 'Details', 'fr-be': 'Détails'},
                    texte_aide={'en': 'Write here', 'fr-be': 'Ecrivez ici'},
                    configuration={},
                ),
            ],
        ),
    ]

    @classmethod
    def get(
        cls,
        entity_id: 'ListeDesQuestionsSpecifiquesDeLaFormationIdentity',
    ) -> 'ListeDesQuestionsSpecifiquesDeLaFormation':
        question_list = super().get(entity_id)
        return ListeDesQuestionsSpecifiquesDeLaFormation(
            entity_id=entity_id,
            questions=[question for question in question_list.questions if not question.supprimee]
            if question_list
            else [],
        )
