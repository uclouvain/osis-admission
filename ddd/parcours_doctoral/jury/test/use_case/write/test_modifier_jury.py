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

from admission.ddd.admission.doctorat.preparation.test.factory.groupe_de_supervision import (
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtCotutelleFactory,
)
from admission.ddd.parcours_doctoral.jury.commands import ModifierJuryCommand
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.parcours_doctoral.jury.repository.in_memory.jury import JuryInMemoryRepository


class TestModifierJury(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance
        GroupeDeSupervisionInMemoryRepository.entities.append(
            GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtCotutelleFactory(proposition_id__uuid='uuid-jury')
        )

    def tearDown(self) -> None:
        GroupeDeSupervisionInMemoryRepository.reset()
        JuryInMemoryRepository.reset()

    def test_should_modifier_jury(self):
        self.message_bus.invoke(
            ModifierJuryCommand(
                uuid_doctorat='uuid-jury',
                titre_propose='autre_titre',
                formule_defense='UN_JOUR',
                date_indicative=datetime.date(2022, 6, 1),
                langue_redaction='french',
                langue_soutenance='french',
                commentaire='commentaire',
            )
        )

        self.assertEqual(len(JuryInMemoryRepository.entities), 1)
        jury = JuryInMemoryRepository.entities[0]
        self.assertEqual(jury.entity_id.uuid, 'uuid-jury')
        self.assertEqual(jury.titre_propose, 'autre_titre')
        self.assertIs(jury.cotutelle, True)
        self.assertEqual(jury.institution_cotutelle, 'MIT')
        self.assertEqual(len(jury.membres), 2)
        self.assertEqual(jury.formule_defense, 'UN_JOUR')
        self.assertEqual(jury.date_indicative, datetime.date(2022, 6, 1))
        self.assertEqual(jury.langue_redaction, 'french')
        self.assertEqual(jury.langue_soutenance, 'french')
        self.assertEqual(jury.commentaire, 'commentaire')
        self.assertIs(jury.situation_comptable, None)
        self.assertEqual(jury.approbation_pdf, [])
