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
from functools import partial
from typing import Any

from django import forms
from django.conf import settings
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from admission.contrib.models.cdd_config import CddConfiguration
from admission.ddd.doctorat.formation.domain.model._enums import CategorieActivite

TextareaArrayField = partial(
    SimpleArrayField,
    base_field=forms.CharField(),
    widget=forms.Textarea(),
    delimiter='\n',
    required=False,
)


class TranslatedListsValueWidget(forms.MultiWidget):
    """Widget of two textareas (one for each language)"""

    template_name = 'admission/config/translated_lists_value_widget.html'

    def __init__(self, *args, **kwargs):
        widgets = {
            settings.LANGUAGE_CODE_EN: forms.Textarea(attrs={'placeholder': _("English values")}),
            settings.LANGUAGE_CODE_FR: forms.Textarea(attrs={'placeholder': _("French values")}),
        }
        super().__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        # On display, transform into lines
        return [
            "\n".join(value[settings.LANGUAGE_CODE_EN]),
            "\n".join(value[settings.LANGUAGE_CODE_FR]),
        ]


class TranslatedListsValueField(forms.MultiValueField):
    widget = TranslatedListsValueWidget

    def __init__(self, *args, **kwargs):
        # Remove arguments from JSONField
        kwargs.pop("encoder", None)
        kwargs.pop("decoder", None)
        kwargs['help_text'] = kwargs['help_text'] or _('One choice per line, leave the "Other" value out')
        super().__init__((TextareaArrayField(), TextareaArrayField()), *args, **kwargs)

    def compress(self, data_list) -> Any:
        # On save, build a dict as JSON value
        return {
            settings.LANGUAGE_CODE_EN: data_list[0],
            settings.LANGUAGE_CODE_FR: data_list[1],
        }


def map_translated_lists_value_field(field, **kwargs):
    if isinstance(field, models.JSONField):
        kwargs['form_class'] = TranslatedListsValueField
    if field.name == 'category_labels':
        kwargs['help_text'] = _("Do not reorder values, and keep the same count")
    return models.Field.formfield(field, **kwargs)


class CddConfigForm(forms.ModelForm):
    formfield_callback = map_translated_lists_value_field

    class Meta:
        model = CddConfiguration
        exclude = ['cdd', 'id']

    def clean_category_labels(self):
        data = self.cleaned_data['category_labels']
        expected_length = len(CategorieActivite.choices())
        if any(len(data[lang]) != expected_length for lang in dict(settings.LANGUAGES)):
            raise ValidationError(_("Number of values mismatch"))
        return data
