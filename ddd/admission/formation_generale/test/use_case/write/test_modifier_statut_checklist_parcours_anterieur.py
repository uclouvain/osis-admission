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

from admission.ddd.admission.formation_generale.commands import ModifierStatutChecklistParcoursAnterieurCommand
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutChecklist
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionNonTrouveeException,
    ConditionAccesEtreSelectionneException,
    TitreAccesEtreSelectionneException,
)
from admission.ddd.admission.formation_generale.test.factory.titre_acces import TitreAccesSelectionnableFactory
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from epc.models.enums.condition_acces import ConditionAcces


class TestModifierStatutChecklistParcoursAnterieurService(SimpleTestCase):
    def assertHasInstance(self, container, cls, msg=None):
        if not any(isinstance(obj, cls) for obj in container):
            self.fail(msg or f"No instance of '{cls}' has been found")

    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.titre_acces_repository = TitreAccesSelectionnableInMemoryRepositoryFactory()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance

    def test_should_modifier_si_statut_cible_est_initial_candidat(self):
        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistParcoursAnterieurCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                gestionnaire='0123456789',
            )
        )
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(
            proposition.checklist_actuelle.parcours_anterieur.statut,
            ChoixStatutChecklist.INITIAL_CANDIDAT,
        )

    def test_should_modifier_si_statut_cible_est_gestionnaire_en_cours(self):
        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistParcoursAnterieurCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                statut=ChoixStatutChecklist.GEST_EN_COURS.name,
                gestionnaire='0123456789',
            )
        )
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(
            proposition.checklist_actuelle.parcours_anterieur.statut,
            ChoixStatutChecklist.GEST_EN_COURS,
        )

    def test_should_modifier_si_statut_cible_est_gestionnaire_blocage(self):
        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistParcoursAnterieurCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                statut=ChoixStatutChecklist.GEST_BLOCAGE.name,
                gestionnaire='0123456789',
            )
        )
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(
            proposition.checklist_actuelle.parcours_anterieur.statut,
            ChoixStatutChecklist.GEST_BLOCAGE,
        )

    def test_should_modifier_si_statut_cible_est_gestionnaire_reussite_et_conditions_respectees(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                ModifierStatutChecklistParcoursAnterieurCommand(
                    uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                    statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                    gestionnaire='0123456789',
                )
            )
            self.assertHasInstance(context.exception.exceptions, ConditionAccesEtreSelectionneException)
            self.assertHasInstance(context.exception.exceptions, TitreAccesEtreSelectionneException)

        proposition = self.proposition_repository.get(PropositionIdentity('uuid-MASTER-SCI-CONFIRMED'))
        proposition.condition_acces = ConditionAcces.BAC
        proposition.millesime_condition_acces = 2021
        self.titre_acces_repository.entities.append(
            TitreAccesSelectionnableFactory(
                entity_id__uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                selectionne=True,
            )
        )

        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistParcoursAnterieurCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(
            proposition.checklist_actuelle.parcours_anterieur.statut,
            ChoixStatutChecklist.GEST_REUSSITE,
        )

    def test_should_empecher_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                ModifierStatutChecklistParcoursAnterieurCommand(
                    uuid_proposition='INCONNUE',
                    statut=ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                    gestionnaire='0123456789',
                )
            )
