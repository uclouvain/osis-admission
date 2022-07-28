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
from typing import List

from django import forms
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.utils.translation import get_language, gettext_lazy as _

from admission.contrib.models.form_item import (
    DEFAULT_MAX_NB_DOCUMENTS,
)
from admission.ddd.projet_doctoral.preparation.domain.model._enums import (
    TypeItemFormulaire,
    CleConfigurationItemFormulaire,
    TypeChampTexteFormulaire,
    TYPES_ITEMS_LECTURE_SEULE,
)
from admission.utils import get_uuid_value
from osis_document.contrib import FileUploadField


class PlainTextWidget(forms.Widget):
    """Widget to display a text content inside a paragraph."""

    template_name = 'admission/config/plain_text_widget.html'

    def __init__(self, content, css_class='', **kwargs):
        self.content = content
        self.css_class = css_class
        super().__init__(**kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['content'] = self.content
        context['widget']['css_class'] = self.css_class
        return context

    def build_attrs(self, base_attrs, extra_attrs=None):
        return {}


class ConfigurableFormItemWidget(forms.MultiWidget):
    template_name = 'admission/config/multiwidget.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['fields'] = list(zip(context['widget']['subwidgets'], self.fields))
        context['current_language'] = self.current_language
        context['is_bound'] = self.is_bound
        return context

    def __init__(self, field_configurations: List[dict], fields: List[forms.Field], is_bound=False, **kwargs):
        self.field_configurations = field_configurations
        self.fields = fields
        self.current_language = get_language()
        self.is_bound = is_bound
        super().__init__(**kwargs)

    def decompress(self, value):
        """Takes a single “compressed” value from the field and returns a list of “decompressed” values."""

        if not value:
            value = {}

        field_values = []

        for field in self.field_configurations:
            if field['type'] == TypeItemFormulaire.DOCUMENT.name:
                field_value = [get_uuid_value(token) for token in value.get(str(field['uuid']), [])]
            else:
                field_value = value.get(str(field['uuid']))
            field_values.append(field_value)

        return field_values


class ConfigurableFormItemField(forms.MultiValueField):
    @staticmethod
    def get_default_field_params(configuration: dict, current_language: str):
        return {
            'required': configuration['required'],
            'label': configuration['title'].get(current_language, ''),
            'help_text': configuration['text'].get(current_language, ''),
            'error_messages': {
                'incomplete': _('Please specify a value for the following field: {}').format(
                    configuration['title'].get(current_language)
                ),
            },
        }

    def __init__(self, configurations: List[dict], **kwargs):
        self.field_configurations = configurations
        current_language = get_language()

        fields = []
        widgets = []

        # Create the lists of fields and widgets based on the input configurations
        for configuration in configurations:

            form_item_type = configuration['type']

            if form_item_type == TypeItemFormulaire.MESSAGE.name:
                field = forms.Field(
                    required=False,
                    widget=PlainTextWidget(
                        content=configuration['text'].get(current_language, ''),
                        css_class=configuration['config'].get(CleConfigurationItemFormulaire.CLASSE_CSS.name, ''),
                    ),
                )

            elif form_item_type == TypeItemFormulaire.TEXTE.name:
                widget = (
                    forms.Textarea
                    if configuration['config'].get(CleConfigurationItemFormulaire.TAILLE_TEXTE.name)
                    == TypeChampTexteFormulaire.LONG.name
                    else forms.TextInput
                )
                field = forms.CharField(
                    **self.get_default_field_params(configuration, current_language),
                    widget=widget(
                        attrs={
                            'placeholder': configuration['help_text'].get(current_language, ''),
                            'required': configuration['required'],
                        }
                    ),
                )

            elif form_item_type == TypeItemFormulaire.DOCUMENT.name:
                field = FileUploadField(
                    **self.get_default_field_params(configuration, current_language),
                    max_files=configuration['config'].get(
                        CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name,
                        DEFAULT_MAX_NB_DOCUMENTS,
                    ),
                    mimetypes=configuration['config'].get(CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name),
                )

            else:
                raise ImproperlyConfigured(
                    _('The type of the admission form item is unknown (%(type)s).' % {'type': form_item_type})
                )

            fields.append(field)
            widgets.append(field.widget)

        super().__init__(
            fields=fields,
            widget=ConfigurableFormItemWidget(
                widgets=widgets,
                field_configurations=self.field_configurations,
                fields=fields,
                is_bound=kwargs.pop('is_bound'),
            ),
            require_all_fields=False,
            required=False,
            **kwargs,
        )

    def clean(self, value):
        """
        Validate every value in the given list. A value is validated against
        the corresponding Field in self.fields which will contain errors if any (errors attribute).

        For example, if this MultiValueField was instantiated with
        fields=(DateField(), TimeField()), clean() would call
        DateField.clean(value[0]) and TimeField.clean(value[1]).
        """
        clean_data = []
        has_error = False
        for i, field in enumerate(self.fields):
            try:
                field_value = value[i]
            except IndexError:
                field_value = None
            try:
                clean_data.append(field.clean(field_value))
            except ValidationError as e:
                field.errors = e.error_list
                has_error = True
        if has_error:
            raise ValidationError('')

        out = self.compress(clean_data)
        self.validate(out)
        self.run_validators(out)
        return out

    def compress(self, data_list):
        """Takes a list of valid values and returns a “compressed” version of those values – in a single value."""
        compressed_data = {}
        for index, data in enumerate(data_list):
            field_configuration = self.field_configurations[index]
            if field_configuration['type'] not in TYPES_ITEMS_LECTURE_SEULE:
                compressed_data[str(field_configuration['uuid'])] = data

        return compressed_data


class ConfigurableFormMixin(forms.Form):
    """Form whose some fields will be automatically created on the basis of a configuration."""

    configurable_form_field_name = 'configurable_form_field'  # Name of the form field which contains several values

    def __init__(self, form_item_configurations: List[dict], *args, **kwargs):
        super().__init__(*args, **kwargs)

        configurable_field = ConfigurableFormItemField(
            configurations=form_item_configurations,
            is_bound=self.is_bound,
        )

        if configurable_field.fields:
            self.fields[self.configurable_form_field_name] = configurable_field
