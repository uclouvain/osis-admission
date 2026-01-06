# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.formation_generale.test.factory.titre_acces import TitreAccesSelectionnableFactory
from admission.ddd.admission.shared_kernel.commands import (
    SpecifierExperienceEnTantQueTitreAccesCommand,
)
from admission.ddd.admission.shared_kernel.domain.model.enums.condition_acces import TypeTitreAccesSelectionnable
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import (
    TitresAccesEtreExperiencesNonAcademiquesOuUneExperienceAcademiqueException,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.shared_kernel.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestSpecifierExperienceEnTantQueTitreAcces(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.titre_acces_repository = TitreAccesSelectionnableInMemoryRepositoryFactory()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance

        self.uuid_proposition = 'uuid-MASTER-SCI-CONFIRMED'

    def test_should_specifier_experience_en_tant_que_titre_acces(self):
        titre_acces_id = self.message_bus.invoke(
            SpecifierExperienceEnTantQueTitreAccesCommand(
                uuid_proposition=self.uuid_proposition,
                uuid_experience='uuid-EXP-1',
                type_experience=TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name,
                selectionne=True,
            )
        )
        titre_acces = self.titre_acces_repository.get(titre_acces_id)

        self.assertEqual(titre_acces.selectionne, True)
        self.assertEqual(titre_acces.annee, None)
        self.assertEqual(titre_acces.entity_id.type_titre, TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE)
        self.assertEqual(titre_acces.entity_id.uuid_experience, 'uuid-EXP-1')
        self.assertEqual(titre_acces.entity_id.uuid_proposition, self.uuid_proposition)

    def test_should_lever_exception_si_selection_experience_academique_et_deja_titre_acces_selectionne(self):
        self.titre_acces_repository.entities.append(
            TitreAccesSelectionnableFactory(
                entity_id__uuid_proposition=self.uuid_proposition,
                entity_id__type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE,
                selectionne=True,
            ),
        )

        for type_experience in [
            TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE,
            TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES,
            TypeTitreAccesSelectionnable.EXAMENS,
            TypeTitreAccesSelectionnable.EXPERIENCE_PARCOURS_INTERNE,
        ]:
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(
                    SpecifierExperienceEnTantQueTitreAccesCommand(
                        uuid_proposition=self.uuid_proposition,
                        uuid_experience='uuid-EXP-2',
                        type_experience=type_experience.name,
                        selectionne=True,
                    )
                )

            self.assertIsInstance(
                context.exception.exceptions.pop(),
                TitresAccesEtreExperiencesNonAcademiquesOuUneExperienceAcademiqueException,
            )

    def test_should_lever_exception_si_selection_experience_non_academique_et_exp_academique_deja_selectionnee(self):
        self.titre_acces_repository.entities.append(
            TitreAccesSelectionnableFactory(
                entity_id__uuid_proposition=self.uuid_proposition,
                entity_id__type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE,
                selectionne=True,
            ),
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                SpecifierExperienceEnTantQueTitreAccesCommand(
                    uuid_proposition=self.uuid_proposition,
                    uuid_experience='uuid-EXP-2',
                    type_experience=TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE.name,
                    selectionne=True,
                )
            )

        self.assertIsInstance(
            context.exception.exceptions.pop(),
            TitresAccesEtreExperiencesNonAcademiquesOuUneExperienceAcademiqueException,
        )
