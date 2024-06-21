# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import html
from typing import List, Optional, Dict

import phonenumbers
from dal import forward
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, get_language

from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.enums import TypeBourse
from base.forms.utils import EMPTY_CHOICE, autocomplete
from base.models.academic_year import AcademicYear
from base.models.campus import Campus
from education_group.forms.fields import MainCampusChoiceField
from education_group.templatetags.education_group_extra import format_to_academic_year
from reference.models.country import Country

NONE_CHOICE = ((None, ' - '),)
ALL_EMPTY_CHOICE = (('', _('All')),)
OTHER_EMPTY_CHOICE = (('', _('Other')),)
MINIMUM_SELECTABLE_YEAR = 2004
MAXIMUM_SELECTABLE_YEAR = 2031
EMPTY_CHOICE_AS_LIST = [list(EMPTY_CHOICE[0])]
REQUIRED_FIELD_CLASS = 'required_field'

DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS = {
    'data-minimum-input-length': 3,
}

CKEDITOR_MAIL_EXTRA_ALLOWED_CONTENT = 'span(*)[*]{*};ul(*)[*]{*}'


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


class PhoneField(forms.CharField):
    def clean(self, value):
        value = super().clean(value)

        if not value:
            return ''
        try:
            phone_number_obj = phonenumbers.parse(value)
            if phonenumbers.is_valid_number(phone_number_obj):
                return value
        except phonenumbers.NumberParseException:
            pass
        raise ValidationError(_('Invalid phone number'))


def get_academic_year_choices(min_year=MINIMUM_SELECTABLE_YEAR, max_year=MAXIMUM_SELECTABLE_YEAR):
    """Return the list of choices of academic years between min_year and max_year"""
    academic_years = AcademicYear.objects.min_max_years(
        min_year=min_year,
        max_year=max_year,
    ).order_by('-year')
    return [(academic_year.year, format_to_academic_year(academic_year.year)) for academic_year in academic_years]


def get_year_choices(min_year=1920, max_year=None, full_format=False, empty_label=' - '):
    """
    Return the choices for a year choice field.
    :param min_year: The minimum year.
    :param max_year: The maximum year. If not specified, the current year is used.
    :param full_format: If True, the choices are in the format 'YYYY-YYYY', otherwise they are 'YYYY'.
    :param empty_label: The label of the empty choice.
    :return: The list of choices.
    """
    if max_year is None:
        max_year = datetime.datetime.now().year

    year_range = range(max_year, min_year - 1, -1)

    if full_format:
        choices = [('', empty_label)]
        for year in year_range:
            current_year = f'{year}-{year + 1}'
            choices.append((current_year, current_year))
        return choices
    else:
        return [('', empty_label)] + [(year, year) for year in year_range]


def get_scholarship_choices(scholarships, scholarship_type: TypeBourse):
    """
    Return the list of choices of a scholarship choice field.
    :param scholarships: The queryset containing the scholarships
    :param scholarship_type: The type of the scholarship
    :return: The list of choices
    """
    return EMPTY_CHOICE_AS_LIST + [
        [str(scholarship.uuid), scholarship.long_name or scholarship.short_name]
        for scholarship in scholarships
        if scholarship.type == scholarship_type.name
    ]


def format_training(training: FormationDTO):
    """
    Format a training into an html string
    :param training: The training
    :return: An html string
    """
    return '{intitule} ({campus}) <span class="training-acronym">{sigle}</span>'.format(
        intitule=training.intitule,
        campus=training.campus,
        sigle=training.sigle,
    )


