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
from django.test import SimpleTestCase

from admission.ddd.projet_doctoral.doctorat.formation.commands import SoumettreActivitesCommand
from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import CategorieActivite, StatutActivite
from admission.ddd.projet_doctoral.doctorat.formation.test.factory.activite import ActiviteFactory
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.projet_doctoral.doctorat.formation.repository.in_memory.activite import (
    ActiviteInMemoryRepository,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class SoumettreActivitesTestCase(SimpleTestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def test_soumettre_activites_vides(self):
        ActiviteInMemoryRepository.entities = [ActiviteFactory(ects=0) for _ in range(len(CategorieActivite.choices()))]
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(
                SoumettreActivitesCommand(
                    activite_uuids=[activite.entity_id.uuid for activite in ActiviteInMemoryRepository.entities]
                )
            )
        self.assertEqual(len(e.exception.exceptions), len(ActiviteInMemoryRepository.entities))
        ActiviteInMemoryRepository.reset()

    def test_soumettre_sous_activites_vides(self):
        ActiviteInMemoryRepository.entities = [
            ActiviteFactory(
                categorie=CategorieActivite.COMMUNICATION,
                generate_dto__date=None,
                generate_dto__class='SeminarCommunicationDTOFactory',
            ),
            ActiviteFactory(
                ects=0,
                categorie=CategorieActivite.COMMUNICATION,
                generate_dto__class='ResidencyCommunicationDTOFactory',
            ),
            ActiviteFactory(
                ects=0,
                categorie=CategorieActivite.COMMUNICATION,
                generate_dto__class='ConferenceCommunicationDTOFactory',
            ),
            ActiviteFactory(
                ects=0,
                categorie=CategorieActivite.PUBLICATION,
                generate_dto__class='ConferencePublicationDTOFactory',
            ),
        ]
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(
                SoumettreActivitesCommand(
                    activite_uuids=[activite.entity_id.uuid for activite in ActiviteInMemoryRepository.entities]
                )
            )
        self.assertEqual(len(e.exception.exceptions), len(ActiviteInMemoryRepository.entities))
        ActiviteInMemoryRepository.reset()

    def test_soumettre_activites_ok(self):
        self.message_bus.invoke(
            SoumettreActivitesCommand(
                activite_uuids=[activite.entity_id.uuid for activite in ActiviteInMemoryRepository.entities]
            )
        )
        self.assertEqual(ActiviteInMemoryRepository.entities[0].statut, StatutActivite.SOUMISE)

    def test_soumettre_sous_activites_ok(self):
        parent_service = ActiviteFactory(
            categorie=CategorieActivite.SEMINAR,
            generate_dto__class='SeminarDTOFactory',
        )
        ActiviteInMemoryRepository.entities = [
            parent_service,
            ActiviteFactory(
                parent_id=parent_service.entity_id,
                categorie=CategorieActivite.COMMUNICATION,
                generate_dto__class='SeminarCommunicationDTOFactory',
            ),
            ActiviteFactory(
                categorie=CategorieActivite.COMMUNICATION,
                generate_dto__class='ResidencyCommunicationDTOFactory',
            ),
            ActiviteFactory(
                categorie=CategorieActivite.COMMUNICATION,
                generate_dto__class='ConferenceCommunicationDTOFactory',
            ),
            ActiviteFactory(
                categorie=CategorieActivite.PUBLICATION,
                generate_dto__class='ConferencePublicationDTOFactory',
            ),
        ]
        self.message_bus.invoke(
            SoumettreActivitesCommand(
                activite_uuids=[activite.entity_id.uuid for activite in ActiviteInMemoryRepository.entities]
            )
        )
        self.assertEqual(ActiviteInMemoryRepository.entities[0].statut, StatutActivite.SOUMISE)
        ActiviteInMemoryRepository.reset()
