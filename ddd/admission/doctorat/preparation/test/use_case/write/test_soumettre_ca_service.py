# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

import freezegun
import mock
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import SoumettreCACommand
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import MembreCAManquantException
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPConfirmeeFactory,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


@freezegun.freeze_time('2020-11-01')
class TestSoumettreCaService(TestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.proposition = PropositionAdmissionSC3DPConfirmeeFactory(
            statut=ChoixStatutPropositionDoctorale.CA_EN_ATTENTE_DE_SIGNATURE
        )
        self.proposition_repository.save(self.proposition)
        self.groupe_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.addCleanup(self.groupe_supervision_repository.reset)
        self.message_bus = message_bus_in_memory_instance

        self.base_cmd = SoumettreCACommand(
            uuid_proposition=self.proposition.entity_id.uuid,
        )

    def test_should_soumettre_ca_etre_ok_si_groupe_complet(self):
        proposition_id = self.message_bus.invoke(self.base_cmd)

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)
        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC)
