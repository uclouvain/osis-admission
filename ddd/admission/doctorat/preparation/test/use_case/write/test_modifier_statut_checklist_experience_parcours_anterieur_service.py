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

from admission.ddd.admission.doctorat.preparation.commands import (
    ModifierStatutChecklistExperienceParcoursAnterieurCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import ChoixStatutChecklist
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestModifierStatutChecklistExperienceParcoursAnterieur(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.proposition_repository.initialiser_checklist_proposition(
            PropositionIdentity(uuid='uuid-SC3DP-confirmee'),
        )
        self.experience_uuid = '9cbdf4db-2454-4cbf-9e48-55d2a9881ee1'

    def test_should_verifier_etat_initial_checklist(self):
        proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-SC3DP-confirmee'))
        enfants_parcours_anterieur = proposition.checklist_actuelle.parcours_anterieur.enfants
        uuids_experiences = [
            # Experiences academiques
            '9cbdf4db-2454-4cbf-9e48-55d2a9881ee1',
            '9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
            # Experiences non academiques
            '0cbdf4db-2454-4cbf-9e48-55d2a9881ee1',
            '0cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
        ]

        self.assertEqual(len(enfants_parcours_anterieur), len(uuids_experiences))

        for index, experience in enumerate(enfants_parcours_anterieur):
            self.assertEqual(experience.statut, ChoixStatutChecklist.INITIAL_CANDIDAT)
            self.assertEqual(experience.libelle, 'To be processed')
            self.assertEqual(experience.extra.get('etat_authentification'), 'NON_CONCERNE')
            self.assertEqual(experience.extra.get('identifiant'), uuids_experiences[index])

    def test_should_modifier_vers_statut_checklist_sans_indication_authentification(self):
        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistExperienceParcoursAnterieurCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                uuid_experience=self.experience_uuid,
                statut=ChoixStatutChecklist.SYST_REUSSITE.name,
                statut_authentification=None,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)

        checklist_experience = proposition.checklist_actuelle.recuperer_enfant(
            'parcours_anterieur',
            self.experience_uuid,
        )
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(checklist_experience.statut, ChoixStatutChecklist.SYST_REUSSITE)
        self.assertEqual(
            checklist_experience.extra,
            {
                'identifiant': self.experience_uuid,
                'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
            },
        )

    def test_should_modifier_vers_statut_checklist_d_authentification(self):
        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistExperienceParcoursAnterieurCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                uuid_experience=self.experience_uuid,
                statut=ChoixStatutChecklist.GEST_BLOCAGE.name,
                statut_authentification=True,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)

        checklist_experience = proposition.checklist_actuelle.recuperer_enfant(
            'parcours_anterieur',
            self.experience_uuid,
        )
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(checklist_experience.statut, ChoixStatutChecklist.GEST_BLOCAGE)
        self.assertEqual(
            checklist_experience.extra,
            {
                'identifiant': self.experience_uuid,
                'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
                'authentification': '1',
            },
        )

    def test_should_modifier_vers_statut_checklist_pas_d_authentification(self):
        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistExperienceParcoursAnterieurCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                uuid_experience=self.experience_uuid,
                statut=ChoixStatutChecklist.GEST_BLOCAGE.name,
                statut_authentification=False,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)

        checklist_experience = proposition.checklist_actuelle.recuperer_enfant(
            'parcours_anterieur',
            self.experience_uuid,
        )
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(checklist_experience.statut, ChoixStatutChecklist.GEST_BLOCAGE)
        self.assertEqual(
            checklist_experience.extra,
            {
                'identifiant': self.experience_uuid,
                'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
                'authentification': '0',
            },
        )

    def test_should_empecher_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                ModifierStatutChecklistExperienceParcoursAnterieurCommand(
                    uuid_proposition='INCONNUE',
                    uuid_experience=self.experience_uuid,
                    statut=ChoixStatutChecklist.GEST_BLOCAGE.name,
                    statut_authentification=False,
                    gestionnaire='0123456789',
                )
            )

    def test_should_creer_experience_si_non_trouvee(self):
        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistExperienceParcoursAnterieurCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                uuid_experience='INCONNUE',
                statut=ChoixStatutChecklist.GEST_BLOCAGE.name,
                statut_authentification=False,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)

        checklist_experience = proposition.checklist_actuelle.recuperer_enfant(
            'parcours_anterieur',
            'INCONNUE',
        )
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(checklist_experience.statut, ChoixStatutChecklist.GEST_BLOCAGE)
        self.assertEqual(
            checklist_experience.extra,
            {
                'identifiant': 'INCONNUE',
                'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
                'authentification': '0',
            },
        )
