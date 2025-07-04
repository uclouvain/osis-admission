# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import override, gettext

from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.learning_unit_year_subtypes import (
    FULL,
)
from base.models.enums.proposal_type import ProposalType
from base.tests.factories.external_learning_unit_year import (
    ExternalLearningUnitYearFactory,
)
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.user import UserFactory


class AutocompleteTestCase(TestCase):
    def test_autocomplete_learning_unit_year_and_classes(self):
        self.client.force_login(UserFactory())
        LearningUnitYearFactory(acronym="FOOBAR1", academic_year__year=2022)
        LearningUnitYearFactory(
            acronym="FOOBAR2",
            academic_year__year=2022,
            learning_container_year__container_type=LearningContainerYearType.EXTERNAL.name,
        )
        url = resolve_url('admission:autocomplete:learning-unit-years-and-classes')
        data = {'forward': '{"annee": "2022"}', 'q': 'FO'}
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 0)

        response = self.client.get(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "FOOBAR1")

    def test_autocomplete_learning_unit_year(self):
        self.client.force_login(UserFactory())
        second_learning_unit = LearningUnitYearFactory(
            acronym="FOOBAR2",
            academic_year__year=2022,
            specific_title='Informatique B',
            specific_title_english='Computer Science B',
            subtype=FULL,
        )
        second_learning_unit_proposal = ProposalLearningUnitFactory(
            learning_unit_year=second_learning_unit,
            type=ProposalType.CREATION.name,
        )
        first_learning_unit = LearningUnitYearFactory(
            acronym="FOOBAR1",
            academic_year__year=2022,
            specific_title='Informatique A',
            specific_title_english='Computer Science A',
            subtype=FULL,
        )
        ExternalLearningUnitYearFactory(
            learning_unit_year__subtype=FULL,
            learning_unit_year__acronym="FOOBAR3",
            learning_unit_year__academic_year__year=2022,
            learning_unit_year__specific_title='Informatique en mobilité',
            learning_unit_year__specific_title_english='Computer Science in mobility',
            learning_unit_year__learning_container_year__container_type=LearningContainerYearType.EXTERNAL.name,
            mobility=True,
        )
        url = resolve_url('admission:autocomplete:learning-unit-years')

        # Without data
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 0)

        # Search by acronym
        response = self.client.get(url, data={'forward': '{"year": "2022"}', 'q': 'FOOBAR1'}, format="json")
        self.assertEqual(response.status_code, 200)

        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0],
            {
                'id': first_learning_unit.acronym,
                'text': f'{first_learning_unit.acronym} - {first_learning_unit.complete_title_i18n}',
                'selected_text': f'{first_learning_unit.acronym} - {first_learning_unit.complete_title_i18n}',
                'disabled': False,
                'title': '',
            },
        )

        # Search by title and exclude the learning unit year with mobility
        response = self.client.get(url, data={'forward': '{"year": "2022"}', 'q': 'Informatique'}, format="json")
        self.assertEqual(response.status_code, 200)

        results = response.json()['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], first_learning_unit.acronym)
        self.assertEqual(results[1]['id'], second_learning_unit.acronym)

        # Search by title and return the english title
        with override(settings.LANGUAGE_CODE_EN):
            response = self.client.get(url, data={'forward': '{"year": "2022"}', 'q': 'Informatique A'}, format="json")
            self.assertEqual(response.status_code, 200)
            results = response.json()['results']
            self.assertEqual(len(results), 1)
            self.assertEqual(
                results[0],
                {
                    'id': first_learning_unit.acronym,
                    'text': f'{first_learning_unit.acronym} - {first_learning_unit.complete_title_i18n}',
                    'selected_text': f'{first_learning_unit.acronym} - {first_learning_unit.complete_title_i18n}',
                    'disabled': False,
                    'title': '',
                },
            )
            self.assertEqual(results[0]['id'], first_learning_unit.acronym)

            learning_unit_without_english_title = LearningUnitYearFactory(
                acronym="FOOBAR4",
                academic_year__year=2022,
                specific_title='Informatique D',
                specific_title_english='',
                subtype=FULL,
            )

            response = self.client.get(url, data={'forward': '{"year": "2022"}', 'q': 'FOOBAR4'}, format="json")

            self.assertEqual(response.status_code, 200)
            results = response.json()['results']
            self.assertEqual(len(results), 1)
            self.assertEqual(
                results[0],
                {
                    'id': learning_unit_without_english_title.acronym,
                    'text': f'{learning_unit_without_english_title.acronym} - '
                    f'{learning_unit_without_english_title.complete_title}',
                    'selected_text': f'{learning_unit_without_english_title.acronym} - '
                    f'{learning_unit_without_english_title.complete_title}',
                    'disabled': False,
                    'title': '',
                },
            )
            self.assertEqual(results[0]['id'], learning_unit_without_english_title.acronym)

            # Search by acronym a learning unit with a proposal (creation)
            response = self.client.get(url, data={'forward': '{"year": "2022"}', 'q': 'FOOBAR2'}, format="json")
            self.assertEqual(response.status_code, 200)

            results = response.json()['results']
            self.assertEqual(len(results), 1)
            self.assertEqual(
                results[0],
                {
                    'id': second_learning_unit.acronym,
                    'text': f'{second_learning_unit.acronym} - {second_learning_unit.complete_title_i18n}',
                    'selected_text': f'{second_learning_unit.acronym} - {second_learning_unit.complete_title_i18n}',
                    'disabled': False,
                    'title': '',
                },
            )

            # Search by acronym a learning unit with a proposal (deletion)
            second_learning_unit_proposal.type = ProposalType.SUPPRESSION.name
            second_learning_unit_proposal.save(update_fields=['type'])
            response = self.client.get(url, data={'forward': '{"year": "2022"}', 'q': 'FOOBAR2'}, format="json")
            self.assertEqual(response.status_code, 200)

            results = response.json()['results']
            icon = '<i class="far fa-file deleted-learning-unit-icon"></i>'
            self.assertEqual(len(results), 1)
            self.assertEqual(
                results[0],
                {
                    'id': second_learning_unit.acronym,
                    'text': f'{icon}{second_learning_unit.acronym} - {second_learning_unit.complete_title_i18n}',
                    'selected_text': f'{second_learning_unit.acronym} - {second_learning_unit.complete_title_i18n}',
                    'disabled': True,
                    'title': gettext('LU proposed for deletion'),
                },
            )
