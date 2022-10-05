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
from unittest.mock import patch

from django.test import SimpleTestCase

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutProposition
from admission.ddd.admission.doctorat.validation.builder.demande_identity import DemandeIdentityBuilder
from admission.ddd.admission.doctorat.validation.commands import ApprouverDemandeCddCommand
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD
from admission.ddd.admission.doctorat.validation.domain.service.proposition_identity import (
    PropositionIdentityTranslator,
)
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.parcours_doctoral.domain.service.demande_identity import DemandeIdentityTranslator
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.doctorat.validation.repository.in_memory.demande import (
    DemandeInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.parcours_doctoral.epreuve_confirmation.repository.in_memory import (
    epreuve_confirmation,
)
from admission.infrastructure.parcours_doctoral.repository.in_memory.doctorat import DoctoratInMemoryRepository


class TestApprouverDemandeCDD(SimpleTestCase):
    def setUp(self) -> None:
        # Mock datetime to return the 2020 year as the current year
        date_patcher = patch(
            'admission.ddd.parcours_doctoral.epreuve_confirmation.domain.service.epreuve_confirmation.datetime',
        )
        mock_date = date_patcher.start()
        self.addCleanup(date_patcher.stop)
        mock_date.date.today.return_value = datetime.date(2020, 11, 1)
        self.message_bus = message_bus_in_memory_instance

    def test_should_approuver_demande_a_verifier(self):
        demande_approuvee_id = self.message_bus.invoke(ApprouverDemandeCddCommand('uuid-SC3DP'))
        demande_a_approuver_entity_id = DemandeIdentityBuilder.build_from_uuid('uuid-SC3DP')

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
        epreuves_confirmations = epreuve_confirmation.EpreuveConfirmationInMemoryRepository.search_by_doctorat_identity(
            doctorat_entity_id=doctorat_id,
        )

        self.assertEqual(len(epreuves_confirmations), 1)
        self.assertEqual(
            epreuves_confirmations[0].date_limite,
            datetime.date(2022, 11, 1),
        )
