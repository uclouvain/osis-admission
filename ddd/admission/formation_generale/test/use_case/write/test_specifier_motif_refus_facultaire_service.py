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
from unittest import TestCase

import factory

from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.ddd.admission.formation_generale.commands import (
    SpecifierMotifRefusFacultairePropositionCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    SituationPropositionNonFACException,
)
from admission.ddd.admission.formation_generale.test.factory.proposition import (
    PropositionFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestSpecifierMotifRefusFacultaireProposition(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = SpecifierMotifRefusFacultairePropositionCommand

    def setUp(self) -> None:
        self.proposition = PropositionFactory(
            entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-SCI-APPROVED'),
            matricule_candidat='0000000001',
            formation_id=FormationIdentityFactory(sigle="MASTER-SCI", annee=2021),
            curriculum=['file1.pdf'],
            est_confirmee=True,
            est_refusee_par_fac_raison_connue=True,
            statut=ChoixStatutPropositionGenerale.TRAITEMENT_FAC,
        )
        self.proposition_repository.save(self.proposition)
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-MASTER-SCI-APPROVED',
            'uuid_motif': 'uuid-nouveau-motif-refus',
            'autre_motif': '',
        }

    def test_should_etre_ok_si_motif_connu_specifie_en_statut_traitement_fac(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.TRAITEMENT_FAC

        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition='uuid-MASTER-SCI-APPROVED',
                uuid_motif='uuid-nouveau-motif-refus',
                autre_motif='',
            )
        )

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-MASTER-SCI-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.TRAITEMENT_FAC)
        self.assertEqual(proposition.checklist_actuelle.decision_facultaire.statut, ChoixStatutChecklist.GEST_BLOCAGE)
        self.assertEqual(proposition.checklist_actuelle.decision_facultaire.extra, {'decision': '1'})
        self.assertEqual(proposition.motif_refus_fac, MotifRefusIdentity(uuid='uuid-nouveau-motif-refus'))
        self.assertEqual(proposition.autre_motif_refus_fac, '')

    def test_should_etre_ok_si_motif_libre_specifie_en_statut_completee_pour_fac(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC

        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition='uuid-MASTER-SCI-APPROVED',
                uuid_motif='',
                autre_motif='Autre motif',
            )
        )

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-MASTER-SCI-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC)
        self.assertEqual(proposition.checklist_actuelle.decision_facultaire.statut, ChoixStatutChecklist.GEST_BLOCAGE)
        self.assertEqual(proposition.checklist_actuelle.decision_facultaire.extra, {'decision': '1'})
        self.assertEqual(proposition.motif_refus_fac, None)
        self.assertEqual(proposition.autre_motif_refus_fac, 'Autre motif')

    def test_should_etre_ok_en_statut_a_completer_pour_fac(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC

        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition='uuid-MASTER-SCI-APPROVED',
                uuid_motif='',
                autre_motif='',
            )
        )

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-MASTER-SCI-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC)

    def test_should_lever_exception_si_statut_non_conforme(self):
        statuts_invalides = ChoixStatutPropositionGenerale.get_names_except(
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC,
            ChoixStatutPropositionGenerale.TRAITEMENT_FAC,
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC,
        )

        for statut in statuts_invalides:
            self.proposition.statut = ChoixStatutPropositionGenerale[statut]
            with self.assertRaises(
                SituationPropositionNonFACException,
                msg=f'The following status must raise an exception: {statut}',
            ):
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
