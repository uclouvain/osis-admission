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
import freezegun
from django import forms
from django.test import SimpleTestCase

from admission.forms import get_year_choices, AdmissionHTMLCharField


@freezegun.freeze_time('2020-01-01')
class GetYearChoicesTestCase(SimpleTestCase):
    def test_get_year_choices_by_specifying_only_the_min_year(self):
        choices = get_year_choices(min_year=2018)

        self.assertEqual(len(choices), 4)
        self.assertEqual(
            choices,
            [
                ('', ' - '),
                (2020, 2020),
                (2019, 2019),
                (2018, 2018),
            ],
        )

    def test_get_year_choices_by_specifying_a_max_year(self):
        choices = get_year_choices(min_year=2018, max_year=2021)

        self.assertEqual(len(choices), 5)
        self.assertEqual(
            choices,
            [
                ('', ' - '),
                (2021, 2021),
                (2020, 2020),
                (2019, 2019),
                (2018, 2018),
            ],
        )

    def test_get_year_choices_with_custom_empty_label(self):
        choices = get_year_choices(min_year=2020, empty_label='My custom label')

        self.assertEqual(len(choices), 2)
        self.assertEqual(
            choices,
            [
                ('', 'My custom label'),
                (2020, 2020),
            ],
        )

    def test_get_year_choices_with_full_format(self):
        choices = get_year_choices(min_year=2020, full_format=True)

        self.assertEqual(len(choices), 2)
        self.assertEqual(
            choices,
            [
                ('', ' - '),
                ('2020-2021', '2020-2021'),
            ],
        )


class AdmissionHTMLCharFieldTestCase(SimpleTestCase):
    class CustomForm(forms.Form):
        html_field = AdmissionHTMLCharField(required=False)
        char_field = forms.CharField(required=False)

    def test_html_char_field_with_accent(self):
        form = self.CustomForm(
            data={
                'html_field': '<p>test with accent &egrave;</p>',
                'char_field': '<p>test with accent &egrave;</p>',
            },
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['html_field'], '<p>test with accent è</p>')
        self.assertEqual(form.cleaned_data['char_field'], '<p>test with accent &egrave;</p>')

    def test_html_char_field_without_accent(self):
        form = self.CustomForm(
            data={
                'html_field': '<p>test without accent e</p>',
                'char_field': '<p>test without accent e</p>',
            },
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['html_field'], '<p>test without accent e</p>')
        self.assertEqual(form.cleaned_data['char_field'], '<p>test without accent e</p>')

    def test_html_char_field_without_value(self):
        form = self.CustomForm(data={})

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['html_field'], '')
        self.assertEqual(form.cleaned_data['char_field'], '')
