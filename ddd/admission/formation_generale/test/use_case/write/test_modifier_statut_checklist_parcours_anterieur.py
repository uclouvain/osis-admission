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

from django.test import SimpleTestCase

from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_generale.commands import (
    ModifierStatutChecklistParcoursAnterieurCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    StatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    ConditionAccesEtreSelectionneException,
    PropositionNonTrouveeException,
    StatutsChecklistExperiencesEtreValidesException,
    TitreAccesEtreSelectionneException,
)
from admission.ddd.admission.formation_generale.test.factory.titre_acces import (
    TitreAccesSelectionnableFactory,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from epc.models.enums.condition_acces import ConditionAcces


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
            self.assertHasInstance(context.exception.exceptions, StatutsChecklistExperiencesEtreValidesException)

        proposition = self.proposition_repository.get(PropositionIdentity('uuid-MASTER-SCI-CONFIRMED'))
        proposition.condition_acces = ConditionAcces.BAC
        proposition.millesime_condition_acces = 2021
        self.titre_acces_repository.entities.append(
            TitreAccesSelectionnableFactory(
                entity_id__uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                selectionne=True,
            )
        )
        proposition.checklist_actuelle.parcours_anterieur.enfants.append(
            StatutChecklist(
                libelle='l1',
                statut=ChoixStatutChecklist.GEST_REUSSITE,
                extra={'identifiant': OngletsDemande.ETUDES_SECONDAIRES.name},
            ),
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

        # Expériences avec un statut incorrect mais inconnues ou non valorisées -> non prises en compte
        checklist_experience = StatutChecklist(
            libelle='l1',
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'identifiant': 'INCONNUE'},
        )
        proposition.checklist_actuelle.parcours_anterieur.enfants.append(checklist_experience)

        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistParcoursAnterieurCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                gestionnaire='0123456789',
            )
        )
        self.assertIsNotNone(proposition_id)

        # Expérience valorisée et avec un statut incorrect -> lever une exception
        self.profil_candidat_translator.valorisations[checklist_experience.extra['identifiant']] = [
            'uuid-MASTER-SCI-CONFIRMED'
        ]

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                ModifierStatutChecklistParcoursAnterieurCommand(
                    uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                    statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                    gestionnaire='0123456789',
                )
            )
            self.assertHasInstance(context.exception.exceptions, StatutsChecklistExperiencesEtreValidesException)

        checklist_experience.statut = ChoixStatutChecklist.GEST_REUSSITE

        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistParcoursAnterieurCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                gestionnaire='0123456789',
            )
        )
        self.assertIsNotNone(proposition_id)

        checklist_experience.statut = ChoixStatutChecklist.GEST_BLOCAGE_ULTERIEUR

        proposition_id = self.message_bus.invoke(
            ModifierStatutChecklistParcoursAnterieurCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                gestionnaire='0123456789',
            )
        )
        self.assertIsNotNone(proposition_id)

        # Expérience valorisée mais sans checklist -> lever une exception
        self.profil_candidat_translator.valorisations['INCONNUE-VALORISEE'] = ['uuid-MASTER-SCI-CONFIRMED']

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                ModifierStatutChecklistParcoursAnterieurCommand(
                    uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                    statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                    gestionnaire='0123456789',
                )
            )
            self.assertHasInstance(context.exception.exceptions, StatutsChecklistExperiencesEtreValidesException)

    def test_should_renvoyer_erreur_si_statut_cible_est_gestionnaire_reussite_et_incomplet_pour_certificat(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            proposition_id = self.message_bus.invoke(
                ModifierStatutChecklistParcoursAnterieurCommand(
                    uuid_proposition='uuid-CERTIFICATE-CONFIRMED',
                    statut=ChoixStatutChecklist.GEST_REUSSITE.name,
                    gestionnaire='0123456789',
                )
            )

            self.assertHasInstance(context.exception.exceptions, ConditionAccesEtreSelectionneException)
            self.assertHasInstance(context.exception.exceptions, TitreAccesEtreSelectionneException)

    def test_should_empecher_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                ModifierStatutChecklistParcoursAnterieurCommand(
                    uuid_proposition='INCONNUE',
                    statut=ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                    gestionnaire='0123456789',
                )
            )
