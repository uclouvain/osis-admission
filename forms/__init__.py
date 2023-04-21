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
from functools import partial
from typing import List, Optional

from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.constants import DEFAULT_MIME_TYPES
from base.forms.utils.datefield import DATE_FORMAT
from base.models.academic_year import AcademicYear
from education_group.templatetags.education_group_extra import format_to_academic_year
from osis_document.contrib import FileUploadField
from reference.models.country import Country

EMPTY_CHOICE = (('', ' - '),)
NONE_CHOICE = ((None, ' - '),)
ALL_EMPTY_CHOICE = (('', _('All')),)
MINIMUM_SELECTABLE_YEAR = 2004
MAXIMUM_SELECTABLE_YEAR = 2031


class SelectOrOtherWidget(forms.MultiWidget):
    """Form widget to handle a configurable (from CDDConfiguration) list of choices, or other"""

    template_name = 'admission/doctorate/forms/select_or_other_widget.html'
    media = forms.Media(
        js=[
            'js/dependsOn.min.js',
            'admission/select_or_other.js',
        ]
    )

    def __init__(self, *args, **kwargs):
        widgets = {
            '': forms.Select(),
            'other': forms.TextInput(),
        }
        super().__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        # No value, no value to both fields
        if not value:
            return [None, None]
        # Pass value to radios if part of choices
        if value in dict(self.widgets[0].choices):
            return [value, '']
        # else pass value to textinput
        return ['other', value]

    def get_context(self, name: str, value, attrs):
        context = super().get_context(name, value, attrs)
        # Remove the required attribute on textinput
        context['widget']['subwidgets'][1]['attrs']['required'] = False
        return context


class SelectOrOtherField(forms.MultiValueField):
    """Form field to handle a list of choices, or other"""

    widget = SelectOrOtherWidget
    select_class = forms.ChoiceField

    def __init__(self, choices: Optional[List[str]] = None, *args, **kwargs):
        select_kwargs = {}
        if choices is not None:
            select_kwargs['choices'] = self.choices = list(zip(choices, choices)) + [('other', _("Other"))]
        fields = [self.select_class(required=False, **select_kwargs), forms.CharField(required=False)]
        super().__init__(fields, require_all_fields=False, *args, **kwargs)

    def get_bound_field(self, form, field_name):
        if not self.widget.widgets[0].choices:
            self.widget.widgets[0].choices = self.choices
        return super().get_bound_field(form, field_name)

    def validate(self, value):
        # We do require all fields, but we want to check the final (compressed value)
        super(forms.MultiValueField, self).validate(value)

    def compress(self, data_list):
        # On save, take the other value if "other" is chosen
        radio, other = data_list
        return radio if radio != "other" else other

    def clean(self, value):
        # Dispatch the correct values to each field before regular cleaning
        radio, other = value
        if hasattr(self, 'choices') and radio not in self.choices and other is None:
            value = ['other', radio]
        return super().clean(value)


class CustomDateInput(forms.DateInput):
    def __init__(self, attrs=None, format=DATE_FORMAT):
        if attrs is None:
            attrs = {
                'placeholder': _("dd/mm/yyyy"),
                'data-mask': '00/00/0000',
                'autocomplete': 'off',
            }
        super().__init__(attrs, format)

    class Media:
        js = ('jquery.mask.min.js',)


def get_academic_year_choices(min_year=MINIMUM_SELECTABLE_YEAR, max_year=MAXIMUM_SELECTABLE_YEAR):
    """Return the list of choices of academic years between min_year and max_year"""
    academic_years = AcademicYear.objects.min_max_years(
        min_year=min_year,
        max_year=max_year,
    ).order_by('-year')
    return [(academic_year.year, format_to_academic_year(academic_year.year)) for academic_year in academic_years]


def get_example_text(example: str):
    return _("e.g.: %(example)s") % {'example': example}


class AdmissionFileUploadField(FileUploadField):
    def __init__(self, **kwargs):
        kwargs.setdefault('mimetypes', DEFAULT_MIME_TYPES)
        super().__init__(**kwargs)


RadioBooleanField = partial(
    forms.TypedChoiceField,
    coerce=lambda value: value == 'True',
    choices=((True, _('Yes')), (False, _('No'))),
    widget=forms.RadioSelect,
    empty_value=None,
)


class AdmissionModelCountryChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', autocomplete.ListSelect2(url="country-autocomplete"))
        kwargs.setdefault('queryset', Country.objects.none())
        super().__init__(*args, **kwargs)
