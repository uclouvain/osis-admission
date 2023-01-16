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
from typing import Any

from django import forms
from django.conf import settings
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


TRANSLATION_LANGUAGES = [settings.LANGUAGE_CODE_EN, settings.LANGUAGE_CODE_FR]


class TranslatedValueWidget(forms.MultiWidget):
    """Widget of two textareas (one for each language)"""

    template_name = 'admission/config/translated_value_widget.html'

    def __init__(self, *args, **kwargs):
        widgets = {
            settings.LANGUAGE_CODE_EN: forms.Textarea(attrs={'placeholder': _("English value"), 'rows': 3}),
            settings.LANGUAGE_CODE_FR: forms.Textarea(attrs={'placeholder': _("French value"), 'rows': 3}),
        }
        super().__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        # On display, return an array of values

        if not value:
            return []

        return [value.get(language, '') for language in TRANSLATION_LANGUAGES]


class TranslatedValueField(forms.MultiValueField):
    widget = TranslatedValueWidget

    def __init__(self, *args, **kwargs):
        # Remove arguments from JSONField
        kwargs.pop("encoder", None)
        kwargs.pop("decoder", None)
        super().__init__((forms.CharField(), forms.CharField()), *args, **kwargs)

    def compress(self, data_list) -> Any:
        # On save, build a dict as JSON value
        if not data_list:
            return {}

        return {language: data_list[index] for index, language in enumerate(TRANSLATION_LANGUAGES)}


class IdentifiedTranslatedListsValueWidget(forms.MultiWidget):
    """Widget of three textareas (one for the id and one for each language)"""

    template_name = 'admission/config/identified_translated_lists_value_widget.html'

    def __init__(self, *args, **kwargs):
        widgets = {
            'key': forms.Textarea(attrs={'placeholder': _("Keys"), 'cols': 3}),
            settings.LANGUAGE_CODE_EN: forms.Textarea(attrs={'placeholder': _("English values")}),
            settings.LANGUAGE_CODE_FR: forms.Textarea(attrs={'placeholder': _("French values")}),
        }
        super().__init__(widgets, *args, **kwargs)


class SplitTextareaArrayField(SimpleArrayField):
    def __init__(self, *args, **kwargs):
        kwargs['base_field'] = forms.CharField(required=False)
        kwargs['required'] = False
        kwargs['widget'] = forms.Textarea()
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if type(value) == str:
            value = value.splitlines()
        return super().to_python(value)


class IdentifiedTranslatedListsValueField(forms.Field):
    widget = IdentifiedTranslatedListsValueWidget
    delimiter = '\r\n'

    def __init__(self, *args, **kwargs):
        # Remove arguments from ArrayField
        kwargs.pop("max_length", None)
        kwargs.pop("base_field", None)
        self.base_form_field = SplitTextareaArrayField()
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if not value:
            return []

        if type(value[0]) == str:
            # Already prepared
            return value

        # On display, transform into lines
        return [
            # Keys
            self.delimiter.join([option.get('key', '') for option in value]),
            # English labels
            self.delimiter.join([option.get(settings.LANGUAGE_CODE_EN, '') for option in value]),
            # French labels
            self.delimiter.join([option.get(settings.LANGUAGE_CODE_FR, '') for option in value]),
        ]

    def clean(self, list_value):
        # Check the string value of every textarea and convert it to array
        max_nb_elements = 0

        for index, sub_value in enumerate(list_value):
            list_value[index] = self.base_form_field.clean(sub_value)
            max_nb_elements = max(max_nb_elements, len(list_value[index]))

        # Compress the value of every array into a dict value
        result = []
        iter_keys = iter(list_value[0] if list_value[0] else [str(number) for number in range(1, max_nb_elements + 1)])
        iter_en_labels = iter(list_value[1])
        iter_fr_labels = iter(list_value[2])
        errors = []

        for index in range(1, max_nb_elements + 1):
            option = {
                'key': next(iter_keys, ''),
                settings.LANGUAGE_CODE_EN: next(iter_en_labels, ''),
                settings.LANGUAGE_CODE_FR: next(iter_fr_labels, ''),
            }

            if all(option.values()):
                result.append(option)
            else:
                errors.append(
                    ValidationError(
                        _(f'The option {index} must have an identifier and a translation for each required language.')
                    )
                )

        if errors:
            raise ValidationError(errors)

        return result
