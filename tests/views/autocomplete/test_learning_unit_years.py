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
from django.shortcuts import resolve_url
from django.test import TestCase

from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.user import UserFactory


class AutocompleteTestCase(TestCase):
    def test_autocomplete_learning_unit_year(self):
        self.client.force_login(UserFactory())
        LearningUnitYearFactory(acronym="FOOBAR1", academic_year__year=2022)
        LearningUnitYearFactory(
            acronym="FOOBAR2",
            academic_year__year=2022,
            learning_container_year__container_type=LearningContainerYearType.EXTERNAL.name,
        )
        url = resolve_url('admission:autocomplete:learning_unit_years')
        data = {'forward': '{"annee": "2022"}', 'q': 'FO'}
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 0)

        response = self.client.get(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "FOOBAR1")
