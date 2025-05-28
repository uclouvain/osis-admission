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
    SpecifierMotifsRefusPropositionParCDDCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    DecisionCDDEnum,
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
from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
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


class TestSpecifierMotifsRefusParCDD(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = SpecifierMotifsRefusPropositionParCDDCommand
        for matricule in ['00321234', '00987890']:
            PersonneConnueUclInMemoryTranslator.personnes_connues_ucl.add(
                PersonneConnueUclDTOFactory(matricule=matricule),
            )

    def setUp(self) -> None:
        self.proposition_repository.reset()
        self.proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-SC3DP-confirmee'))
        self.proposition.statut = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-SC3DP-confirmee',
            'uuids_motifs': ['uuid-nouveau-motif-refus'],
            'autres_motifs': [],
            'gestionnaire': '00321234',
        }

    def test_should_etre_ok_si_motif_connu_specifie_en_statut_traitement_fac(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC

        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition=self.proposition.entity_id.uuid,
                uuids_motifs=['uuid-nouveau-motif-refus'],
                autres_motifs=[],
                gestionnaire='0123456789',
            )
        )

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, self.proposition.entity_id.uuid)

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC)
        self.assertEqual(proposition.checklist_actuelle.decision_cdd.statut, ChoixStatutChecklist.GEST_BLOCAGE)
        self.assertEqual(
            proposition.checklist_actuelle.decision_cdd.extra,
            {'decision': DecisionCDDEnum.EN_DECISION.name},
        )
        self.assertEqual(proposition.motifs_refus, [MotifRefusIdentity(uuid='uuid-nouveau-motif-refus')])
        self.assertEqual(proposition.autres_motifs_refus, [])

    def test_should_etre_ok_si_motif_libre_specifie_en_statut_completee_pour_fac(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC

        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition=self.proposition.entity_id.uuid,
                uuids_motifs=[],
                autres_motifs=['Autre motif'],
                gestionnaire='0123456789',
            )
        )

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, self.proposition.entity_id.uuid)

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC)
        self.assertEqual(proposition.checklist_actuelle.decision_cdd.statut, ChoixStatutChecklist.GEST_BLOCAGE)
        self.assertEqual(
            proposition.checklist_actuelle.decision_cdd.extra,
            {'decision': DecisionCDDEnum.EN_DECISION.name},
        )
        self.assertEqual(proposition.motifs_refus, [])
        self.assertEqual(proposition.autres_motifs_refus, ['Autre motif'])

    def test_should_etre_ok_en_statut_a_completer_pour_fac(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC

        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition=self.proposition.entity_id.uuid,
                uuids_motifs=[],
                autres_motifs=[],
                gestionnaire='0123456789',
            )
        )

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, self.proposition.entity_id.uuid)

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC)

    def test_should_lever_exception_si_statut_non_conforme(self):
        statuts_invalides = ChoixStatutPropositionDoctorale.get_names_except(
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC,
            ChoixStatutPropositionDoctorale.TRAITEMENT_FAC,
            ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC,
        )

        for statut in statuts_invalides:
            self.proposition.statut = ChoixStatutPropositionDoctorale[statut]

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(context.exception.exceptions.pop(), SituationPropositionNonCddException)

    def test_should_lever_exception_si_statut_checklist_invalide(self):
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
