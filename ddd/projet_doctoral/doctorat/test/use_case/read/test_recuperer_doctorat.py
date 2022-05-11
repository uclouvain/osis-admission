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

from admission.ddd.projet_doctoral.doctorat.commands import RecupererDoctoratQuery
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.projet_doctoral.doctorat.dtos import DoctoratDTO
from admission.ddd.projet_doctoral.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPMinimaleFactory,
    PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    PropositionAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory,
    _PropositionFactory,
)
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


class TestRecupererDoctorat(SimpleTestCase):
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

    def test_should_pas_trouver_si_doctorat_inconnu(self):
        with self.assertRaises(DoctoratNonTrouveException):
            self.message_bus.invoke(
                RecupererDoctoratQuery(
                    doctorat_uuid='inconnu',
                )
            )

    def test_should_recuperer_doctorat_connu(self):
        doctorat_dto: DoctoratDTO = self.message_bus.invoke(
            RecupererDoctoratQuery(
                doctorat_uuid='uuid-SC3DP-promoteurs-membres-deja-approuves',
            )
        )
        self.assertEqual(doctorat_dto.uuid, 'uuid-SC3DP-promoteurs-membres-deja-approuves')
        self.assertEqual(doctorat_dto.reference, 'r4')

        self.assertEqual(doctorat_dto.statut, ChoixStatutDoctorat.ADMITTED.name)

        self.assertEqual(doctorat_dto.sigle_formation, 'SC3DP')
        self.assertEqual(doctorat_dto.annee_formation, 2022)
        self.assertEqual(doctorat_dto.intitule_formation, 'Doctorat en sciences')

        self.assertEqual(doctorat_dto.matricule_doctorant, '3')
        self.assertEqual(doctorat_dto.nom_doctorant, 'Dupond'),
        self.assertEqual(doctorat_dto.prenom_doctorant, 'Pierre')
