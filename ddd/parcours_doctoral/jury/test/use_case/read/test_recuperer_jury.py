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
import datetime

from django.test import TestCase

from admission.ddd.parcours_doctoral.jury.commands import RecupererJuryQuery
from admission.ddd.parcours_doctoral.jury.dtos.jury import JuryDTO
from admission.ddd.parcours_doctoral.jury.validator.exceptions import JuryNonTrouveException
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRecupererJury(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def test_should_pas_trouver_si_jury_inconnu(self):
        with self.assertRaises(JuryNonTrouveException):
            self.message_bus.invoke(
                RecupererJuryQuery(
                    uuid_jury='inconnu',
                )
            )

    def test_should_recuperer_jury_connu(self):
        jury_dto: JuryDTO = self.message_bus.invoke(
            RecupererJuryQuery(
                uuid_jury='uuid-jury',
            )
        )
        self.assertEqual(jury_dto.uuid, 'uuid-jury')
        self.assertEqual(jury_dto.titre_propose, 'titre_propose')
        self.assertIs(jury_dto.cotutelle, False)
        self.assertEqual(jury_dto.institution_cotutelle, '')
        self.assertEqual(len(jury_dto.membres), 2)
        self.assertEqual(jury_dto.formule_defense, 'DEUX_TEMPS')
        self.assertEqual(jury_dto.date_indicative, datetime.date(2022, 1, 1))
        self.assertEqual(jury_dto.langue_redaction, 'english')
        self.assertEqual(jury_dto.langue_soutenance, 'english')
        self.assertEqual(jury_dto.commentaire, '')
        self.assertIsNone(jury_dto.situation_comptable)
        self.assertIsNone(jury_dto.approbation_pdf)
