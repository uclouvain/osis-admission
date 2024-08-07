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
import datetime
from unittest import mock

import freezegun
from django.test import TestCase

from admission.ddd.admission.formation_generale.commands import (
    SpecifierPaiementPlusNecessaireCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionPourPaiementInvalideException,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


@freezegun.freeze_time('2020-11-01')
class TestSpecifierPaiementPlusNecessaire(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.academic_year_repository = AcademicYearInMemoryRepository()
        for annee in range(2016, 2023):
            cls.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )
        cls.message_bus = message_bus_in_memory_instance

    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.candidat = self.candidat_translator.profil_candidats[1]
        self.proposition = self.proposition_repository.get(
            PropositionIdentity(
                uuid='uuid-MASTER-SCI-CONFIRMED',
            ),
        )

        self.commande_candidat_non_concerne_selon_systeme = SpecifierPaiementPlusNecessaireCommand(
            uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
            gestionnaire='987654321',
            statut_checklist_frais_dossier=ChoixStatutChecklist.INITIAL_NON_CONCERNE.name,
        )

        self.commande_candidat_non_concerne_selon_gestionnaire = SpecifierPaiementPlusNecessaireCommand(
            uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
            gestionnaire='987654321',
            statut_checklist_frais_dossier=ChoixStatutChecklist.GEST_REUSSITE.name,
        )

    def test_should_specifier_paiement_plus_necessaire_etre_ok(self):
        # INITIAL_NON_CONCERNE -> GEST_REUSSITE
        with mock.patch.multiple(
            self.proposition.checklist_actuelle.frais_dossier,
            statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
        ):
            proposition_id = self.message_bus.invoke(self.commande_candidat_non_concerne_selon_gestionnaire)

        proposition = self.proposition_repository.get(proposition_id)

        # Résultat de la commande
        self.assertEqual(proposition_id.uuid, proposition.entity_id.uuid)

        # Proposition mise à jour
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.CONFIRMEE)
        self.assertEqual(proposition.checklist_actuelle.frais_dossier.statut, ChoixStatutChecklist.GEST_REUSSITE)
        self.assertEqual(proposition.checklist_actuelle.frais_dossier.libelle, 'Dispensed')

        # GEST_REUSSITE -> INITIAL_NON_CONCERNE
        with mock.patch.multiple(
            self.proposition.checklist_actuelle.frais_dossier,
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        ):
            proposition_id = self.message_bus.invoke(self.commande_candidat_non_concerne_selon_systeme)

        proposition = self.proposition_repository.get(proposition_id)

        # Résultat de la commande
        self.assertEqual(proposition_id.uuid, proposition.entity_id.uuid)

        # Proposition mise à jour
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.CONFIRMEE)
        self.assertEqual(proposition.checklist_actuelle.frais_dossier.statut, ChoixStatutChecklist.INITIAL_NON_CONCERNE)
        self.assertEqual(proposition.checklist_actuelle.frais_dossier.libelle, 'Not concerned')

        # GEST_BLOCAGE -> GEST_REUSSITE
        with mock.patch.multiple(
            self.proposition.checklist_actuelle.frais_dossier,
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
        ):
            proposition_id = self.message_bus.invoke(self.commande_candidat_non_concerne_selon_gestionnaire)

        proposition = self.proposition_repository.get(proposition_id)

        # Résultat de la commande
        self.assertEqual(proposition_id.uuid, proposition.entity_id.uuid)

        # Proposition mise à jour
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.CONFIRMEE)
        self.assertEqual(proposition.checklist_actuelle.frais_dossier.statut, ChoixStatutChecklist.GEST_REUSSITE)
        self.assertEqual(proposition.checklist_actuelle.frais_dossier.libelle, 'Dispensed')

        # GEST_BLOCAGE -> INITIAL_NON_CONCERNE
        with mock.patch.multiple(
            self.proposition.checklist_actuelle.frais_dossier,
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
        ):
            proposition_id = self.message_bus.invoke(self.commande_candidat_non_concerne_selon_systeme)

        proposition = self.proposition_repository.get(proposition_id)

        # Résultat de la commande
        self.assertEqual(proposition_id.uuid, proposition.entity_id.uuid)

        # Proposition mise à jour
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.CONFIRMEE)
        self.assertEqual(proposition.checklist_actuelle.frais_dossier.statut, ChoixStatutChecklist.INITIAL_NON_CONCERNE)
        self.assertEqual(proposition.checklist_actuelle.frais_dossier.libelle, 'Not concerned')

    def test_should_lever_exception_si_frais_deja_payes_a_la_soumission(self):
        with mock.patch.multiple(
            self.proposition.checklist_initiale.frais_dossier,
            statut=ChoixStatutChecklist.SYST_REUSSITE,
        ):
            with self.assertRaises(PropositionPourPaiementInvalideException):
                self.message_bus.invoke(self.commande_candidat_non_concerne_selon_systeme)

            with self.assertRaises(PropositionPourPaiementInvalideException):
                self.message_bus.invoke(self.commande_candidat_non_concerne_selon_gestionnaire)

    def test_should_lever_exception_si_frais_deja_payes_suite_demande_gestionnaire(self):
        with mock.patch.multiple(
            self.proposition.checklist_actuelle.frais_dossier,
            statut=ChoixStatutChecklist.SYST_REUSSITE,
        ):
            with self.assertRaises(PropositionPourPaiementInvalideException):
                self.message_bus.invoke(self.commande_candidat_non_concerne_selon_systeme)

            with self.assertRaises(PropositionPourPaiementInvalideException):
                self.message_bus.invoke(self.commande_candidat_non_concerne_selon_gestionnaire)
