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
from unittest import TestCase

from admission.ddd.admission.domain.validator.exceptions import PosteDiplomatiqueNonTrouveException
from admission.ddd.admission.formation_generale.commands import (
    CompleterQuestionsSpecifiquesCommand,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PropositionNonTrouveeException
from admission.infrastructure.admission.domain.service.in_memory.poste_diplomatique import (
    PosteDiplomatiqueInMemoryFactory,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestCompleterQuestionsSpecifiquesService(TestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()

        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.poste_diplomatique_translator = PosteDiplomatiqueInMemoryFactory()

    def test_should_completer(self):
        proposition_id = self.message_bus.invoke(
            CompleterQuestionsSpecifiquesCommand(
                uuid_proposition='uuid-MASTER-SCI',
                reponses_questions_specifiques={
                    '35db2d60-9874-41fc-9f5a-ebfea38277d0': 'valeur',
                },
                documents_additionnels=['5453f700-9c1a-4f3e-99b4-20ba6e638299'],
                poste_diplomatique=1,
            )
        )
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition

        # Vérifier le retour de la commande
        self.assertEqual(proposition_id, proposition.entity_id)

        # Vérifier que la proposition a bien été mise à jour
        self.assertEqual(
            proposition.reponses_questions_specifiques,
            {
                '35db2d60-9874-41fc-9f5a-ebfea38277d0': 'valeur',
            },
        )
        self.assertEqual(proposition.documents_additionnels, ['5453f700-9c1a-4f3e-99b4-20ba6e638299'])
        self.assertEqual(proposition.poste_diplomatique.code, 1)

    def test_should_lever_exception_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                CompleterQuestionsSpecifiquesCommand(
                    uuid_proposition='INCONNUE',
                    reponses_questions_specifiques={},
                    documents_additionnels=[],
                    poste_diplomatique=None,
                )
            )

    def test_should_lever_exception_si_poste_diplomatique_non_trouve(self):
        with self.assertRaises(PosteDiplomatiqueNonTrouveException):
            self.message_bus.invoke(
                CompleterQuestionsSpecifiquesCommand(
                    uuid_proposition='uuid-MASTER-SCI',
                    reponses_questions_specifiques={},
                    documents_additionnels=[],
                    poste_diplomatique=10,
                )
            )
