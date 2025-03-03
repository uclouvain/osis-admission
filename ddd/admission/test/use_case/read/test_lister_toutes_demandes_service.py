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

from admission.ddd.admission.commands import ListerToutesDemandesQuery
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository as PropositionDoctoraleInMemoryRepository,
)
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository as PropositionContinueInMemoryRepository,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository as PropositionGeneraleInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)


class TestListerToutesDemandes(TestCase):
    def setUp(self) -> None:
        self.cmd = ListerToutesDemandesQuery(matricule_candidat='0123456789')
        self.message_bus = message_bus_in_memory_instance
        PropositionGeneraleInMemoryRepository.reset()
        PropositionContinueInMemoryRepository.reset()
        PropositionDoctoraleInMemoryRepository.reset()

    def test_should_rechercher_par_matricule(self):
        propositions = self.message_bus.invoke(self.cmd)
        self.assertEqual(len(propositions), 20)
        for proposition in propositions:
            self.assertEqual(proposition.noma_candidat, '0123456789')
