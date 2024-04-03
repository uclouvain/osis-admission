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

from django.test import SimpleTestCase

from admission.ddd.admission.shared_kernel.email_destinataire.domain.validator.exceptions import \
    InformationsDestinatairePasTrouvee
from admission.ddd.admission.shared_kernel.email_destinataire.dtos.destinataire import InformationsDestinataireDTO
from admission.ddd.admission.shared_kernel.email_destinataire.queries import RecupererInformationsDestinataireQuery
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRecupererInformationsDestinataireService(SimpleTestCase):
    def setUp(self) -> None:
        self.annee = 2022
        self.sigle_formation = 'DROI1BA'
        self.est_en_premiere_annee = False

        self.message_bus = message_bus_in_memory_instance

    def test_doit_retourner_informations_destinataire(self):
        cmd = RecupererInformationsDestinataireQuery(
            annee=self.annee,
            sigle_formation=self.sigle_formation,
            est_premiere_annee=self.est_en_premiere_annee,
        )
        result = self.message_bus.invoke(cmd)
        expected_result = InformationsDestinataireDTO(
            annee=self.annee,
            sigle_formation=self.sigle_formation,
            pour_premiere_annee=self.est_en_premiere_annee,
            email='test@test.be',
            en_tete='Prénom nom',
        )

        self.assertEqual(result, expected_result)

    def test_doit_raise_exception_si_pas_trouvee(self):
        cmd = RecupererInformationsDestinataireQuery(
            annee=self.annee,
            sigle_formation='FAKE',
            est_premiere_annee=self.est_en_premiere_annee,
        )
        with self.assertRaises(InformationsDestinatairePasTrouvee):
            self.message_bus.invoke(cmd)
