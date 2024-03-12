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
import uuid
from typing import List
from unittest.mock import ANY, patch

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import override_settings
from osis_document.contrib import FileUploadField

from admission.constants import PDF_MIME_TYPE
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.enums import (
    Onglets,
    TypeItemFormulaire,
    CleConfigurationItemFormulaire,
    TypeChampTexteFormulaire,
    TypeChampSelectionFormulaire,
)
from admission.forms.specific_question import ConfigurableFormMixin, PlainTextWidget
from base.forms.utils import EMPTY_CHOICE


class ConfigurableFormItemFieldTestCase(TestCase):
    first_uuid = uuid.uuid4()
    default_translated_value = {'en': '', 'fr-be': ''}

    @classmethod
    @override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/', LANGUAGE_CODE='en')
    def setUpTestData(cls):
        field_configurations: List[QuestionSpecifiqueDTO] = [
            QuestionSpecifiqueDTO(
                uuid='fe254203-17c7-47d6-95e4-3c5c532da551',
                type=TypeItemFormulaire.MESSAGE.name,
                requis=False,
                label='',
                texte='The very short message.',
                texte_aide='',
                configuration={CleConfigurationItemFormulaire.CLASSE_CSS.name: 'bg-valid'},
                onglet=Onglets.CHOIX_FORMATION.name,
                valeurs_possibles=[],
                valeur='',
                valeur_formatee='The very short message.',
                label_langue_candidat='',
            ),
            QuestionSpecifiqueDTO(
                uuid='fe254203-17c7-47d6-95e4-3c5c532da552',
                type=TypeItemFormulaire.TEXTE.name,
                requis=True,
                label='Text field 1',
                texte='Detailed data',
                texte_aide='Write here',
                configuration={CleConfigurationItemFormulaire.TAILLE_TEXTE.name: TypeChampTexteFormulaire.COURT.name},
                onglet=Onglets.CHOIX_FORMATION.name,
                valeurs_possibles=[],
                valeur='My short answer',
                valeur_formatee='My short answer',
                label_langue_candidat='Champ texte 1',
            ),
            QuestionSpecifiqueDTO(
                uuid='fe254203-17c7-47d6-95e4-3c5c532da553',
                type=TypeItemFormulaire.TEXTE.name,
                requis=False,
                label='Text field 2',
                texte='Detailed data',
                texte_aide='Write here',
                configuration={CleConfigurationItemFormulaire.TAILLE_TEXTE.name: TypeChampTexteFormulaire.LONG.name},
                onglet=Onglets.CHOIX_FORMATION.name,
                valeurs_possibles=[],
                valeur='My long answer',
                valeur_formatee='My long answer',
                label_langue_candidat='Champ texte 2',
            ),
            QuestionSpecifiqueDTO(
                uuid='fe254203-17c7-47d6-95e4-3c5c532da554',
                type=TypeItemFormulaire.DOCUMENT.name,
                requis=False,
                label='Document field',
                texte='Detailed data',
                texte_aide='',
                configuration={
                    CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name: 2,
                    CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name: ['text/plain'],
                },
                onglet=Onglets.CHOIX_FORMATION.name,
                valeurs_possibles=[],
                valeur=['file-token'],
                valeur_formatee=['file-token'],
                label_langue_candidat='Champ document',
            ),
            QuestionSpecifiqueDTO(
                uuid='fe254203-17c7-47d6-95e4-3c5c532da556',
                type=TypeItemFormulaire.SELECTION.name,
                requis=True,
                label='Unique selection field',
                texte='Detailed data',
                texte_aide='',
                configuration={
                    CleConfigurationItemFormulaire.TYPE_SELECTION.name: TypeChampSelectionFormulaire.BOUTONS_RADIOS.name,
                },
                onglet=Onglets.CHOIX_FORMATION.name,
                valeurs_possibles=[
                    ('1', 'One'),
                    ('2', 'Two'),
                ],
                valeur='1',
                valeur_formatee='1',
                label_langue_candidat='Champ sélection simple',
            ),
            QuestionSpecifiqueDTO(
                uuid='fe254203-17c7-47d6-95e4-3c5c532da557',
                type=TypeItemFormulaire.SELECTION.name,
                requis=False,
                label='Multiple selection field',
                texte='Detailed data',
                texte_aide='',
                configuration={
                    CleConfigurationItemFormulaire.TYPE_SELECTION.name: TypeChampSelectionFormulaire.CASES_A_COCHER.name,
                },
                onglet=Onglets.CHOIX_FORMATION.name,
                valeurs_possibles=[
                    ('1', 'One'),
                    ('2', 'Two'),
                ],
                valeur=['1', '2'],
                valeur_formatee='1, 2',
                label_langue_candidat='Champ sélection multiple',
            ),
            QuestionSpecifiqueDTO(
                uuid='fe254203-17c7-47d6-95e4-3c5c532da558',
                type=TypeItemFormulaire.SELECTION.name,
                requis=False,
                label='List field',
                texte='Detailed data',
                texte_aide='',
                configuration={
                    CleConfigurationItemFormulaire.TYPE_SELECTION.name: TypeChampSelectionFormulaire.LISTE.name,
                },
                onglet=Onglets.CHOIX_FORMATION.name,
                valeurs_possibles=[
                    ('1', 'One'),
                    ('2', 'Two'),
                ],
                valeur='1',
                valeur_formatee='1',
                label_langue_candidat='Champ liste',
            ),
        ]
        form = ConfigurableFormMixin(
            initial={
                'specific_question_answers': {
                    'fe254203-17c7-47d6-95e4-3c5c532da552': 'My response to the question 1.',
                    'fe254203-17c7-47d6-95e4-3c5c532da553': 'My response to the question 2.',
                    'fe254203-17c7-47d6-95e4-3c5c532da554': ['file:token', str(cls.first_uuid)],
                    'fe254203-17c7-47d6-95e4-3c5c532da555': 'My response in another tab',
                    'fe254203-17c7-47d6-95e4-3c5c532da556': '1',
                    'fe254203-17c7-47d6-95e4-3c5c532da557': ['1', '2'],
                    'fe254203-17c7-47d6-95e4-3c5c532da558': '1',
                },
            },
            form_item_configurations=field_configurations,
        )

        cls.fields = form.fields['specific_question_answers'].fields
        cls.widgets = form.fields['specific_question_answers'].widget.widgets

        cls.form = form
        cls.field_configurations = field_configurations

    def setUp(self) -> None:
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_configurable_form_decompress_method(self):
        result = self.form.fields['specific_question_answers'].widget.decompress(
            self.form.initial['specific_question_answers']
        )

        self.assertEqual(
            result,
            [
                ANY,
                'My response to the question 1.',
                'My response to the question 2.',
                ['file:token', self.first_uuid],
                '1',
                ['1', '2'],
                '1',
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
        self.assertTrue(field.required)
        self.assertTrue(getattr(field, 'is_required', None))
        self.assertEqual(field.label, 'Text field 1')
        self.assertEqual(field.help_text, 'Detailed data')

        # Check widget
        self.assertIsInstance(widget, forms.TextInput)
        self.assertEqual(widget.attrs['placeholder'], 'Write here')

        # Short text
        field = self.fields[2]
        widget = self.widgets[2]

        # Check field
        self.assertIsInstance(field, forms.CharField)
        self.assertFalse(field.required)
        self.assertEqual(field.label, 'Text field 2')
        self.assertEqual(field.help_text, 'Detailed data')

        # Check widget
        self.assertIsInstance(widget, forms.Textarea)
        self.assertEqual(widget.attrs['placeholder'], 'Write here')

    def test_configurable_form_with_document_field(self):
        field = self.fields[3]

        # Check field
        self.assertIsInstance(field, FileUploadField)
        self.assertEqual(field.required, False)
        self.assertEqual(field.label, 'Document field')
        self.assertEqual(field.help_text, 'Detailed data')
        self.assertEqual(field.max_files, 1)
        self.assertEqual(field.mimetypes, [PDF_MIME_TYPE])

    def test_configurable_form_with_selection_field(self):
        # Unique selection
        field = self.fields[4]
        widget = self.widgets[4]

        # Check field
        self.assertIsInstance(field, forms.ChoiceField)
        self.assertTrue(field.required)
        self.assertTrue(getattr(field, 'is_required', None))
        self.assertEqual(field.label, 'Unique selection field')
        self.assertEqual(field.help_text, 'Detailed data')
        self.assertEqual(field.choices, [('1', 'One'), ('2', 'Two')])

        # Check widget
        self.assertIsInstance(widget, forms.RadioSelect)

        # Multiple selection
        field = self.fields[5]
        widget = self.widgets[5]

        # Check field
        self.assertIsInstance(field, forms.MultipleChoiceField)
        self.assertFalse(field.required)
        self.assertEqual(field.label, 'Multiple selection field')
        self.assertEqual(field.help_text, 'Detailed data')
        self.assertEqual(field.choices, [('1', 'One'), ('2', 'Two')])

        # Check widget
        self.assertIsInstance(widget, forms.CheckboxSelectMultiple)

        # List field
        field = self.fields[6]
        widget = self.widgets[6]

        # Check field
        self.assertIsInstance(field, forms.ChoiceField)
        self.assertFalse(field.required)
        self.assertEqual(field.label, 'List field')
        self.assertEqual(field.help_text, 'Detailed data')
        self.assertEqual(field.choices, [EMPTY_CHOICE[0], ('1', 'One'), ('2', 'Two')])

        # Check widget
        self.assertIsInstance(widget, forms.Select)

    def test_configurable_form_with_unknown_field(self):
        with self.assertRaises(ImproperlyConfigured):
            ConfigurableFormMixin(
                form_item_configurations=[
                    QuestionSpecifiqueDTO(
                        uuid='fe254203-17c7-47d6-95e4-3c5c532da550',
                        type='UNKNOWN',
                        requis=False,
                        label='',
                        texte='',
                        texte_aide='',
                        configuration={},
                        onglet=Onglets.CHOIX_FORMATION.name,
                        valeurs_possibles=[],
                        valeur='',
                        valeur_formatee='',
                        label_langue_candidat='',
                    )
                ],
            )

    def test_configurable_form_with_valid_data(self):
        form = ConfigurableFormMixin(
            data={
                'specific_question_answers_1': 'My response to the question 1',
                'specific_question_answers_2': 'My response to the question 2',
                'specific_question_answers_4': '2',
                'specific_question_answers_5': ['2'],
                'specific_question_answers_6': '2',
            },
            form_item_configurations=self.field_configurations,
            initial={
                'specific_question_answers': {
                    'fe254203-17c7-47d6-95e4-3c5c532da555': 'My response in another tab',
                },
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data,
            {
                'specific_question_answers': {
                    'fe254203-17c7-47d6-95e4-3c5c532da552': 'My response to the question 1',
                    'fe254203-17c7-47d6-95e4-3c5c532da553': 'My response to the question 2',
                    'fe254203-17c7-47d6-95e4-3c5c532da554': [],
                    'fe254203-17c7-47d6-95e4-3c5c532da555': 'My response in another tab',
                    'fe254203-17c7-47d6-95e4-3c5c532da556': '2',
                    'fe254203-17c7-47d6-95e4-3c5c532da557': ['2'],
                    'fe254203-17c7-47d6-95e4-3c5c532da558': '2',
                }
            },
        )

    def test_configurable_form_with_empty_configuration(self):
        form = ConfigurableFormMixin(
            form_item_configurations=[],
        )
        self.assertEqual(len(form.fields['specific_question_answers'].fields), 0)

    def test_displayed_form(self):
        form_p = self.form.as_p()
        self.assertIn('The very short message.</p>', form_p)
        self.assertIn('value="My response to the question 1."', form_p)
        self.assertIn('My response to the question 2.</textarea>', form_p)
        self.assertIn('data-values="file:token,foobar"', form_p)
