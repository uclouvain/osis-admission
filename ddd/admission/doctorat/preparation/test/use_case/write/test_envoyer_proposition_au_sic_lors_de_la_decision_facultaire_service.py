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

import factory
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    DecisionFacultaireEnum,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    SituationPropositionNonFACException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.groupe_de_supervision import (
    GroupeDeSupervisionSC3DPFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestEnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand
        cls.parametres_commande_par_defaut = {
            'gestionnaire': '00321234',
            'uuid_proposition': '',
            'envoi_par_fac': True,
        }

    def setUp(self) -> None:
        self.proposition_repository.reset()
        self.proposition = PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(
            entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-APPROVED'),
            matricule_candidat='0123456789',
            formation_id=FormationIdentityFactory(sigle="SC3DP", annee=2020),
            est_confirmee=True,
            est_approuvee_par_fac=True,
            statut=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC,
        )
        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.groupe_de_supervision_repository.save(
            GroupeDeSupervisionSC3DPFactory(
                proposition_id=self.proposition.entity_id,
            )
        )
        self.parametres_commande_par_defaut['uuid_proposition'] = self.proposition.entity_id.uuid
        self.proposition_repository.save(self.proposition)

    def test_should_etre_ok_si_proposition_avec_les_bons_statuts_proposition_et_checklist(self):
        # Proposition: TRAITEMENT_FAC et checklist: INITIAL_CANDIDAT
        self.proposition.statut = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC
        self.proposition.checklist_actuelle.decision_facultaire.statut = ChoixStatutChecklist.INITIAL_CANDIDAT
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat, self.proposition.entity_id)

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC)

        # Proposition: COMPLETEE_POUR_FAC et checklist: GEST_EN_COURS
        self.proposition.statut = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC
        self.proposition.checklist_actuelle.decision_facultaire.statut = ChoixStatutChecklist.GEST_EN_COURS
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat, self.proposition.entity_id)

        # Proposition: COMPLETEE_POUR_FAC et checklist: GEST_BLOCAGE sans decision
        self.proposition.statut = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC
        self.proposition.checklist_actuelle.decision_facultaire.statut = ChoixStatutChecklist.GEST_BLOCAGE
        self.proposition.checklist_actuelle.decision_facultaire.extra = {
            'decision': DecisionFacultaireEnum.HORS_DECISION.value,
        }
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat, self.proposition.entity_id)

    def test_should_lever_exception_si_statuts_non_conformes(self):
        self.proposition.checklist_actuelle.decision_facultaire.statut = ChoixStatutChecklist.GEST_EN_COURS

        # Statut de la proposition non conforme
        statuts_invalides = ChoixStatutPropositionDoctorale.get_names_except(
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC,
            ChoixStatutPropositionDoctorale.TRAITEMENT_FAC,
        )

        for statut in statuts_invalides:
            self.proposition.statut = ChoixStatutPropositionDoctorale[statut]
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
                self.assertIsInstance(context.exception.exceptions.pop(), SituationPropositionNonFACException)
