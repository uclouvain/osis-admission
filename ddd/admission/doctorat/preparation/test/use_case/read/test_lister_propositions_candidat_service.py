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
    ListerPropositionsCandidatQuery,
)
from admission.ddd.admission.doctorat.preparation.test.factory.person import (
    PersonneConnueUclDTOFactory,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)


class TestListerPropositionsCandidatService(TestCase):
    def setUp(self) -> None:
        PersonneConnueUclInMemoryTranslator.personnes_connues_ucl = {
            PersonneConnueUclDTOFactory(matricule='0123456789'),
        }
        self.cmd = ListerPropositionsCandidatQuery(matricule_candidat='0123456789')
        self.message_bus = message_bus_in_memory_instance

    def test_should_rechercher_par_matricule(self):
        results = self.message_bus.invoke(self.cmd)
        self.assertIn('uuid-ECGE3DP', [r.uuid for r in results])
