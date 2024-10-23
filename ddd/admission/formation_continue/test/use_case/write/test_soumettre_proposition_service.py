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
import freezegun
from django.test import TestCase

from admission.ddd.admission.formation_continue.commands import SoumettrePropositionCommand
from admission.ddd.admission.formation_continue.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.infrastructure.admission.domain.service.in_memory.elements_confirmation import (
    ElementsConfirmationInMemory,
)
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.models.enums.academic_calendar_type import AcademicCalendarTypes


@freezegun.freeze_time('2020-11-01')
class TestSoumettrePropositionContinue(TestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance

    def test_should_soumettre_proposition_etre_ok_si_admission_complete(self):
        proposition = self.proposition_repository.get(PropositionIdentityBuilder.build_from_uuid("uuid-USCC1"))
        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(
                uuid_proposition="uuid-USCC1",
                pool=AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name,
                annee=2020,
                elements_confirmation=ElementsConfirmationInMemory.get_elements_for_tests(proposition),
            ),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)
        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionContinue.CONFIRMEE)
        self.assertEqual(updated_proposition.auteur_derniere_modification, proposition.matricule_candidat)

    def test_should_soumettre_proposition_en_nettoyant_reponses_questions_specifiques(self):
        proposition = self.proposition_repository.get(PropositionIdentityBuilder.build_from_uuid("uuid-USCC1"))

        proposition.reponses_questions_specifiques = {
            '26de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
            # A default value will be set
            # '26de0c3d-3c06-4c93-8eb4-c8648f04f141': 'My response 1',
            '26de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
            '26de0c3d-3c06-4c93-8eb4-c8648f04f144': 'My response 4',
            '26de0c3d-3c06-4c93-8eb4-c8648f04f145': ['24de0c3d-3c06-4c93-8eb4-c8648f04f144'],
            # Will be deleted as it's a readonly element
            '26de0c3d-3c06-4c93-8eb4-c8648f04f142': 'MESSAGE',
            # Will be deleted as it's not interesting for this admission
            '36de0c3d-3c06-4c93-8eb4-c8648f04f140': 'Not interesting response 0',
            '36de0c3d-3c06-4c93-8eb4-c8648f04f141': 'Not interesting response 1',
        }

        self.proposition_repository.save(proposition)

        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(
                uuid_proposition="uuid-USCC1",
                pool=AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name,
                annee=2020,
                elements_confirmation=ElementsConfirmationInMemory.get_elements_for_tests(proposition),
            ),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)

        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionContinue.CONFIRMEE)

        self.assertEqual(
            updated_proposition.reponses_questions_specifiques,
            {
                '26de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
                '26de0c3d-3c06-4c93-8eb4-c8648f04f141': '',
                '26de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
                '26de0c3d-3c06-4c93-8eb4-c8648f04f144': 'My response 4',
                '26de0c3d-3c06-4c93-8eb4-c8648f04f145': ['24de0c3d-3c06-4c93-8eb4-c8648f04f144'],
            },
        )
