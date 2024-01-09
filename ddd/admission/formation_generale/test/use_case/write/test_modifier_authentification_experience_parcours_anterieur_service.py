# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import SimpleTestCase

from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.domain.validator.exceptions import ExperienceNonTrouveeException
from admission.ddd.admission.formation_generale.commands import (
    ModifierAuthentificationExperienceParcoursAnterieurCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutChecklist
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestModifierAuthentificationExperienceParcoursAnterieur(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.proposition_repository.initialiser_checklist_proposition(
            PropositionIdentity(uuid='uuid-MASTER-SCI-CONFIRMED'),
        )
        self.experience_uuid = '9cbdf4db-2454-4cbf-9e48-55d2a9881ee3'

    def test_should_modifier_vers_statut_checklist_sans_indication_authentification(self):
        proposition_id = self.message_bus.invoke(
            ModifierAuthentificationExperienceParcoursAnterieurCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                uuid_experience=self.experience_uuid,
                etat_authentification=EtatAuthentificationParcours.VRAI.name,
            )
        )

        proposition = self.proposition_repository.get(proposition_id)

        checklist_experience = proposition.checklist_actuelle.recuperer_enfant(
            'parcours_anterieur',
            self.experience_uuid,
        )
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(checklist_experience.statut, ChoixStatutChecklist.INITIAL_CANDIDAT)
        self.assertEqual(
            checklist_experience.extra,
            {
                'identifiant': self.experience_uuid,
                'etat_authentification': EtatAuthentificationParcours.VRAI.name,
            },
        )

    def test_should_empecher_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                ModifierAuthentificationExperienceParcoursAnterieurCommand(
                    uuid_proposition='INCONNUE',
                    uuid_experience=self.experience_uuid,
                    etat_authentification=EtatAuthentificationParcours.VRAI.name,
                )
            )

    def test_should_empecher_si_experience_non_trouvee(self):
        with self.assertRaises(ExperienceNonTrouveeException):
            self.message_bus.invoke(
                ModifierAuthentificationExperienceParcoursAnterieurCommand(
                    uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                    uuid_experience='INCONNUE',
                    etat_authentification=EtatAuthentificationParcours.VRAI.name,
                )
            )
