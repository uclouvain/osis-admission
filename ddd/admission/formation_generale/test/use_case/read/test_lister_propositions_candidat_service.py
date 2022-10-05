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
from typing import List

from django.test import SimpleTestCase

from admission.ddd.admission.enums.type_bourse import TypeBourse
from admission.ddd.admission.formation_generale.commands import ListerPropositionsCandidatQuery
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutProposition
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestListerPropositionsCandidatService(SimpleTestCase):
    def setUp(self) -> None:
        self.cmd = ListerPropositionsCandidatQuery(matricule_candidat='0123456789')
        self.message_bus = message_bus_in_memory_instance

    def test_should_rechercher_par_matricule(self):
        results: List[PropositionDTO] = self.message_bus.invoke(self.cmd)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].formation.sigle, 'SC3DP')
        self.assertEqual(results[0].formation.annee, 2020)
        self.assertEqual(results[0].formation.intitule, 'Doctorat en sciences')
        self.assertEqual(results[0].formation.campus, 'Louvain-la-Neuve')
        self.assertEqual(results[0].statut, ChoixStatutProposition.IN_PROGRESS.name)
        self.assertEqual(results[0].matricule_candidat, '0123456789')
        self.assertEqual(results[0].prenom_candidat, 'Jean')
        self.assertEqual(results[0].nom_candidat, 'Dupont')
        self.assertEqual(
            results[0].bourse_internationale.type,
            TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name,
        )
        self.assertEqual(results[0].bourse_internationale.nom_court, 'AFEPA')
        self.assertEqual(results[0].bourse_internationale.nom_long, 'AFEPA --')
        self.assertEqual(results[0].bourse_erasmus_mundus.type, TypeBourse.ERASMUS_MUNDUS.name)
        self.assertEqual(results[0].bourse_erasmus_mundus.nom_court, 'EMDI')
        self.assertEqual(results[0].bourse_erasmus_mundus.nom_long, 'EMDI --')
        self.assertEqual(results[0].bourse_double_diplome.type, TypeBourse.DOUBLE_TRIPLE_DIPLOMATION.name)
        self.assertEqual(results[0].bourse_double_diplome.nom_court, 'AGRO DD UCLOUVAIN/GEM')
        self.assertEqual(results[0].bourse_double_diplome.nom_long, 'AGRO DD UCLOUVAIN/GEM --')
