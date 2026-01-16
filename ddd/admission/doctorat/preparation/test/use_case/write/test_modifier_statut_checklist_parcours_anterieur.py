# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from itertools import chain
from unittest.mock import patch

import freezegun
from django.test import SimpleTestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    ModifierStatutChecklistParcoursAnterieurCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    ConditionAccesEtreSelectionneException,
    PropositionNonTrouveeException,
    StatutsChecklistExperiencesEtreValidesException,
    TitreAccesEtreSelectionneException,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    StatutChecklist,
)
from admission.ddd.admission.formation_generale.test.factory.titre_acces import (
    TitreAccesSelectionnableFactory,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.admission.shared_kernel.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from epc.models.enums.condition_acces import ConditionAcces
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience


@freezegun.freeze_time('2020-01-01')
class TestModifierStatutChecklistParcoursAnterieurService(SimpleTestCase):
    def assertHasInstance(self, container, cls, msg=None):
        if not any(isinstance(obj, cls) for obj in container):
            self.fail(msg or f"No instance of '{cls}' has been found")

    @classmethod
    def setUpClass(cls):
        cls.profil_candidat_translator = ProfilCandidatInMemoryTranslator()

    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.titre_acces_repository = TitreAccesSelectionnableInMemoryRepositoryFactory()
        self.addCleanup(self.proposition_repository.reset)
        self.addCleanup(self.profil_candidat_translator.reset)

        self.message_bus = message_bus_in_memory_instance

        self.academic_year_repository = AcademicYearInMemoryRepository()

        for annee in range(2016, 2021):
            self.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

    def test_should_modifier_si_statut_cible_est_initial_candidat(self):
        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistParcoursAnterieurCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
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
                uuid_proposition='uuid-SC3DP-confirmee',
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
                uuid_proposition='uuid-SC3DP-confirmee',
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
                    uuid_proposition='uuid-SC3DP-confirmee',
                    statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                    gestionnaire='0123456789',
                )
            )
            self.assertHasInstance(context.exception.exceptions, ConditionAccesEtreSelectionneException)
            self.assertHasInstance(context.exception.exceptions, TitreAccesEtreSelectionneException)

        proposition = self.proposition_repository.get(PropositionIdentity('uuid-SC3DP-confirmee'))
        proposition.condition_acces = ConditionAcces.BAC
        proposition.millesime_condition_acces = 2021
        self.titre_acces_repository.entities.append(
            TitreAccesSelectionnableFactory(
                entity_id__uuid_proposition='uuid-SC3DP-confirmee',
                selectionne=True,
            )
        )

        experiences_academiques_candidat = [
            xp for xp in self.profil_candidat_translator.experiences_academiques
            if xp.personne == proposition.matricule_candidat
        ]

        experiences_non_academiques_candidat = [
            xp for xp in self.profil_candidat_translator.experiences_non_academiques
            if xp.personne == proposition.matricule_candidat
        ]

        for xp in experiences_academiques_candidat + experiences_non_academiques_candidat:
            xp.statut_validation = ChoixStatutValidationExperience.VALIDEE.name

        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistParcoursAnterieurCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                gestionnaire='0123456789',
            )
        )
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(
            proposition.checklist_actuelle.parcours_anterieur.statut,
            ChoixStatutChecklist.GEST_REUSSITE,
        )

        for xp in experiences_academiques_candidat + experiences_non_academiques_candidat:
            xp.statut_validation = ChoixStatutValidationExperience.A_COMPLETER_APRES_INSCRIPTION.name

        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistParcoursAnterieurCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                gestionnaire='0123456789',
            )
        )
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(
            proposition.checklist_actuelle.parcours_anterieur.statut,
            ChoixStatutChecklist.GEST_REUSSITE,
        )

        # Expérience académique avec un statut incorrect
        with patch.multiple(experiences_academiques_candidat[0], statut_validation=ChoixStatutValidationExperience.AVIS_EXPERT):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(
                    ModifierStatutChecklistParcoursAnterieurCommand(
                        uuid_proposition='uuid-SC3DP-confirmee',
                        statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                        gestionnaire='0123456789',
                    )
                )
                self.assertHasInstance(context.exception.exceptions, StatutsChecklistExperiencesEtreValidesException)

        # Expérience non-académique avec un statut incorrect
        with patch.multiple(experiences_non_academiques_candidat[0], statut_validation=ChoixStatutValidationExperience.AVIS_EXPERT):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(
                    ModifierStatutChecklistParcoursAnterieurCommand(
                        uuid_proposition='uuid-SC3DP-confirmee',
                        statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                        gestionnaire='0123456789',
                    )
                )
                self.assertHasInstance(context.exception.exceptions, StatutsChecklistExperiencesEtreValidesException)

    def test_should_empecher_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                ModifierStatutChecklistParcoursAnterieurCommand(
                    uuid_proposition='INCONNUE',
                    statut=ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                    gestionnaire='0123456789',
                )
            )
