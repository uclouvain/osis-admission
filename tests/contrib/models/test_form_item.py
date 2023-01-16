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

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.models import AdmissionFormItemInstantiation
from admission.contrib.models.form_item import (
    is_valid_translated_json_field,
    TRANSLATION_LANGUAGES,
    AdmissionFormItem,
)
from admission.ddd.admission.enums.question_specifique import (
    CleConfigurationItemFormulaire,
    TypeItemFormulaire,
    CritereItemFormulaireNationaliteCandidat,
    CritereItemFormulaireLangueEtudes,
    CritereItemFormulaireVIP,
    Onglets,
    CritereItemFormulaireFormation,
)
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory


class AdmissionFormItemTestCase(TestCase):
    config_params = [property_choice.name for property_choice in CleConfigurationItemFormulaire]

    @classmethod
    def setUpTestData(cls):
        json_value = {
            'en': 'Value',
            'fr-be': 'Valeur',
        }
        cls.default_form_item_properties = {
            'internal_label': 'field_1',
            'title': json_value,
            'text': json_value,
            'help_text': json_value,
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
            configuration={param: '' for param in self.config_params},
            **self.default_form_item_properties,
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(
                    'Propriétés invalides : TAILLE_TEXTE,TYPE_SELECTION,TYPES_MIME_FICHIER,NOMBRE_MAX_DOCUMENTS'
                ),
                error.error_dict['configuration'],
            )

    def test_text_is_invalid_because_of_incompatible_config_properties(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.TEXTE.name,
            configuration={param: '' for param in self.config_params},
            **self.default_form_item_properties,
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(
                    'Propriétés invalides : TYPE_SELECTION,CLASSE_CSS,TYPES_MIME_FICHIER,NOMBRE_MAX_DOCUMENTS'
                ),
                error.error_dict['configuration'],
            )

    def test_document_is_invalid_because_of_incompatible_config_properties(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.DOCUMENT.name,
            configuration={param: '' for param in self.config_params},
            **self.default_form_item_properties,
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError('Propriétés invalides : TYPE_SELECTION,TAILLE_TEXTE,CLASSE_CSS'),
                error.error_dict['configuration'],
            )

    def test_selection_is_invalid_because_of_incompatible_config_properties(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.SELECTION.name,
            configuration={param: '' for param in self.config_params},
            **self.default_form_item_properties,
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(
                    'Propriétés invalides : TAILLE_TEXTE,TYPE_SELECTION,TYPES_MIME_FICHIER,NOMBRE_MAX_DOCUMENTS'
                ),
                error.error_dict['configuration'],
            )

    def test_message_is_valid_if_no_config(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.MESSAGE.name,
                configuration={},
                **self.default_form_item_properties,
            )
            first_field.clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a message: ') + error.message)

    def test_message_is_not_valid_if_missing_text_for_a_language(self):
        first_field = AdmissionFormItem.objects.create(
            internal_label='field_1',
            type=TypeItemFormulaire.MESSAGE.name,
            text={
                'fr-be': 'Valeur',
            },
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(FIELD_REQUIRED_MESSAGE),
                error.error_dict['text'],
            )

    def test_message_is_not_valid_if_missing_text_for_all_languages(self):
        first_field = AdmissionFormItem.objects.create(
            internal_label='field_1',
            type=TypeItemFormulaire.MESSAGE.name,
            text={},
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(FIELD_REQUIRED_MESSAGE),
                error.error_dict['text'],
            )

    def test_text_is_not_valid_if_missing_title_for_a_language(self):
        first_field = AdmissionFormItem.objects.create(
            internal_label='field_1',
            type=TypeItemFormulaire.TEXTE.name,
            title={
                'fr-be': 'Valeur',
            },
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(FIELD_REQUIRED_MESSAGE),
                error.error_dict['title'],
            )

    def test_document_is_not_valid_if_missing_title_for_a_language(self):
        first_field = AdmissionFormItem.objects.create(
            internal_label='field_1',
            type=TypeItemFormulaire.TEXTE.name,
            title={
                'fr-be': 'Valeur',
            },
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(FIELD_REQUIRED_MESSAGE),
                error.error_dict['message'],
            )

    def test_document_is_valid_if_no_config(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.DOCUMENT.name,
                configuration={},
                **self.default_form_item_properties,
            )
            first_field.clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a document field: ') + error.message)

    def test_message_is_invalid_if_the_css_class_is_not_none_or_a_string(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.MESSAGE.name,
            configuration={
                'CLASSE_CSS': 10,
            },
            **self.default_form_item_properties,
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(_('The css class must be a string.')),
                error.error_dict['configuration'],
            )

    def test_message_is_valid_if_the_css_class_is_a_string(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.MESSAGE.name,
                configuration={
                    'CLASSE_CSS': 'valid',
                },
                **self.default_form_item_properties,
            )
            first_field.clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a message: ') + error.message)

    def test_text_is_invalid_if_the_text_size_is_not_none_or_a_valid_value(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.TEXTE.name,
            configuration={
                'TAILLE_TEXTE': 'VERY_LONG_TEXT',
            },
            **self.default_form_item_properties,
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(
                    _('The text size must be one of the following values: %(values)s.')
                    % {'values': str(AdmissionFormItem.valid_form_item_text_types)},
                ),
                error.error_dict['configuration'],
            )

    def test_text_is_valid_if_the_text_size_is_one_of_the_valid_values(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.TEXTE.name,
                configuration={
                    'TAILLE_TEXTE': 'COURT',
                },
                **self.default_form_item_properties,
            )
            first_field.clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a text: ') + error.message)

    def test_document_is_invalid_if_the_maximum_number_of_documents_is_not_an_integer(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.DOCUMENT.name,
            configuration={
                'NOMBRE_MAX_DOCUMENTS': 'DEUX',
            },
            **self.default_form_item_properties,
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(_('The maximum number of documents must be a positive number.')),
                error.error_dict['configuration'],
            )

    def test_document_is_invalid_if_the_maximum_number_of_documents_is_not_a_positive_integer(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.DOCUMENT.name,
            configuration={
                'NOMBRE_MAX_DOCUMENTS': -1,
            },
            **self.default_form_item_properties,
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(_('The maximum number of documents must be a positive number.')),
                error.error_dict['configuration'],
            )

    def test_document_is_valid_if_the_maximum_number_of_documents_is_a_positive_integer(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.DOCUMENT.name,
                configuration={
                    'NOMBRE_MAX_DOCUMENTS': 2,
                },
                **self.default_form_item_properties,
            )
            first_field.clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a document: ') + error.message)

    def test_document_is_invalid_if_the_mime_types_are_not_a_list_of_at_least_one_element(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.DOCUMENT.name,
            configuration={
                'TYPES_MIME_FICHIER': [],
            },
            **self.default_form_item_properties,
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(_('The mimetypes must be a list with at least one mimetype.')),
                error.error_dict['configuration'],
            )

    def test_document_is_valid_if_the_mime_types_are_a_list_of_at_least_one_element(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.DOCUMENT.name,
                configuration={
                    'TYPES_MIME_FICHIER': ['text/plain'],
                },
                **self.default_form_item_properties,
            )
            first_field.clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a document: ') + error.message)

    def test_selection_is_invalid_if_the_selection_type_is_not_none_or_a_valid_value(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.SELECTION.name,
            configuration={
                'TYPE_SELECTION': 'UNKNOWN',
            },
            values=[{'key': '1', 'en': 'One', 'fr-be': 'Un'}],
            **self.default_form_item_properties,
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(
                    _('The selection type must be one of the following values: %(values)s.')
                    % {'values': str(AdmissionFormItem.valid_form_item_selection_types)},
                ),
                error.error_dict['configuration'],
            )

    def test_selection_is_valid_if_the_selection_type_is_one_of_the_valid_values(self):
        try:
            first_field = AdmissionFormItem.objects.create(
                type=TypeItemFormulaire.SELECTION.name,
                configuration={
                    'TYPE_SELECTION': 'CASES_A_COCHER',
                },
                values=[{'key': '1', 'en': 'One', 'fr-be': 'Un'}],
                **self.default_form_item_properties,
            )
            first_field.clean()
        except ValidationError as error:
            self.fail(_('The configuration is not valid for a text: ') + error.message)

    def test_selection_is_not_valid_if_missing_title_for_a_language(self):
        first_field = AdmissionFormItem.objects.create(
            internal_label='field_1',
            type=TypeItemFormulaire.SELECTION.name,
            title={
                'fr-be': 'Valeur',
            },
            values=[{'key': '1', 'en': 'One', 'fr-be': 'Un'}],
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(FIELD_REQUIRED_MESSAGE),
                error.error_dict['message'],
            )

    def test_selection_is_not_valid_if_no_value(self):
        first_field = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.SELECTION.name,
            **self.default_form_item_properties,
            values=[],
        )
        with self.assertRaises(ValidationError) as error:
            first_field.clean()
            self.assertIn(
                ValidationError(FIELD_REQUIRED_MESSAGE),
                error.error_dict['message'],
            )


class AdmissionFormItemInstantiationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        admission_form_item = AdmissionFormItem.objects.create(
            type=TypeItemFormulaire.MESSAGE.name,
        )
        academic_year_pk = AcademicYearFactory().pk

        cls.default_form_item_instantiation_properties = {
            'form_item': admission_form_item,
            'academic_year_id': academic_year_pk,
            'weight': 1,
            'required': True,
            # 'display_according_education': ,
            # 'education_group_type': '',
            # 'education_group': '',
            'candidate_nationality': CritereItemFormulaireNationaliteCandidat.TOUS.name,
            'study_language': CritereItemFormulaireLangueEtudes.TOUS.name,
            'vip_candidate': CritereItemFormulaireVIP.TOUS.name,
            'tab': Onglets.CURRICULUM.name,
        }

        cls.education_group = EducationGroupFactory()
        cls.education_group_type = EducationGroupTypeFactory()

    def test_clean_education_group_and_education_group_type_if_question_for_all_education(self):
        admission_form_item_instantiation = AdmissionFormItemInstantiation.objects.create(
            display_according_education=CritereItemFormulaireFormation.TOUTE_FORMATION.name,
            education_group_type=self.education_group_type,
            education_group=self.education_group,
            **self.default_form_item_instantiation_properties,
        )
        admission_form_item_instantiation.clean()
        self.assertIsNone(admission_form_item_instantiation.education_group_id)
        self.assertIsNone(admission_form_item_instantiation.education_group_type_id)

    def test_clean_education_group_if_question_for_an_education_group_type(self):
        admission_form_item_instantiation = AdmissionFormItemInstantiation.objects.create(
            display_according_education=CritereItemFormulaireFormation.TYPE_DE_FORMATION.name,
            education_group_type=self.education_group_type,
            education_group=self.education_group,
            **self.default_form_item_instantiation_properties,
        )
        admission_form_item_instantiation.clean()
        self.assertIsNotNone(admission_form_item_instantiation.education_group_type_id)
        self.assertIsNone(admission_form_item_instantiation.education_group_id)

    def test_clean_education_group_if_question_for_an_education_group(self):
        admission_form_item_instantiation = AdmissionFormItemInstantiation.objects.create(
            display_according_education=CritereItemFormulaireFormation.UNE_FORMATION.name,
            education_group_type=self.education_group_type,
            education_group=self.education_group,
            **self.default_form_item_instantiation_properties,
        )
        admission_form_item_instantiation.clean()
        self.assertIsNotNone(admission_form_item_instantiation.education_group_id)
        self.assertIsNone(admission_form_item_instantiation.education_group_type_id)

    def test_raise_an_exception_if_education_group_type_needed_and_not_specified(self):
        admission_form_item_instantiation = AdmissionFormItemInstantiation.objects.create(
            display_according_education=CritereItemFormulaireFormation.TYPE_DE_FORMATION.name,
            **self.default_form_item_instantiation_properties,
        )
        with self.assertRaises(ValidationError) as error:
            admission_form_item_instantiation.clean()
            self.assertIn(ValidationError(FIELD_REQUIRED_MESSAGE), error.error_dict.get('education_group_type', []))

    def test_raise_an_exception_if_education_group_needed_and_not_specified(self):
        admission_form_item_instantiation = AdmissionFormItemInstantiation.objects.create(
            display_according_education=CritereItemFormulaireFormation.UNE_FORMATION.name,
            **self.default_form_item_instantiation_properties,
        )
        with self.assertRaises(ValidationError) as error:
            admission_form_item_instantiation.clean()
            self.assertIn(ValidationError(FIELD_REQUIRED_MESSAGE), error.error_dict.get('education_group', []))
