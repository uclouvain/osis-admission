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

from django.test import TestCase

from admission.ddd.admission.formation_continue.commands import GetComptabiliteQuery
from admission.ddd.admission.formation_continue.dtos import ComptabiliteDTO
from admission.ddd.admission.enums import ChoixTypeCompteBancaire
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class GetComptabiliteTestCase(TestCase):
    def setUp(self):
        self.message_bus = message_bus_in_memory_instance
        self.cmd = GetComptabiliteQuery(uuid_proposition='uuid-SC3DP')

    def test_get_comptabilite(self):
        result = self.message_bus.invoke(self.cmd)
        self.assertEqual(
            result,
            ComptabiliteDTO(
                etudiant_solidaire=False,
                type_numero_compte=ChoixTypeCompteBancaire.NON.name,
                numero_compte_iban='BE43068999999501',
                iban_valide=True,
                numero_compte_autre_format='123456',
                code_bic_swift_banque='GKCCBEBB',
                prenom_titulaire_compte='John',
                nom_titulaire_compte='Doe',
            ),
        )
