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
import uuid
from unittest.mock import ANY, patch

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import override_settings
from osis_document.contrib import FileUploadField

from admission.forms.fields import PlainTextWidget, ConfigurableFormMixin


class ConfigurableFormItemFieldTestCase(TestCase):
    first_uuid = uuid.uuid4()

    @classmethod
    @override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/', LANGUAGE_CODE='en')
    def setUpTestData(cls):
        field_configurations = [
            {
                'uuid': 'fe254203-17c7-47d6-95e4-3c5c532da551',
                'type': 'MESSAGE',
                'required': None,
                'title': {},
                'text': {'en': 'The very short message.', 'fr-be': 'Le très court message.'},
                'help_text': {},
                'config': {
                    'CLASSE_CSS': 'bg-valid',
                },
            },
            {
                'uuid': 'fe254203-17c7-47d6-95e4-3c5c532da552',
                'type': 'TEXTE',
                'required': True,
                'title': {'en': 'Text field 1', 'fr-be': 'Champ texte 1'},
                'help_text': {'en': 'Write here', 'fr-be': 'Ecrivez ici'},
                'text': {'en': 'Detailed data', 'fr-be': 'Données détaillées'},
                'config': {
                    'TAILLE_TEXTE': 'COURT',
                },
            },
            {
                'uuid': 'fe254203-17c7-47d6-95e4-3c5c532da553',
                'type': 'TEXTE',
                'required': False,
                'title': {'en': 'Text field 2', 'fr-be': 'Champ texte 2'},
                'help_text': {'en': 'Write here', 'fr-be': 'Ecrivez ici'},
                'text': {'en': 'Detailed data', 'fr-be': 'Données détaillées'},
                'config': {
                    'TAILLE_TEXTE': 'LONG',
                },
            },
            {
                'uuid': 'fe254203-17c7-47d6-95e4-3c5c532da554',
                'type': 'DOCUMENT',
                'required': False,
                'title': {'en': 'Document field', 'fr-be': 'Champ document'},
                'help_text': {},
                'text': {'en': 'Detailed data', 'fr-be': 'Données détaillées'},
                'config': {
                    'NOMBRE_MAX_DOCUMENTS': 3,
                    'TYPES_MIME_FICHIER': ['text/plain'],
                },
            },
        ]

        form = ConfigurableFormMixin(
            initial={
                'configurable_form_field': {
                    'fe254203-17c7-47d6-95e4-3c5c532da552': 'My response to the question 1.',
                    'fe254203-17c7-47d6-95e4-3c5c532da553': 'My response to the question 2.',
                    'fe254203-17c7-47d6-95e4-3c5c532da554': ['file:token', str(cls.first_uuid)],
                },
            },
            form_item_configurations=field_configurations,
        )

        cls.fields = form.fields['configurable_form_field'].fields
        cls.widgets = form.fields['configurable_form_field'].widget.widgets

        cls.form = form
        cls.field_configurations = field_configurations

    def setUp(self) -> None:
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile"})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = "550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"
        self.addCleanup(patcher.stop)

    def test_configurable_form_decompress_method(self):
        result = self.form.fields['configurable_form_field'].widget.decompress(
            self.form.initial['configurable_form_field']
        )

        self.assertEqual(
            result,
            [
                ANY,
                'My response to the question 1.',
                'My response to the question 2.',
                ['file:token', self.first_uuid],
            ],
        )

    def test_configurable_form_with_message_field(self):
        field = self.fields[0]
        widget = self.widgets[0]

        # Check field
        self.assertIsInstance(field, forms.Field)
        self.assertEqual(field.required, False)

        # Check widget
        self.assertIsInstance(widget, PlainTextWidget)
        self.assertEqual(widget.content, 'The very short message.')
        self.assertEqual(widget.css_class, 'bg-valid')

    def test_configurable_form_with_text_field(self):
        # Short text
        field = self.fields[1]
        widget = self.widgets[1]

        # Check field
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.required, True)
        self.assertEqual(field.label, 'Text field 1')
        self.assertEqual(field.help_text, 'Detailed data')

        # Check widget
        self.assertIsInstance(widget, forms.TextInput)
        self.assertEqual(widget.attrs['placeholder'], 'Write here')
        self.assertEqual(widget.attrs['required'], True)

        # Short text
        field = self.fields[2]
        widget = self.widgets[2]

        # Check field
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.required, False)
        self.assertEqual(field.label, 'Text field 2')
        self.assertEqual(field.help_text, 'Detailed data')

        # Check widget
        self.assertIsInstance(widget, forms.Textarea)
        self.assertEqual(widget.attrs['placeholder'], 'Write here')
        self.assertEqual(widget.attrs['required'], False)

    def test_configurable_form_with_document_field(self):
        field = self.fields[3]

        # Check field
        self.assertIsInstance(field, FileUploadField)
        self.assertEqual(field.required, False)
        self.assertEqual(field.label, 'Document field')
        self.assertEqual(field.help_text, 'Detailed data')
        self.assertEqual(field.max_files, 3)
        self.assertEqual(field.mimetypes, ['text/plain'])

    def test_configurable_form_with_unknown_field(self):
        with self.assertRaises(ImproperlyConfigured):
            ConfigurableFormMixin(
                form_item_configurations=[
                    {
                        'pk': 5,
                        'type': 'UNKNOWN',
                        'required': False,
                        'title': {},
                        'help_text': {},
                        'text': {},
                        'config': {},
                    },
                ],
            )

    def test_configurable_form_with_valid_data(self):
        form = ConfigurableFormMixin(
            data={
                'configurable_form_field_1': 'My response to the question 1',
                'configurable_form_field_2': 'My response to the question 2',
            },
            form_item_configurations=self.field_configurations,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data,
            {
                'configurable_form_field': {
                    'fe254203-17c7-47d6-95e4-3c5c532da552': 'My response to the question 1',
                    'fe254203-17c7-47d6-95e4-3c5c532da553': 'My response to the question 2',
                    'fe254203-17c7-47d6-95e4-3c5c532da554': [],
                }
            },
        )

    def test_configurable_form_with_invalid_data(self):
        form = ConfigurableFormMixin(
            data={
                'configurable_form_field': {
                    # Text field 1 is required but missing
                },
            },
            form_item_configurations=self.field_configurations,
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.fields['configurable_form_field'].fields[1].errors[0].message,
            'Ce champ est obligatoire.',
        )

    def test_configurable_form_with_empty_configuration(self):
        form = ConfigurableFormMixin(
            form_item_configurations=[],
        )
        self.assertEqual(len(form.fields), 0)

    def test_displayed_form(self):
        form_p = self.form.as_p()
        self.assertIn('The very short message.</p>', form_p)
        self.assertIn('value="My response to the question 1."', form_p)
        self.assertIn('My response to the question 2.</textarea>', form_p)
        self.assertIn('data-values="file:token,foobar"', form_p)
