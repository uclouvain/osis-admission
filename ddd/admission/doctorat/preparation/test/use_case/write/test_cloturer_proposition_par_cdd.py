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
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    CloturerPropositionParCddCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    SituationPropositionNonCddException,
    StatutChecklistDecisionCddDoitEtreDifferentClotureException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.person import (
    PersonneConnueUclDTOFactory,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)


class TestCloturerPropositionParCdd(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = CloturerPropositionParCddCommand
        for matricule in ['00321234', '00987890']:
            PersonneConnueUclInMemoryTranslator.personnes_connues_ucl.add(
                PersonneConnueUclDTOFactory(matricule=matricule),
            )

    def setUp(self) -> None:
        self.proposition_repository.reset()
        self.proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-SC3DP-confirmee'))
        self.proposition.statut = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-SC3DP-confirmee',
            'gestionnaire': '00321234',
        }

    def test_should_etre_ok_si_statuts_corrects(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC

        statuts_decision_cdd = ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[OngletsChecklist.decision_cdd.name]

        statut_a_traiter = statuts_decision_cdd['A_TRAITER']
        statut_cloture = statuts_decision_cdd['CLOTURE']

        self.proposition.checklist_actuelle.decision_cdd.statut = statut_a_traiter.statut
        self.proposition.checklist_actuelle.decision_cdd.extra = statut_a_traiter.extra.copy()

        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-SC3DP-confirmee')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.CLOTUREE)
        self.assertEqual(proposition.checklist_actuelle.decision_cdd.statut, statut_cloture.statut)
        self.assertEqual(proposition.checklist_actuelle.decision_cdd.extra, statut_cloture.extra)
        self.assertEqual(proposition.auteur_derniere_modification, '00321234')

    def test_should_lever_exception_si_statut_non_conforme(self):
        statuts_invalides = ChoixStatutPropositionDoctorale.get_names_except(
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC,
            ChoixStatutPropositionDoctorale.TRAITEMENT_FAC,
        )

        for statut in statuts_invalides:
            self.proposition.statut = ChoixStatutPropositionDoctorale[statut]

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
                self.assertIsInstance(context.exception.exceptions.pop(), SituationPropositionNonCddException)

    def test_should_lever_exception_si_statut_checklist_invalide(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC

        statuts_decision_cdd = ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[OngletsChecklist.decision_cdd.name]

        statuts_invalides = {
            'CLOTURE',
        }

        for identifiant_statut in statuts_invalides:
            statut = statuts_decision_cdd[identifiant_statut]
            self.proposition.checklist_actuelle.decision_cdd.statut = statut.statut
            self.proposition.checklist_actuelle.decision_cdd.extra = statut.extra.copy()

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

            self.assertIsInstance(
                context.exception.exceptions.pop(),
                StatutChecklistDecisionCddDoitEtreDifferentClotureException,
            )
