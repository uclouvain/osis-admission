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

from django.test import SimpleTestCase

from admission.ddd.admission.formation_continue.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_continue.commands import RecupererPropositionQuery
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class RecupererPropositionServiceTestCase(SimpleTestCase):
    def setUp(self):
        self.cmd = RecupererPropositionQuery(uuid_proposition='uuid-USCC4')
        self.message_bus = message_bus_in_memory_instance

    def test_get_proposition(self):
        result = self.message_bus.invoke(self.cmd)
        self.assertEqual(result.formation.sigle, 'USCC4')
        self.assertEqual(result.formation.annee, 2020)
        self.assertEqual(result.formation.intitule, 'Formation USCC4')
        self.assertEqual(result.formation.campus, 'Louvain-La-Neuve')
        self.assertEqual(result.statut, ChoixStatutPropositionContinue.EN_BROUILLON.name)
        self.assertEqual(result.matricule_candidat, '0123456789')
        self.assertEqual(result.prenom_candidat, 'Jean')
        self.assertEqual(result.nom_candidat, 'Dupont')

    def test_get_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(RecupererPropositionQuery(uuid_proposition='inexistant'))
