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
from django.conf import settings
from django.forms import forms
from django.test import SimpleTestCase

from admission.forms.translation_field import TranslatedValueField


class FormWithTranslatedValueField(forms.Form):
    translated_value = TranslatedValueField(required=False, require_all_fields=False)


class TranslatedValueFieldTestCase(SimpleTestCase):
    def test_init_form_without_initial_value(self):
        form = FormWithTranslatedValueField()
        self.assertRegex(form.as_p(), r'<textarea.*></textarea>.*<textarea.*></textarea>')

    def test_init_form_with_initial_value(self):
        form = FormWithTranslatedValueField(
            initial={
                'translated_value': {
                    settings.LANGUAGE_CODE_EN: 'My text',
                    settings.LANGUAGE_CODE_FR: 'Mon texte',
                }
            }
        )
        self.assertRegex(form.as_p(), r'<textarea.*>\nMy text</textarea>.*<textarea.*>\nMon texte</textarea>')

    def test_form_with_data_value(self):
        form = FormWithTranslatedValueField(
            data={
                'translated_value_en': 'My text',
                'translated_value_fr-be': 'Mon texte',
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {
            'translated_value': {
                settings.LANGUAGE_CODE_EN: 'My text',
                settings.LANGUAGE_CODE_FR: 'Mon texte',
            }
        })

    def test_form_without_data_value(self):
        form = FormWithTranslatedValueField(data={})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {
            'translated_value': {}
        })
