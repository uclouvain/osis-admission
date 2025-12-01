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
import datetime

import freezegun
from django.test import SimpleTestCase

from admission.ddd.admission.formation_generale.commands import (
    RedonnerMainAuGestionnaireLorsDeLaReclamationDocumentsCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import (
    DocumentsReclamesException,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.shared_kernel.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
    AcademicYearIdentity,
)
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import (
    AcademicYearInMemoryRepository,
)


@freezegun.freeze_time("2023-01-03")
class RedonnerMainAuGestionnaireLorsDeLaReclamationDocumentsTestCase(SimpleTestCase):
    def setUp(self) -> None:
        self.emplacements_document_repository = emplacement_document_in_memory_repository
        self.proposition_repository = PropositionInMemoryRepository()
        self.message_bus = message_bus_in_memory_instance
        self.addCleanup(self.proposition_repository.reset)
        self.addCleanup(self.emplacements_document_repository.reset)

        self.proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-MASTER-SCI'))
        self.cmd = RedonnerMainAuGestionnaireLorsDeLaReclamationDocumentsCommand(
            uuid_proposition=self.proposition.entity_id.uuid,
        )

        academic_year_repository = AcademicYearInMemoryRepository()
        for annee in range(2016, 2023):
            academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

    def test_should_lever_exception_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                RedonnerMainAuGestionnaireLorsDeLaReclamationDocumentsCommand(uuid_proposition='INCONNUE')
            )

    def test_should_lever_exception_si_document_encore_reclame(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)
            exception = context.exception.exceptions.pop()
            self.assertIsInstance(exception, DocumentsReclamesException)

    def test_should_redonner_main_au_gestionnaire_fac(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC
        self.proposition.documents_demandes = {}

        resultat = self.message_bus.invoke(self.cmd)

        # Le statut de la proposition a changé et la date d'échéance de réclamation est réinitialisée
        proposition_a_jour = self.proposition_repository.get(entity_id=self.proposition.entity_id)

        self.assertEqual(resultat, proposition_a_jour.entity_id)
        self.assertEqual(proposition_a_jour.statut, ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC)
        self.assertIsNone(proposition_a_jour.echeance_demande_documents)

    def test_should_redonner_main_au_gestionnaire_sic(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC
        self.proposition.documents_demandes = {}

        resultat = self.message_bus.invoke(self.cmd)

        # Le statut de la proposition a changé et la date d'échéance de réclamation est réinitialisée
        proposition_a_jour = self.proposition_repository.get(entity_id=self.proposition.entity_id)

        self.assertEqual(resultat, proposition_a_jour.entity_id)
        self.assertEqual(proposition_a_jour.statut, ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC)
        self.assertIsNone(proposition_a_jour.echeance_demande_documents)