# Move to base or reference (move url too)
class AdmissionModelCountryChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        to_field_name = kwargs.get('to_field_name', '')

        forward_params = kwargs.pop('additional_forward_params', []) + [
            forward.Const(True, 'active'),
        ]

        # The ids of the returned results will be the 'id_field' fields of the country model instead of 'pk'
        if to_field_name:
            forward_params.append(forward.Const(to_field_name, 'id_field'))

        kwargs.setdefault(
            'widget',
            autocomplete.ListSelect2(
                url=kwargs.pop('autocomplete_url_path', 'admission:autocomplete:countries'),
                attrs=DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
                forward=forward_params,
            ),
        )
        kwargs.setdefault('queryset', Country.objects.none())
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return getattr(obj, 'name' if get_language() == settings.LANGUAGE_CODE_FR else 'name_en')


class AdmissionModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        """
        When using a model form, the fields that are not specified in the 'data' attribute of the form are not updated,
        even if some data is provided through the 'cleaned_data' so we need to initialize them to
        simulate their submission.
        Define the 'fields_to_init' attribute in the Meta class of the form to specify which fields should be
        initialized.
        """
        super().__init__(*args, **kwargs)
        if self.data:
            self.data = self.data.copy()
            for field in getattr(self.Meta, 'fields_to_init', []):
                self.data.setdefault(self.add_prefix(field), None)


class FilterFieldWidget(forms.SelectMultiple):
    """
    A SelectMultiple with a JavaScript filter interface. The options can be filtered and new ones can be added
    whose the value corresponds to the specified text.
    If the choices are grouped (optgroups), the last optgroup is used to add new options.
    """

    class Media:
        js = [
            'admission/AdmissionSelectFilter.js',
        ]
        css = [
            'admission/AdmissionSelectFilter.css',
        ]

    def __init__(self, with_search=False, with_free_options=False, free_options_placeholder='', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.with_search = with_search
        self.with_free_options = with_free_options
        self.free_options_placeholder = free_options_placeholder

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs']['class'] = 'admissionselectfilter'
        context['widget']['attrs']['data-with-search'] = int(self.with_search)
        context['widget']['attrs']['data-with-free-options'] = int(self.with_free_options)
        context['widget']['attrs']['data-free-options-placeholder'] = self.free_options_placeholder
        return context


def get_initial_choices_for_additional_approval_conditions(
    predefined_approval_conditions,
    cv_experiences_conditions: Dict[str, str],
):
    name_field = 'name_fr' if get_language() == settings.LANGUAGE_CODE_FR else 'name_en'
    choices = []

    # Predefined conditions
    for condition in predefined_approval_conditions:
        choices.append((condition.uuid, mark_safe(getattr(condition, name_field))))

    # Free conditions generated by the system
    for experience_uuid, experience_name in cv_experiences_conditions.items():
        choices.append((experience_uuid, _('Graduation of {program_name}').format(program_name=experience_name)))

    return choices


def get_diplomatic_post_initial_choices(diplomatic_post):
    """Return the unique initial choice for a diplomatic post."""
    if not diplomatic_post:
        return EMPTY_CHOICE

    return EMPTY_CHOICE + (
        (
            diplomatic_post.code,
            diplomatic_post.name_fr if get_language() == settings.LANGUAGE_CODE else diplomatic_post.name_en,
        ),
    )


def disable_unavailable_forms(forms_by_access: Dict[forms.Form, bool]):
    """
    Disable forms that are not available for the current user.
    :param forms_by_access: Association between the form and its availability.
    """
    for form, is_available in forms_by_access.items():
        if not is_available:
            for field in form.fields:
                form.fields[field].disabled = True


class NullBooleanSelectField(forms.NullBooleanField):
    def __init__(self, empty_label='', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.widget = forms.Select(
            choices=(
                ('', empty_label),
                ('true', _('Yes')),
                ('false', _('No')),
            )
        )


class AdmissionMainCampusChoiceField(MainCampusChoiceField):
    def label_from_instance(self, obj: Campus) -> str:
        return obj.name


class AdmissionHTMLCharField(forms.CharField):
    def clean(self, value):
        cleaned_value = super().clean(value)

        if cleaned_value:
            return html.unescape(cleaned_value)

        return cleaned_value
