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
from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework.test import APITestCase

from admission.ddd.admission.enums.type_bourse import TypeBourse
from admission.tests.factories.scholarship import (
    DoubleDegreeScholarshipFactory,
    ErasmusMundusScholarshipFactory,
    InternationalScholarshipFactory,
)
from base.tests.factories.user import UserFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class ScholarshipAutocompleteTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.scholarships = [
            DoubleDegreeScholarshipFactory(short_name='DDS-1', long_name='Dual degree scholarship 1'),
            DoubleDegreeScholarshipFactory(short_name='DDS-2', long_name='Dual degree scholarship 2'),
            InternationalScholarshipFactory(short_name='IS-1', long_name='International scholarship 1', disabled=True),
            InternationalScholarshipFactory(short_name='IS-1bis', long_name='International scholarship 1bis'),
            InternationalScholarshipFactory(short_name='IS-2', long_name='International scholarship 2'),
            InternationalScholarshipFactory(short_name='IS-2bis', long_name='International scholarship 2bis'),
            InternationalScholarshipFactory(short_name='AIS', long_name=''),
            ErasmusMundusScholarshipFactory(short_name='EMS-1', long_name='Erasmus Mundus scholarship 1'),
            ErasmusMundusScholarshipFactory(short_name='EMS-2', long_name='Erasmus Mundus scholarship 2'),
        ]
        cls.user = UserFactory()

    def test_autocomplete_scholarship_with_specific_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url(
                'autocomplete-scholarships',
                scholarship_type=TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name,
            ),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 4)

        self.assertEqual(
            response.json()['results'],
            [
                {
                    'uuid': str(scholarship.uuid),
                    'short_name': scholarship.short_name,
                    'long_name': scholarship.long_name,
                    'type': scholarship.type,
                }
                for scholarship in [
                    self.scholarships[6],
                    self.scholarships[3],
                    self.scholarships[4],
                    self.scholarships[5],
                ]
            ],
        )

    def test_autocomplete_scholarship_with_specific_type_and_search(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url(
                'autocomplete-scholarships',
                scholarship_type=TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name,
            ),
            format='json',
            data={
                'search': '2',
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 2)

        self.assertEqual(
            response.json()['results'],
            [
                {
                    'uuid': str(scholarship.uuid),
                    'short_name': scholarship.short_name,
                    'long_name': scholarship.long_name,
                    'type': scholarship.type,
                }
                for scholarship in [
                    self.scholarships[4],
                    self.scholarships[5],
                ]
            ],
        )
