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
from django.utils.translation import gettext_lazy

from admission.forms.translation_field import TranslatedValueField, IdentifiedTranslatedListsValueField


class FormWithTranslatedValueField(forms.Form):
    translated_value = TranslatedValueField(required=False, require_all_fields=False)


class FormWithIdentifiedTranslatedListsValueField(forms.Form):
    identified_translated_lists_value = IdentifiedTranslatedListsValueField(required=False)


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
        self.assertEqual(
            form.cleaned_data,
            {
                'translated_value': {
                    settings.LANGUAGE_CODE_EN: 'My text',
                    settings.LANGUAGE_CODE_FR: 'Mon texte',
                }
            },
        )

    def test_form_without_data_value(self):
        form = FormWithTranslatedValueField(data={})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {'translated_value': {}})


class IdentifiedTranslatedListsValueFieldTestCase(SimpleTestCase):
    def test_init_form_without_initial_value(self):
        form = FormWithIdentifiedTranslatedListsValueField()
        self.assertRegex(form.as_p(), r'.*<textarea.*></textarea>.*<textarea.*></textarea>.*<textarea.*></textarea>.*')

    def test_init_form_with_empty_data(self):
        form = FormWithIdentifiedTranslatedListsValueField(
            initial={
                'identified_translated_lists_value': [],
            }
        )
        self.assertRegex(form.as_p(), r'.*<textarea.*></textarea>.*<textarea.*></textarea>.*<textarea.*></textarea>.*')

    def test_init_form_with_initial_value(self):
        form = FormWithIdentifiedTranslatedListsValueField(
            initial={
                'identified_translated_lists_value': [
                    {
                        'key': 'key-1',
                        settings.LANGUAGE_CODE_EN: 'My text 1',
                        settings.LANGUAGE_CODE_FR: 'Mon texte 1',
                    },
                    {
                        'key': 'key-2',
                        settings.LANGUAGE_CODE_EN: 'My text 2',
                        settings.LANGUAGE_CODE_FR: 'Mon texte 2',
                    },
                ]
            }
        )
        self.assertRegex(
            form.as_p(),
            r'.*<textarea.*>\nkey-1\r\nkey-2</textarea>.*'
            r'<textarea.*>\nMy text 1\r\nMy text 2</textarea>.*'
            r'<textarea.*>\nMon texte 1\r\nMon texte 2</textarea>.*',
        )

    def test_form_with_data_value(self):
        form = FormWithIdentifiedTranslatedListsValueField(
            data={
                'identified_translated_lists_value_key': 'key-1\nkey-2\nkey-3\n',
                'identified_translated_lists_value_en': 'One\nTwo\nThree\n',
                'identified_translated_lists_value_fr-be': 'Un\nDeux\nTrois\n',
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data,
            {
                'identified_translated_lists_value': [
                    {
                        'key': 'key-1',
                        settings.LANGUAGE_CODE_EN: 'One',
                        settings.LANGUAGE_CODE_FR: 'Un',
                    },
                    {
                        'key': 'key-2',
                        settings.LANGUAGE_CODE_EN: 'Two',
                        settings.LANGUAGE_CODE_FR: 'Deux',
                    },
                    {
                        'key': 'key-3',
                        settings.LANGUAGE_CODE_EN: 'Three',
                        settings.LANGUAGE_CODE_FR: 'Trois',
                    },
                ]
            },
        )

    def test_form_with_data_value_without_keys(self):
        form = FormWithIdentifiedTranslatedListsValueField(
            data={
                'identified_translated_lists_value_key': '',
                'identified_translated_lists_value_en': 'One\nTwo\nThree\n',
                'identified_translated_lists_value_fr-be': 'Un\nDeux\nTrois\n',
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data,
            {
                'identified_translated_lists_value': [
                    {
                        'key': '1',
                        settings.LANGUAGE_CODE_EN: 'One',
                        settings.LANGUAGE_CODE_FR: 'Un',
                    },
                    {
                        'key': '2',
                        settings.LANGUAGE_CODE_EN: 'Two',
                        settings.LANGUAGE_CODE_FR: 'Deux',
                    },
                    {
                        'key': '3',
                        settings.LANGUAGE_CODE_EN: 'Three',
                        settings.LANGUAGE_CODE_FR: 'Trois',
                    },
                ]
            },
        )

    def test_form_without_data_value(self):
        form = FormWithIdentifiedTranslatedListsValueField(data={})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {'identified_translated_lists_value': []})

    def test_form_without_empty_data(self):
        form = FormWithIdentifiedTranslatedListsValueField(
            data={
                'identified_translated_lists_value_key': '',
                'identified_translated_lists_value_en': '',
                'identified_translated_lists_value_fr-be': '',
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {'identified_translated_lists_value': []})

    def test_form_with_invalid_middle_option(self):
        form = FormWithIdentifiedTranslatedListsValueField(
            data={
                'identified_translated_lists_value_key': 'key-1\nkey-2\nkey-3\n',
                'identified_translated_lists_value_en': 'One\n\nThree\n',
                'identified_translated_lists_value_fr-be': 'Un\nDeux\nTrois\n',
            },
        )
        index = 2
        self.assertFalse(form.is_valid())
        self.assertIn(
            gettext_lazy(f'The option {index} must have an identifier and a translation for each required language.'),
            form.errors.get('identified_translated_lists_value', []),
        )

    def test_form_with_invalid_last_option(self):
        form = FormWithIdentifiedTranslatedListsValueField(
            data={
                'identified_translated_lists_value_key': 'key-1\nkey-2\nkey-3\n',
                'identified_translated_lists_value_en': 'One\nTwo\nThree\n',
                'identified_translated_lists_value_fr-be': 'Un\nDeux\n',
            },
        )
        index = 3
        self.assertFalse(form.is_valid())
        self.assertIn(
            gettext_lazy(f'The option {index} must have an identifier and a translation for each required language.'),
            form.errors.get('identified_translated_lists_value', []),
        )
