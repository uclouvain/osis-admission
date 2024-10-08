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
from django.test import TestCase

from admission.ddd.admission.commands import RecupererEtudesSecondairesQuery
from admission.ddd.admission.dtos import EtudesSecondairesAdmissionDTO
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRecupererEtudesSecondaires(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def test_should_recuperer_etudes_secondaires(self):
        etudes_secondaires: EtudesSecondairesAdmissionDTO = self.message_bus.invoke(
            RecupererEtudesSecondairesQuery(
                matricule_candidat='0123456789',
            ),
        )
        self.assertIsNotNone(etudes_secondaires.diplome_belge)

    def test_should_retourner_etudes_secondaires_par_defaut_si_diplomes_non_trouves(self):
        etudes_secondaires: EtudesSecondairesAdmissionDTO = self.message_bus.invoke(
            RecupererEtudesSecondairesQuery(
                matricule_candidat='INCONNU',
            )
        )

        self.assertIsNone(etudes_secondaires.diplome_belge)
        self.assertIsNone(etudes_secondaires.diplome_etranger)
        self.assertIsNone(etudes_secondaires.alternative_secondaires)
        self.assertEqual(etudes_secondaires.valorisation.est_valorise_par_epc, False)
        self.assertEqual(etudes_secondaires.valorisation.types_formations_admissions_valorisees, [])
