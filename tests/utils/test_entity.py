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
from django.test import TransactionTestCase

from admission.admission_utils.entity import get_faculty_id_from_entity_id
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import MainEntityVersionFactory, EntityVersionFactory


class EntityTestCase(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        cls.main_entity = MainEntityVersionFactory().entity

        cls.fac_1_entity = EntityVersionFactory(
            parent=cls.main_entity,
            entity_type=EntityType.FACULTY.name,
        ).entity

        cls.fac_2_entity = EntityVersionFactory(
            parent=cls.main_entity,
            entity_type=EntityType.FACULTY.name,
        ).entity

        cls.main_school_entity = EntityVersionFactory(
            parent=cls.main_entity,
            entity_type=EntityType.SCHOOL.name,
        ).entity

        cls.fac_1_school_1_entity = EntityVersionFactory(
            parent=cls.fac_1_entity,
            entity_type=EntityType.SCHOOL.name,
        ).entity

        cls.fac_2_school_1_entity = EntityVersionFactory(
            parent=cls.fac_2_entity,
            entity_type=EntityType.SCHOOL.name,
        ).entity

        cls.main_cdd_entity = EntityVersionFactory(
            parent=cls.main_school_entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        ).entity

        cls.fac_1_school_1_cdd_1_entity = EntityVersionFactory(
            parent=cls.fac_1_school_1_entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        ).entity

        cls.fac_2_school_1_cdd_1_entity = EntityVersionFactory(
            parent=cls.fac_2_school_1_entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        ).entity

    def test_get_faculty_id_from_entity_id(self):
        self.assertEqual(
            get_faculty_id_from_entity_id(entity_id=self.main_entity.id),
            None,
        )
        self.assertEqual(
            get_faculty_id_from_entity_id(entity_id=self.fac_1_entity.id),
            self.fac_1_entity.id,
        )
        self.assertEqual(
            get_faculty_id_from_entity_id(entity_id=self.fac_2_entity.id),
            self.fac_2_entity.id,
        )
        self.assertEqual(
            get_faculty_id_from_entity_id(entity_id=self.main_school_entity.id),
            None,
        )
        self.assertEqual(
            get_faculty_id_from_entity_id(entity_id=self.fac_1_school_1_entity.id),
            self.fac_1_entity.id,
        )
        self.assertEqual(
            get_faculty_id_from_entity_id(entity_id=self.fac_2_school_1_entity.id),
            self.fac_2_entity.id,
        )

        self.assertEqual(
            get_faculty_id_from_entity_id(entity_id=self.main_cdd_entity.id),
            None,
        )
        self.assertEqual(
            get_faculty_id_from_entity_id(entity_id=self.fac_1_school_1_cdd_1_entity.id),
            self.fac_1_entity.id,
        )
        self.assertEqual(
            get_faculty_id_from_entity_id(entity_id=self.fac_2_school_1_cdd_1_entity.id),
            self.fac_2_entity.id,
        )
