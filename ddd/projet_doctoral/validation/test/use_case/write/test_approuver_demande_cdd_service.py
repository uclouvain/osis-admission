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
import datetime
from typing import List, Optional
from unittest.mock import patch, _patch

from django.test import SimpleTestCase

from admission.ddd.projet_doctoral.doctorat.builder.doctorat_identity import DoctoratIdentityBuilder
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.doctorat.domain.service.demande_identity import DemandeIdentityTranslator
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixStatutProposition
from admission.ddd.projet_doctoral.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPMinimaleFactory,
    PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    PropositionAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory,
    _PropositionFactory,
)
from admission.ddd.projet_doctoral.validation.commands import ApprouverDemandeCddCommand
from admission.ddd.projet_doctoral.validation.domain.model._enums import ChoixStatutCDD
from admission.ddd.projet_doctoral.validation.domain.service.proposition_identity import PropositionIdentityTranslator
from admission.ddd.projet_doctoral.validation.test.factory.demande import (
    DemandeAdmissionSC3DPMinimaleFactory,
    DemandePreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory,
    DemandeAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory,
    _DemandeFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.projet_doctoral.doctorat.epreuve_confirmation.repository.in_memory.epreuve_confirmation \
    import (EpreuveConfirmationInMemoryRepository)
from admission.infrastructure.projet_doctoral.doctorat.repository.in_memory.doctorat import DoctoratInMemoryRepository
from admission.infrastructure.projet_doctoral.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.projet_doctoral.validation.repository.in_memory.demande import DemandeInMemoryRepository


class TestApprouverDemandeCDD(SimpleTestCase):
    proposition_patcher: Optional[_patch] = None
    demande_patcher: Optional[_patch] = None
    date_patcher: Optional[_patch] = None
    entites_propositions: List[_PropositionFactory] = []
    entites_demandes: List[_DemandeFactory] = []

    @classmethod
    def setUpClass(cls) -> None:
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

        # Mock datetime to return the 2020 year as the current year
        cls.date_patcher = patch(
            'admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.domain.service.epreuve_confirmation.datetime',
        )
        mock_date = cls.date_patcher.start()
        mock_date.date.today.return_value = datetime.date(2020, 11, 1)

    @classmethod
    def tearDownClass(cls):
        cls.proposition_patcher.stop()
        cls.demande_patcher.stop()
        cls.date_patcher.stop()

    def setUp(self):
        self.message_bus = message_bus_in_memory_instance

    def test_should_approuver_demande_a_verifier(self):
        demande_a_approuver_entity_id = self.entites_demandes[0].entity_id

        demande_approuvee_id = self.message_bus.invoke(ApprouverDemandeCddCommand(demande_a_approuver_entity_id.uuid))

        # Returned result
        self.assertEqual(demande_approuvee_id, demande_a_approuver_entity_id)

        # Updated proposition
        proposition_id = PropositionInMemoryRepository.get(
            PropositionIdentityTranslator.convertir_depuis_demande(demande_a_approuver_entity_id),
        )
        proposition = PropositionInMemoryRepository.get(proposition_id.entity_id)
        self.assertEqual(proposition.statut, ChoixStatutProposition.ENROLLED)

        # Updated dossier
        demande = DemandeInMemoryRepository.get(demande_a_approuver_entity_id)
        self.assertEqual(demande.statut_cdd, ChoixStatutCDD.ACCEPTED)

        # Update doctorat
        doctorat_id = DemandeIdentityTranslator.convertir_en_doctorat(demande_a_approuver_entity_id)
        doctorat = DoctoratInMemoryRepository.get(doctorat_id)
        self.assertEqual(doctorat.statut, ChoixStatutDoctorat.ADMITTED)

        # New confirmation paper
        epreuves_confirmations = EpreuveConfirmationInMemoryRepository.search_by_doctorat_identity(
            doctorat_entity_id=doctorat_id,
        )

        self.assertEqual(len(epreuves_confirmations), 1)
        self.assertEqual(
            epreuves_confirmations[0].date_limite,
            datetime.date(2022, 11, 1),
        )
