# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.test import TestCase

from admission.infrastructure.admission.formation_generale.domain.service.pdf_generation import ENTITY_UCL
from admission.infrastructure.utils import get_entities_with_descendants_ids
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory, MainEntityVersionFactory


class EntitiesComputationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ucl_entity = MainEntityVersionFactory(acronym=ENTITY_UCL, entity_type='')

        cls.faculty_a_entity = EntityVersionFactory(parent=cls.ucl_entity.entity, entity_type=EntityType.FACULTY.name)
        cls.faculty_b_entity = EntityVersionFactory(parent=cls.ucl_entity.entity, entity_type=EntityType.FACULTY.name)
        cls.faculty_c_entity = EntityVersionFactory(parent=cls.ucl_entity.entity, entity_type=EntityType.FACULTY.name)

        cls.logistics_a_entity = EntityVersionFactory(
            parent=cls.faculty_a_entity.entity,
            entity_type=EntityType.LOGISTICS_ENTITY.name,
        )
        cls.first_school_a_entity = EntityVersionFactory(
            parent=cls.faculty_a_entity.entity,
            entity_type=EntityType.SCHOOL.name,
        )
        cls.second_school_a_entity = EntityVersionFactory(
            parent=cls.faculty_a_entity.entity,
            entity_type=EntityType.SCHOOL.name,
        )

        cls.first_school_b_entity = EntityVersionFactory(
            parent=cls.faculty_b_entity.entity,
            entity_type=EntityType.SCHOOL.name,
        )

    def test_get_entities_with_descendants_ids_with_no_input_acronym(self):
        entities = get_entities_with_descendants_ids(entities_acronyms=[])
        self.assertEqual(len(entities), 0)

    def test_get_entities_with_descendants_ids_with_no_pedagogical_acronym(self):
        entities = get_entities_with_descendants_ids(entities_acronyms=[self.ucl_entity.acronym])
        self.assertEqual(len(entities), 0)

        entities = get_entities_with_descendants_ids(entities_acronyms=[self.logistics_a_entity.acronym])
        self.assertEqual(len(entities), 0)

    def test_get_entities_with_descendants_ids_with_faculty_acronyms(self):
        entities = get_entities_with_descendants_ids(entities_acronyms=[self.faculty_a_entity.acronym])
        self.assertCountEqual(
            entities,
            [
                self.faculty_a_entity.entity.id,
                self.first_school_a_entity.entity.id,
                self.second_school_a_entity.entity.id,
                self.logistics_a_entity.entity.id,
            ],
        )

    def test_get_entities_with_descendants_ids_with_school_acronyms(self):
        entities = get_entities_with_descendants_ids(entities_acronyms=[self.first_school_a_entity.acronym])
        self.assertCountEqual(
            entities,
            [
                self.first_school_a_entity.entity.id,
            ],
        )

    def test_get_entities_with_descendants_ids_with_school_and_faculty_acronyms(self):
        entities = get_entities_with_descendants_ids(
            entities_acronyms=[self.first_school_b_entity.acronym, self.faculty_b_entity.acronym],
        )

        self.assertCountEqual(entities, [self.first_school_b_entity.entity.id, self.faculty_b_entity.entity.id])
