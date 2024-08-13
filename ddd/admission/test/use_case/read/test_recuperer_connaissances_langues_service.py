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
from typing import List
from unittest import TestCase

from admission.ddd.admission.commands import RecupererConnaissancesLanguesQuery
from admission.ddd.admission.doctorat.preparation.dtos import ConnaissanceLangueDTO
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRecupererConnaissancesLangues(TestCase):
    def test_should_recuperer_connaissances_langues(self):
        connaissances_langues: List[ConnaissanceLangueDTO] = message_bus_in_memory_instance.invoke(
            RecupererConnaissancesLanguesQuery(
                matricule_candidat='0123456789',
            ),
        )

        self.assertEqual(len(connaissances_langues), 3)

        self.assertEqual(connaissances_langues[0].langue, 'FR')
        self.assertEqual(connaissances_langues[0].nom_langue_en, 'Français')
        self.assertEqual(connaissances_langues[0].nom_langue_fr, 'Français')
        self.assertEqual(connaissances_langues[0].capacite_ecriture, 'C2')
        self.assertEqual(connaissances_langues[0].capacite_orale, 'C2')
        self.assertEqual(connaissances_langues[0].comprehension_orale, 'C2')
        self.assertEqual(connaissances_langues[0].certificat, [])

        self.assertEqual(connaissances_langues[1].langue, 'EN')
        self.assertEqual(connaissances_langues[1].nom_langue_en, 'Anglais')
        self.assertEqual(connaissances_langues[1].nom_langue_fr, 'Anglais')
        self.assertEqual(connaissances_langues[1].capacite_ecriture, 'B2')
        self.assertEqual(connaissances_langues[1].capacite_orale, 'B2')
        self.assertEqual(connaissances_langues[1].comprehension_orale, 'B2')
        self.assertEqual(connaissances_langues[1].certificat, [])

        self.assertEqual(connaissances_langues[2].langue, 'NL')
        self.assertEqual(connaissances_langues[2].nom_langue_en, 'Néerlandais')
        self.assertEqual(connaissances_langues[2].nom_langue_fr, 'Néerlandais')
        self.assertEqual(connaissances_langues[2].capacite_ecriture, 'B2')
        self.assertEqual(connaissances_langues[2].capacite_orale, 'B2')
        self.assertEqual(connaissances_langues[2].comprehension_orale, 'B2')
        self.assertEqual(connaissances_langues[2].certificat, [])

    def test_should_retourner_liste_vide_si_candidat_inconnu(self):
        connaissances_langues: List[ConnaissanceLangueDTO] = message_bus_in_memory_instance.invoke(
            RecupererConnaissancesLanguesQuery(
                matricule_candidat='INCONNU',
            )
        )

        self.assertEqual(len(connaissances_langues), 0)
