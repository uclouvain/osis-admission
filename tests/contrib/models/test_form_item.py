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
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext as _

from admission.contrib.models.form_item import (
    is_valid_translated_json_field,
    TRANSLATION_LANGUAGES,
    AdmissionFormItem,
)
from admission.ddd.projet_doctoral.preparation.domain.model._enums import (
    CleConfigurationItemFormulaire,
    TypeItemFormulaire,
)
from base.tests.factories.education_group_year import EducationGroupYearFactory


class AdmissionFormItemTestCase(TestCase):
    config_params = [property_choice.name for property_choice in CleConfigurationItemFormulaire]

    @classmethod
    def setUpTestData(cls):
        cls.default_form_item_properties = {
            'education': EducationGroupYearFactory(),
            'weight': 1,
            'internal_label': 'field_1',
        }

    def test_is_valid_translated_json_field(self):
        try:
            is_valid_translated_json_field(
                {
                    'en': 'my translation',
                    'fr-be': 'ma traduction',
                }
            )
        except ValidationError:
            self.fail(_("No 'ValidationError' exception must be triggered with the the provided data."))

    def test_is_valid_translated_json_field_if_empty(self):
        try:
            is_valid_translated_json_field({})
        except ValidationError:
            self.fail(_("No 'ValidationError' exception must be triggered with the the provided data."))

    def test_is_invalid_translated_json_field_because_of_missing_language(self):
        with self.assertRaisesMessage(
            ValidationError,
            _('This field must contain a translation for each of the following languages: %(languages)s.')
            % {'languages': str(TRANSLATION_LANGUAGES)},
        ):
            is_valid_translated_json_field(
                {
                    'en': 'my translation',
                }
            )

    def test_is_invalid_translated_json_field_if_none(self):
        with self.assertRaisesMessage(ValidationError, _('Must be a dictionary.')):
            is_valid_translated_json_field(None)

    def test_is_invalid_translated_json_field_if_translation_is_not_a_string(self):
        with self.assertRaises(ValidationError):
            is_valid_translated_json_field(
                {
                    'en': 'my translation',
                    'fr-be': 10,
                }
            )

    def test_message_is_invalid_because_of_incompatible_config_properties(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.MESSAGE.name,
            config={param: '' for param in self.config_params},
            **self.default_form_item_properties,
        )
        try:
            first_field.full_clean()
            self.fail(
                'Some configuration parameters must be invalid among: %(params)s.' % {'params': self.config_params}
            )
        except ValidationError as error:
            self.assertIn(
                ValidationError('Propriétés invalides : TAILLE_TEXTE,TYPES_MIME_FICHIER,NOMBRE_MAX_DOCUMENTS'),
                error.error_dict['config'],
            )

    def test_text_is_invalid_because_of_incompatible_config_properties(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.TEXTE.name,
            config={param: '' for param in self.config_params},
            **self.default_form_item_properties,
        )
        try:
            first_field.full_clean()
            self.fail(
                'Some configuration parameters must be invalid among: %(params)s.' % {'params': self.config_params}
            )
        except ValidationError as error:
            self.assertIn(
                ValidationError('Propriétés invalides : CLASSE_CSS,TYPES_MIME_FICHIER,NOMBRE_MAX_DOCUMENTS'),
                error.error_dict['config'],
            )

    def test_document_is_invalid_because_of_incompatible_config_properties(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.DOCUMENT.name,
            config={param: '' for param in self.config_params},
            **self.default_form_item_properties,
        )
        try:
            first_field.full_clean()
            self.fail(
                'Some configuration parameters must be invalid among: %(params)s.' % {'params': self.config_params}
            )
        except ValidationError as error:
            self.assertIn(
                ValidationError('Propriétés invalides : TAILLE_TEXTE,CLASSE_CSS'),
                error.error_dict['config'],
            )

    def test_message_is_valid_if_no_config(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.MESSAGE.name,
                config={},
                **self.default_form_item_properties,
            )
            first_field.full_clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a message: ') + error.message)

    def test_text_is_valid_if_no_config(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.TEXTE.name,
                config={},
                **self.default_form_item_properties,
            )
            first_field.full_clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a text field: ') + error.message)

    def test_document_is_valid_if_no_config(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.DOCUMENT.name,
                config={},
                **self.default_form_item_properties,
            )
            first_field.full_clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a document field: ') + error.message)

    def test_message_is_invalid_if_the_css_class_is_not_none_or_a_string(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.MESSAGE.name,
                config={
                    'CLASSE_CSS': 10,
                },
                **self.default_form_item_properties,
            )
            first_field.full_clean()
            self.fail('10 must not be a valid property value.')
        except ValidationError as error:
            self.assertIn(
                ValidationError(_('The css class must be a string.')),
                error.error_dict['config'],
            )

    def test_message_is_valid_if_the_css_class_is_a_string(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.MESSAGE.name,
                config={
                    'CLASSE_CSS': 'valid',
                },
                **self.default_form_item_properties,
            )
            first_field.full_clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a message: ') + error.message)

    def test_text_is_invalid_if_the_text_size_is_not_none_or_a_valid_value(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.TEXTE.name,
                config={
                    'TAILLE_TEXTE': 'VERY_LONG_TEXT',
                },
                **self.default_form_item_properties,
            )
            first_field.full_clean()
            self.fail(
                _('The following value must not be a valid property: %(property)s.' % {'property': 'VERY_LONG_TEXT'})
            )
        except ValidationError as error:
            self.assertIn(
                ValidationError(
                    _('The text size must be one of the following values: %(values)s.')
                    % {'values': str(AdmissionFormItem.valid_form_item_text_types)},
                ),
                error.error_dict['config'],
            )

    def test_text_is_valid_if_the_text_size_is_one_a_the_valid_values(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.TEXTE.name,
                config={
                    'TAILLE_TEXTE': 'COURT',
                },
                **self.default_form_item_properties,
            )
            first_field.full_clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a text: ') + error.message)

    def test_document_is_invalid_if_the_maximum_number_of_documents_is_not_an_integer(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.DOCUMENT.name,
                config={
                    'NOMBRE_MAX_DOCUMENTS': 'DEUX',
                },
                **self.default_form_item_properties,
            )
            first_field.full_clean()
            self.fail(_('The following value must not be a valid property: %(property)s.' % {'property': 'DEUX'}))
        except ValidationError as error:
            self.assertIn(
                ValidationError(_('The maximum number of documents must be a positive number.')),
                error.error_dict['config'],
            )

    def test_document_is_invalid_if_the_maximum_number_of_documents_is_not_a_positive_integer(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.DOCUMENT.name,
                config={
                    'NOMBRE_MAX_DOCUMENTS': -1,
                },
                **self.default_form_item_properties,
            )
            first_field.full_clean()
            self.fail(_('The following value must not be a valid property: %(property)s.' % {'property': -1}))
        except ValidationError as error:
            self.assertIn(
                ValidationError(_('The maximum number of documents must be a positive number.')),
                error.error_dict['config'],
            )

    def test_document_is_valid_if_the_maximum_number_of_documents_is_a_positive_integer(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.DOCUMENT.name,
                config={
                    'NOMBRE_MAX_DOCUMENTS': 2,
                },
                **self.default_form_item_properties,
            )
            first_field.full_clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a document: ') + error.message)

    def test_document_is_invalid_if_the_mime_types_are_not_a_list_of_at_least_one_element(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.DOCUMENT.name,
                config={
                    'TYPES_MIME_FICHIER': [],
                },
                **self.default_form_item_properties,
            )
            first_field.full_clean()
            self.fail(_('The following value must not be a valid property: %(property)s.' % {'property': -1}))
        except ValidationError as error:
            self.assertIn(
                ValidationError(_('The mimetypes must be a list with at least one mimetype.')),
                error.error_dict['config'],
            )

    def test_document_is_valid_if_the_mime_types_are_a_list_of_at_least_one_element(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.DOCUMENT.name,
                config={
                    'TYPES_MIME_FICHIER': ['text/plain'],
                },
                **self.default_form_item_properties,
            )
            first_field.full_clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a document: ') + error.message)
