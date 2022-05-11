# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional
from unittest.mock import patch, _patch

from django.test import SimpleTestCase

from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixTypeAdmission
from admission.ddd.projet_doctoral.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPMinimaleFactory,
    PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    PropositionAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory,
    _PropositionFactory,
)
from admission.ddd.projet_doctoral.validation.commands import FiltrerDemandesQuery
from admission.ddd.projet_doctoral.validation.domain.model._enums import ChoixStatutCDD, ChoixStatutSIC
from admission.ddd.projet_doctoral.validation.dtos import DemandeRechercheDTO
from admission.ddd.projet_doctoral.validation.test.factory.demande import (
    DemandeAdmissionSC3DPMinimaleFactory,
    DemandePreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory,
    DemandeAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory,
    _DemandeFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.projet_doctoral.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.projet_doctoral.validation.repository.in_memory.demande import DemandeInMemoryRepository


class TestFiltrerDemandes(SimpleTestCase):
    proposition_patcher: Optional[_patch] = None
    demande_patcher: Optional[_patch] = None
    entites_propositions: List[_PropositionFactory] = []
    entites_demandes: List[_DemandeFactory] = []

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.entites_propositions = [
            PropositionAdmissionSC3DPMinimaleFactory(),
            PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
            PropositionAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory(),
        ]
        cls.proposition_patcher = patch.object(PropositionInMemoryRepository, 'entities', cls.entites_propositions)
        cls.proposition_patcher.start()

        cls.entites_demandes = [
            DemandeAdmissionSC3DPMinimaleFactory(),
            DemandePreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory(),
            DemandeAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory(),
        ]
        cls.demande_patcher = patch.object(DemandeInMemoryRepository, 'entities', cls.entites_demandes)
        cls.demande_patcher.start()
        cls.message_bus = message_bus_in_memory_instance

    @classmethod
    def tearDownClass(cls):
        cls.proposition_patcher.stop()
        cls.demande_patcher.stop()
        super().tearDownClass()

    def test_should_rechercher_sans_parametre(self):
        results: List[DemandeRechercheDTO] = self.message_bus.invoke(FiltrerDemandesQuery())
        self.assertEqual(len(results), 0)

    def test_should_rechercher_selon_parametre_proposition(self):
        proposition_recherchee = self.entites_propositions[0]
        resultats: List[DemandeRechercheDTO] = self.message_bus.invoke(
            FiltrerDemandesQuery(
                numero=proposition_recherchee.reference,
                type=ChoixTypeAdmission.ADMISSION.name,
            )
        )
        self.assertEqual(len(resultats), 1)
        self.assertEqual(resultats[0].numero_demande, proposition_recherchee.reference)

    def test_should_rechercher_selon_parametre_demande(self):
        resultats: List[DemandeRechercheDTO] = self.message_bus.invoke(
            FiltrerDemandesQuery(
                etat_cdd=ChoixStatutCDD.ACCEPTED.name,
            )
        )
        self.assertEqual(len(resultats), 1)
        self.assertEqual(resultats[0].statut_cdd, ChoixStatutCDD.ACCEPTED.name)

    def test_should_rechercher_selon_parametre_demande_et_proposition_avec_resultat_commun(self):
        demande_recherchee = self.entites_demandes[1]
        proposition_recherchee = self.entites_propositions[1]
        resultats: List[DemandeRechercheDTO] = self.message_bus.invoke(
            FiltrerDemandesQuery(etat_cdd=ChoixStatutCDD.ACCEPTED.name, numero=proposition_recherchee.reference)
        )
        self.assertEqual(len(resultats), 1)
        self.assertEqual(resultats[0].numero_demande, proposition_recherchee.reference)
        self.assertEqual(resultats[0].statut_cdd, demande_recherchee.statut_cdd.name)
        self.assertEqual(resultats[0].uuid, proposition_recherchee.entity_id.uuid)
        self.assertEqual(resultats[0].numero_demande, proposition_recherchee.reference)
        self.assertEqual(resultats[0].statut_cdd, demande_recherchee.statut_cdd.name)
        self.assertEqual(resultats[0].statut_sic, demande_recherchee.statut_sic.name)
        self.assertEqual(resultats[0].statut_demande, proposition_recherchee.statut.name)
        self.assertEqual(resultats[0].nom_candidat, 'Dupont, Jean')
        self.assertEqual(resultats[0].formation, 'SC3DP - Doctorat en sciences')
        self.assertEqual(resultats[0].nationalite, 'France')
        self.assertEqual(resultats[0].derniere_modification, proposition_recherchee.modifiee_le)
        self.assertEqual(resultats[0].code_bourse, 'ARC')

    def test_should_rechercher_selon_parametre_demande_et_proposition_sans_resultat_commun(self):
        proposition_recherchee = self.entites_propositions[0]
        resultats: List[DemandeRechercheDTO] = self.message_bus.invoke(
            FiltrerDemandesQuery(etat_cdd=ChoixStatutCDD.ACCEPTED.name, numero=proposition_recherchee.reference)
        )
        self.assertEqual(len(resultats), 0)

    def test_should_rechercher_sans_resultat(self):
        results: List[DemandeRechercheDTO] = self.message_bus.invoke(
            FiltrerDemandesQuery(
                numero='numero_inconnu',
            )
        )
        self.assertEqual(len(results), 0)

    def test_should_rechercher_et_trier_croissant(self):
        results: List[DemandeRechercheDTO] = self.message_bus.invoke(
            FiltrerDemandesQuery(
                etat_sic=ChoixStatutSIC.VALID.name,
                champ_tri='statut_cdd',
            )
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].statut_cdd, ChoixStatutCDD.ACCEPTED.name)
        self.assertEqual(results[1].statut_cdd, ChoixStatutCDD.REJECTED.name)

    def test_should_rechercher_et_trier_decroissant(self):
        results: List[DemandeRechercheDTO] = self.message_bus.invoke(
            FiltrerDemandesQuery(
                etat_sic=ChoixStatutSIC.VALID.name,
                tri_inverse=True,
                champ_tri='statut_cdd',
            )
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].statut_cdd, ChoixStatutCDD.REJECTED.name)
        self.assertEqual(results[1].statut_cdd, ChoixStatutCDD.ACCEPTED.name)
