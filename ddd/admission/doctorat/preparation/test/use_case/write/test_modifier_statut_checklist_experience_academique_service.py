# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock

from django.test import SimpleTestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    ModifierStatutChecklistExperienceAcademiqueCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    ExperiencesAcademiquesNonCompleteesException,
    PropositionNonTrouveeException,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.modifier_checklist_experience_parcours_anterieur import (
    ValidationExperienceParcoursAnterieurInMemoryService,
)
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.community import CommunityEnum
from ddd.logic.shared_kernel.profil.domain.enums import TypeExperience
from osis_profile.models.enums.experience_validation import (
    ChoixStatutValidationExperience,
    EtatAuthentificationParcours,
)
from reference.models.enums.cycle import Cycle


class TestModifierStatutChecklistExperienceAcademique(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.proposition_entity_id = PropositionIdentity(uuid='uuid-SC3DP-confirmee')
        self.experience_academique_uuid = '9cbdf4db-2454-4cbf-9e48-55d2a9881ee1'
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.experiences_academiques = self.candidat_translator.experiences_academiques
        self.experience_academique = next(
            exp for exp in self.experiences_academiques if exp.uuid == self.experience_academique_uuid
        )
        self.validation_experience_service = ValidationExperienceParcoursAnterieurInMemoryService()

    def test_should_modifier_vers_statut_checklist_validee(self):
        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistExperienceAcademiqueCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                uuid_experience=self.experience_academique_uuid,
                statut=ChoixStatutValidationExperience.VALIDEE.name,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)

        informations_validation = (
            self.validation_experience_service.recuperer_information_validation_experience_academique(
                uuid_experience=self.experience_academique_uuid,
            )
        )

        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(informations_validation.uuid, self.experience_academique_uuid)
        self.assertEqual(informations_validation.type_experience, TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name)
        self.assertEqual(informations_validation.statut_validation, ChoixStatutValidationExperience.VALIDEE.name)
        self.assertEqual(
            informations_validation.statut_authentification, EtatAuthentificationParcours.NON_CONCERNE.name
        )

    def test_should_modifier_vers_statut_checklist_d_authentification(self):
        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistExperienceAcademiqueCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                uuid_experience=self.experience_academique_uuid,
                statut=ChoixStatutValidationExperience.AUTHENTIFICATION.name,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)

        informations_validation = (
            self.validation_experience_service.recuperer_information_validation_experience_academique(
                uuid_experience=self.experience_academique_uuid,
            )
        )

        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(informations_validation.uuid, self.experience_academique_uuid)
        self.assertEqual(informations_validation.type_experience, TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name)
        self.assertEqual(
            informations_validation.statut_validation, ChoixStatutValidationExperience.AUTHENTIFICATION.name
        )
        self.assertEqual(
            informations_validation.statut_authentification, EtatAuthentificationParcours.NON_CONCERNE.name
        )

    def test_should_modifier_vers_statut_checklist_pas_d_authentification(self):
        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistExperienceAcademiqueCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                uuid_experience=self.experience_academique_uuid,
                statut=ChoixStatutValidationExperience.A_COMPLETER.name,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)

        informations_validation = (
            self.validation_experience_service.recuperer_information_validation_experience_academique(
                uuid_experience=self.experience_academique_uuid,
            )
        )

        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(informations_validation.uuid, self.experience_academique_uuid)
        self.assertEqual(informations_validation.type_experience, TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name)
        self.assertEqual(informations_validation.statut_validation, ChoixStatutValidationExperience.A_COMPLETER.name)
        self.assertEqual(
            informations_validation.statut_authentification, EtatAuthentificationParcours.NON_CONCERNE.name
        )

    def test_should_empecher_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                ModifierStatutChecklistExperienceAcademiqueCommand(
                    uuid_proposition='INCONNUE',
                    uuid_experience=self.experience_academique_uuid,
                    statut=ChoixStatutValidationExperience.AVIS_EXPERT.name,
                    gestionnaire='0123456789',
                )
            )

    def test_should_verifier_experience_academique_complete_pour_passage_a_valide(self):
        with mock.patch.multiple(
            self.experience_academique,
            a_obtenu_diplome=False,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=None,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(
                    ModifierStatutChecklistExperienceAcademiqueCommand(
                        uuid_proposition='uuid-SC3DP-confirmee',
                        uuid_experience=self.experience_academique_uuid,
                        statut=ChoixStatutValidationExperience.VALIDEE.name,
                        gestionnaire='0123456789',
                    )
                )

            self.assertIsInstance(
                context.exception.exceptions.pop(),
                ExperiencesAcademiquesNonCompleteesException,
            )

        with mock.patch.multiple(
            self.experience_academique,
            a_obtenu_diplome=False,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=None,
            grade_academique_formation='2',
        ):
            proposition_id = self.message_bus.invoke(
                ModifierStatutChecklistExperienceAcademiqueCommand(
                    uuid_proposition='uuid-SC3DP-confirmee',
                    uuid_experience=self.experience_academique_uuid,
                    statut=ChoixStatutValidationExperience.VALIDEE.name,
                    gestionnaire='0123456789',
                )
            )
            self.assertEqual(proposition_id, self.proposition_entity_id)

        with mock.patch.multiple(
            self.experience_academique,
            a_obtenu_diplome=False,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=True,
            credits_inscrits_complements=None,
            credits_acquis_complements=10,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(
                    ModifierStatutChecklistExperienceAcademiqueCommand(
                        uuid_proposition='uuid-SC3DP-confirmee',
                        uuid_experience=self.experience_academique_uuid,
                        statut=ChoixStatutValidationExperience.VALIDEE.name,
                        gestionnaire='0123456789',
                    )
                )

            self.assertIsInstance(
                context.exception.exceptions.pop(),
                ExperiencesAcademiquesNonCompleteesException,
            )

        with mock.patch.multiple(
            self.experience_academique,
            a_obtenu_diplome=False,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=True,
            credits_inscrits_complements=10,
            credits_acquis_complements=None,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(
                    ModifierStatutChecklistExperienceAcademiqueCommand(
                        uuid_proposition='uuid-SC3DP-confirmee',
                        uuid_experience=self.experience_academique_uuid,
                        statut=ChoixStatutValidationExperience.VALIDEE.name,
                        gestionnaire='0123456789',
                    )
                )

            self.assertIsInstance(
                context.exception.exceptions.pop(),
                ExperiencesAcademiquesNonCompleteesException,
            )

        with mock.patch.multiple(
            self.experience_academique,
            a_obtenu_diplome=False,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.FIRST_CYCLE.name,
            credits_acquis_bloc_1=None,
        ):
            proposition_id = self.message_bus.invoke(
                ModifierStatutChecklistExperienceAcademiqueCommand(
                    uuid_proposition='uuid-SC3DP-confirmee',
                    uuid_experience=self.experience_academique_uuid,
                    statut=ChoixStatutValidationExperience.A_COMPLETER.name,
                    gestionnaire='0123456789',
                )
            )

            self.assertEqual(proposition_id.uuid, 'uuid-SC3DP-confirmee')

        with mock.patch.multiple(
            self.experience_academique,
            a_obtenu_diplome=False,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.FIRST_CYCLE.name,
            credits_acquis_bloc_1=None,
        ):
            proposition_id = self.message_bus.invoke(
                ModifierStatutChecklistExperienceAcademiqueCommand(
                    uuid_proposition='uuid-SC3DP-confirmee',
                    uuid_experience=self.experience_academique_uuid,
                    statut=ChoixStatutValidationExperience.A_COMPLETER.name,
                    gestionnaire='0123456789',
                )
            )

            self.assertEqual(proposition_id.uuid, 'uuid-SC3DP-confirmee')

        with mock.patch.multiple(
            self.experience_academique,
            a_obtenu_diplome=False,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.FIRST_CYCLE.name,
            credits_acquis_bloc_1=10,
        ):
            proposition_id = self.message_bus.invoke(
                ModifierStatutChecklistExperienceAcademiqueCommand(
                    uuid_proposition='uuid-SC3DP-confirmee',
                    uuid_experience=self.experience_academique_uuid,
                    statut=ChoixStatutValidationExperience.A_COMPLETER.name,
                    gestionnaire='0123456789',
                )
            )

            self.assertEqual(proposition_id.uuid, 'uuid-SC3DP-confirmee')

        with mock.patch.multiple(
            self.experience_academique,
            a_obtenu_diplome=False,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=True,
            credits_inscrits_complements=10,
            credits_acquis_complements=10,
        ):
            proposition_id = self.message_bus.invoke(
                ModifierStatutChecklistExperienceAcademiqueCommand(
                    uuid_proposition='uuid-SC3DP-confirmee',
                    uuid_experience=self.experience_academique_uuid,
                    statut=ChoixStatutValidationExperience.A_COMPLETER.name,
                    gestionnaire='0123456789',
                )
            )

            self.assertEqual(proposition_id.uuid, 'uuid-SC3DP-confirmee')

        with mock.patch.multiple(
            self.experience_academique,
            a_obtenu_diplome=False,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=False,
            credits_inscrits_complements=None,
            credits_acquis_complements=None,
        ):
            proposition_id = self.message_bus.invoke(
                ModifierStatutChecklistExperienceAcademiqueCommand(
                    uuid_proposition='uuid-SC3DP-confirmee',
                    uuid_experience=self.experience_academique_uuid,
                    statut=ChoixStatutValidationExperience.A_COMPLETER.name,
                    gestionnaire='0123456789',
                )
            )

            self.assertEqual(proposition_id.uuid, 'uuid-SC3DP-confirmee')
