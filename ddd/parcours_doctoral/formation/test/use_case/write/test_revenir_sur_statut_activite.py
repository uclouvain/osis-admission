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

from admission.ddd.parcours_doctoral.formation.commands import RevenirSurStatutActiviteCommand
from admission.ddd.parcours_doctoral.formation.domain.model.enums import CategorieActivite, StatutActivite
from admission.ddd.parcours_doctoral.formation.domain.validator.exceptions import (
    ActiviteDoitEtreAccepteeOuRefusee,
)
from admission.ddd.parcours_doctoral.formation.test.factory.activite import ActiviteFactory
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.parcours_doctoral.formation.repository.in_memory.activite import (
    ActiviteInMemoryRepository,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class RevenirSurStatutActiviteTestCase(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance
        self.activite = ActiviteFactory(
            categorie=CategorieActivite.COMMUNICATION,
            statut=StatutActivite.REFUSEE,
        )
        self.seminaire = ActiviteFactory(
            categorie=CategorieActivite.SEMINAR,
            statut=StatutActivite.ACCEPTEE,
        )
        self.sous_activite = ActiviteFactory(
            categorie=CategorieActivite.COMMUNICATION,
            statut=StatutActivite.ACCEPTEE,
            parent_id=self.seminaire.entity_id,
        )
        ActiviteInMemoryRepository.entities = [self.activite, self.seminaire, self.sous_activite]

    def tearDown(self) -> None:
        ActiviteInMemoryRepository.reset()

    def test_revenir_sur_activite_soumise(self):
        activite = ActiviteFactory(
            categorie=CategorieActivite.COMMUNICATION,
            statut=StatutActivite.SOUMISE,
        )
        ActiviteInMemoryRepository.entities = [activite]
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(RevenirSurStatutActiviteCommand(activite_uuid=activite.entity_id.uuid))
        self.assertIsInstance(e.exception.exceptions.pop(), ActiviteDoitEtreAccepteeOuRefusee)

    def test_revenir_sur_activite(self):
        self.message_bus.invoke(RevenirSurStatutActiviteCommand(activite_uuid=self.activite.entity_id.uuid))
        self.assertEqual(ActiviteInMemoryRepository.get(self.activite.entity_id).statut, StatutActivite.SOUMISE)

    def test_revenir_sur_seminaire_et_sous_activites(self):
        self.message_bus.invoke(RevenirSurStatutActiviteCommand(activite_uuid=self.seminaire.entity_id.uuid))
        self.assertEqual(ActiviteInMemoryRepository.get(self.seminaire.entity_id).statut, StatutActivite.SOUMISE)
        self.assertEqual(ActiviteInMemoryRepository.get(self.sous_activite.entity_id).statut, StatutActivite.SOUMISE)
