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
import datetime

from django.test import TestCase
from django.utils.translation import gettext as _

from admission.forms.doctorate.cdd.confirmation import ConfirmationForm, ConfirmationRetakingForm


class ConfirmationTestCase(TestCase):
    def test_form_validation_with_no_data(self):
        form = ConfirmationForm(data={})

        self.assertFalse(form.is_valid())

        # Mandatory fields
        self.assertIn('date_limite', form.errors)
        self.assertIn('date', form.errors)

    def test_form_validation_with_valid_dates(self):
        form = ConfirmationForm(
            data={
                'date_limite': datetime.date(2022, 1, 4),
                'date': datetime.date(2022, 1, 3),
            },
        )
        self.assertTrue(form.is_valid())

    def test_form_validation_with_invalid_dates(self):
        form = ConfirmationForm(
            data={
                'date_limite': datetime.date(2022, 1, 4),
                'date': datetime.date(2022, 1, 5),
            },
        )
        self.assertFalse(form.is_valid())
        non_fields_errors = form.non_field_errors()
        self.assertEqual(len(non_fields_errors), 1)
        self.assertEqual(
            non_fields_errors[0],
            _('The date of the confirmation paper cannot be later than its deadline.'),
        )


class ConfirmationRetakingFormTestCase(TestCase):
    def test_form_validation_with_no_data(self):
        form = ConfirmationRetakingForm(
            data={},
        )

        self.assertFalse(form.is_valid())

        # Mandatory fields
        self.assertIn('subject', form.errors)
        self.assertIn('body', form.errors)
        self.assertIn('date_limite', form.errors)

    def test_form_validation_with_valid_data(self):
        form = ConfirmationRetakingForm(
            data={
                'subject': 'The subject',
                'body': 'The content of the message',
                'date_limite': datetime.date(2022, 5, 1),
            },
        )

        self.assertTrue(form.is_valid())
