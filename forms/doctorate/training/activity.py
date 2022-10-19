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
from datetime import date
from functools import partial
from typing import List, Tuple

import dal.forward
from dal import autocomplete
from django import forms
from django.utils.translation import get_language, gettext_lazy as _, pgettext_lazy

from admission.contrib.models.cdd_config import CddConfiguration
from admission.contrib.models.doctoral_training import Activity
from admission.ddd.parcours_doctoral.formation.domain.model.enums import (
    CategorieActivite,
    ChoixComiteSelection,
    ChoixTypeEpreuve,
    ContexteFormation,
)
from admission.forms import SelectOrOtherField
from base.forms.utils.datefield import DatePickerInput
from base.models.academic_year import AcademicYear
from base.models.learning_unit_year import LearningUnitYear

__all__ = [
    "ConfigurableActivityTypeField",
    "AcademicYearField",
    "ConferenceForm",
    "ConferenceCommunicationForm",
    "ConferencePublicationForm",
    "CommunicationForm",
    "PublicationForm",
    "ResidencyForm",
    "ResidencyCommunicationForm",
    "ServiceForm",
    "SeminarForm",
    "SeminarCommunicationForm",
    "ValorisationForm",
    "CourseForm",
    "PaperForm",
    "ComplementaryCourseForm",
    "UclCourseForm",
]

INSTITUTION_UCL = "UCLouvain"


def get_cdd_config(cdd_id) -> CddConfiguration:
    return CddConfiguration.objects.get_or_create(cdd_id=cdd_id)[0]


def get_category_labels(cdd_id, lang_code: str = None) -> List[Tuple[str, str]]:
    lang_code = lang_code or get_language()
    original_constants = dict(CategorieActivite.choices()).keys()
    return list(zip(original_constants, get_cdd_config(cdd_id).category_labels[lang_code]))


class ConfigurableActivityTypeField(SelectOrOtherField):
    select_class = forms.CharField

    def __init__(self, source: str = '', *args, **kwargs):
        self.source = source
        super().__init__(*args, **kwargs)

    def get_bound_field(self, form, field_name):
        # Update radio choices from CDD configuration
        config = get_cdd_config(form.cdd_id)
        values = getattr(config, self.source, {}).get(get_language(), [])
        self.widget.widgets[0].choices = list(zip(values, values)) + [('other', _("Other"))]
        return super().get_bound_field(form, field_name)


class BooleanRadioSelect(forms.RadioSelect):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # Override to explicitly set initial selected option to 'False' value
        if value is None:
            context['widget']['optgroups'][0][1][0]['selected'] = True
            context['widget']['optgroups'][0][1][0]['attrs']['checked'] = True
        return context


class AcademicYearField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', _("Academic year"))
        if kwargs.pop('future_only', False):
            kwargs.setdefault('queryset', AcademicYear.objects.filter(year__gte=date.today().year).order_by('-year'))
        else:
            kwargs.setdefault('queryset', AcademicYear.objects.order_by('-year'))
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj: AcademicYear) -> str:
        return f"{obj.year}-{obj.year + 1}"


CustomDatePickerInput = partial(
    DatePickerInput,
    attrs={
        'placeholder': _("dd/mm/yyyy"),
        'autocomplete': 'off',
        **DatePickerInput.defaut_attrs,
    },
)

IsOnlineField = partial(
    forms.BooleanField,
    label=_("Online or in person"),
    initial=False,
    required=False,
    widget=BooleanRadioSelect(choices=((False, _("In person")), (True, _("Online")))),
)


class ActivityFormMixin(forms.BaseForm):
    def __init__(self, admission, *args, **kwargs) -> None:
        self.cdd_id = admission.doctorate.management_entity_id
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get('start_date')
            and cleaned_data.get('end_date')
            and cleaned_data.get('start_date') > cleaned_data.get('end_date')
        ):
            self.add_error('start_date', forms.ValidationError(_("The start date can't be later than the end date")))
        return cleaned_data

    class Media:
        js = [
            # Dates
            'js/moment.min.js',
            'js/locales/moment-fr.js',
            'js/bootstrap-datetimepicker.min.js',
            'js/dates-input.js',
        ]


class ConferenceForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/conference.html"
    type = ConfigurableActivityTypeField('conference_types', label=_("Type of activity"))
    is_online = IsOnlineField()

    class Meta:
        model = Activity
        fields = [
            'type',
            'ects',
            'title',
            'start_date',
            'end_date',
            'participating_days',
            'is_online',
            'website',
            'country',
            'city',
            'organizing_institution',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Name of the manifestation"),
            'website': _("Event website"),
            'ects': _("ECTS for the participation"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'end_date': CustomDatePickerInput(),
            'country': autocomplete.ListSelect2(url="country-autocomplete"),
        }
        help_texts = {
            'title': _("Name in the language of the manifestation"),
        }


class ConferenceCommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/conference_communication.html"
    type = SelectOrOtherField(
        label=_("Type of communication"),
        choices=[
            _("Oral expose"),
            _("Poster"),
        ],
    )

    def clean(self):
        data = super().clean()
        if data.get('committee') != ChoixComiteSelection.YES.name and data.get('acceptation_proof'):
            data['acceptation_proof'] = []
        return data

    class Meta:
        model = Activity
        fields = [
            'type',
            'ects',
            'title',
            'summary',
            'committee',
            'acceptation_proof',
            'dial_reference',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the communication"),
            'summary': _("Summary of the communication"),
            'acceptation_proof': _("Proof of acceptation by the committee"),
            'participating_proof': _("Attestation of the communication"),
            'committee': _("Selection committee"),
        }


class ConferencePublicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/conference_publication.html"
    type = ConfigurableActivityTypeField('conference_publication_types', label=_("Type of publication"))

    class Meta:
        model = Activity
        fields = [
            'type',
            'ects',
            'title',
            'start_date',
            'publication_status',
            'authors',
            'role',
            'keywords',
            'summary',
            'committee',
            'journal',
            'dial_reference',
            'acceptation_proof',
            'comment',
        ]
        labels = {
            'type': _("Type of publication"),
            'title': _("Title of the publication"),
            'start_date': _("Date of the publication"),
            'committee': _("Selection committee"),
            'summary': pgettext_lazy("paper summary", "Summary"),
            'acceptation_proof': _("Proof of acceptation or publication"),
            'publication_status': _("Publication status"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
        }


class CommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/communication.html"
    type = ConfigurableActivityTypeField('communication_types', label=_("Type of activity"))
    subtype = SelectOrOtherField(
        label=_("Type of communication"),
        choices=[
            _("Oral expose"),
            _("Poster"),
        ],
    )
    subtitle = forms.CharField(
        label=_("Title of the communication"),
        max_length=200,
        required=False,
    )
    is_online = IsOnlineField()

    def clean(self):
        data = super().clean()
        if data.get('committee') != ChoixComiteSelection.YES.name and data.get('acceptation_proof'):
            data['acceptation_proof'] = []
        return data

    class Meta:
        model = Activity
        fields = [
            'type',
            'subtype',
            'title',
            'start_date',
            'is_online',
            'country',
            'city',
            'organizing_institution',
            'website',
            'subtitle',
            'summary',
            'committee',
            'acceptation_proof',
            'participating_proof',
            'dial_reference',
            'ects',
            'comment',
        ]
        labels = {
            'title': _("Name of the activity"),
            'start_date': _("Date of the activity"),
            'website': _("Event website"),
            'acceptation_proof': _("Proof of acceptation by the committee"),
            'participating_proof': _("Communication attestation"),
            'committee': _("Selection committee"),
            'summary': _("Summary of the communication"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'country': autocomplete.ListSelect2(url="country-autocomplete"),
        }


class PublicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/publication.html"
    type = ConfigurableActivityTypeField('publication_types', label=_("Type of publication"))

    class Meta:
        model = Activity
        fields = [
            'type',
            'title',
            'start_date',
            'authors',
            'role',
            'keywords',
            'summary',
            'journal',
            'publication_status',
            'dial_reference',
            'ects',
            'acceptation_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the publication"),
            'start_date': _("Date of the publication"),
            'publication_status': _("Publication status"),
            'acceptation_proof': _("Proof of publication"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
        }


class ResidencyForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/residency.html"
    type = ConfigurableActivityTypeField('residency_types', label=_("Type of activity"))

    class Meta:
        model = Activity
        fields = [
            'type',
            'ects',
            'subtitle',
            'start_date',
            'end_date',
            'country',
            'city',
            'participating_proof',
            'comment',
        ]
        labels = {
            'subtitle': _("Description of the activity"),
            'participating_proof': _("Proof (if needed)"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'end_date': CustomDatePickerInput(),
            'country': autocomplete.ListSelect2(url="country-autocomplete"),
        }


class ResidencyCommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/residency_communication.html"
    type = SelectOrOtherField(choices=[_("Research seminar")], label=_("Type of activity"))
    subtype = SelectOrOtherField(
        choices=[_("Oral expose")],
        label=_("Type of communication"),
        required=False,
    )
    subtitle = forms.CharField(label=_("Title of the communication"), max_length=200, required=False)
    is_online = IsOnlineField()

    class Meta:
        model = Activity
        fields = [
            'type',
            'subtype',
            'title',
            'start_date',
            'is_online',
            'organizing_institution',
            'website',
            'subtitle',
            'ects',
            'summary',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Name of the event"),
            'start_date': _("Date of the activity"),
            'website': _("Event website"),
            'summary': _("Summary of the communication"),
            'participating_proof': _("Attestation of the communication"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
        }


class ServiceForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/service.html"
    type = ConfigurableActivityTypeField("service_types", label=_("Type of activity"))

    class Meta:
        model = Activity
        fields = [
            'type',
            'title',
            'start_date',
            'end_date',
            'organizing_institution',
            'hour_volume',
            'participating_proof',
            'ects',
            'comment',
        ]
        labels = {
            'title': _("Name of the activity"),
            'subtitle': _("Description of the activity"),
            'participating_proof': _("Proof (if needed)"),
            'organizing_institution': _("Institution"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'end_date': CustomDatePickerInput(),
        }


class SeminarForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/seminar.html"
    type = ConfigurableActivityTypeField("seminar_types", label=_("Type of activity"))

    class Meta:
        model = Activity
        fields = [
            'type',
            'title',
            'start_date',
            'end_date',
            'hour_volume',
            'participating_proof',
            'ects',
        ]
        labels = {
            'title': _("Name of the activity"),
            'participating_proof': _("Proof of participation for the whole activity"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'end_date': CustomDatePickerInput(),
        }


class SeminarCommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/seminar_communication.html"
    is_online = IsOnlineField()

    class Meta:
        model = Activity
        fields = [
            'title',
            'start_date',
            'is_online',
            'country',
            'city',
            'organizing_institution',
            'website',
            'authors',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the communication"),
            'start_date': _("Date of presentation"),
            'authors': _("Speaker"),
            'participating_proof': _("Certificate of participation in the presentation"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'country': autocomplete.ListSelect2(url="country-autocomplete"),
        }


class ValorisationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/valorisation.html"

    class Meta:
        model = Activity
        fields = [
            'title',
            'subtitle',
            'summary',
            'participating_proof',
            'ects',
            'comment',
        ]
        labels = {
            'title': _("Title"),
            'subtitle': _("Description"),
            'summary': _("Detailed curriculum vitae"),
            'participating_proof': _("Proof"),
        }


class CourseForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/course.html"
    type = ConfigurableActivityTypeField("course_types", label=_("Type of activity"))
    subtitle = forms.CharField(
        label=_("Course code (if needed)"),
        max_length=200,
        required=False,
    )
    organizing_institution = SelectOrOtherField(choices=[INSTITUTION_UCL], label=_("Institution"))
    academic_year = AcademicYearField(widget=autocomplete.ListSelect2(), required=False)
    is_online = forms.BooleanField(
        label=_("Course with evaluation"),  # Yes, its another meaning, but we spare a db field
        initial=False,
        required=False,
        widget=BooleanRadioSelect(choices=((False, _("No")), (True, _("Yes")))),
    )

    def __init__(self, admission, *args, **kwargs) -> None:
        super().__init__(admission, *args, **kwargs)
        # Convert from dates to year if UCLouvain
        if (
            self.instance
            and self.instance.organizing_institution == INSTITUTION_UCL
            and self.instance.start_date
            and self.instance.end_date
        ):
            self.fields['academic_year'].initial = AcademicYear.objects.get(
                start_date=self.instance.start_date,
                end_date=self.instance.end_date,
            )

    def clean(self):
        cleaned_data = super().clean()
        # Convert from academic year to dates if UCLouvain
        if cleaned_data.get('organizing_institution') == INSTITUTION_UCL and cleaned_data.get('academic_year'):
            cleaned_data['start_date'] = cleaned_data['academic_year'].start_date
            cleaned_data['end_date'] = cleaned_data['academic_year'].end_date
        cleaned_data.pop('academic_year', None)
        return cleaned_data

    class Meta:
        model = Activity
        fields = [
            'type',
            'title',
            'subtitle',
            'organizing_institution',
            'start_date',
            'end_date',
            'hour_volume',
            'authors',
            'is_online',
            'ects',
            'participating_proof',
            'comment',
        ]
        widgets = {
            'start_date': CustomDatePickerInput(),
            'end_date': CustomDatePickerInput(),
        }
        labels = {
            'title': _("Name of the activity"),
            'authors': _("Course owner if applicable"),
            'participating_proof': _("Proof of participation or success"),
        }


class ComplementaryCourseForm(CourseForm):
    """Course form for complementary training"""

    type = ConfigurableActivityTypeField("complementary_course_types", label=_("Type of activity"))

    def __init__(self, admission, *args, **kwargs):
        super().__init__(admission, *args, **kwargs)
        self.instance.context = ContexteFormation.COMPLEMENTARY_TRAINING.name


class PaperForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/paper.html"
    type = forms.ChoiceField(label=_("Type of paper"), choices=ChoixTypeEpreuve.choices())

    class Meta:
        model = Activity
        fields = [
            'type',
            'ects',
            'comment',
        ]


class UclCourseForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/ucl_course.html"
    academic_year = AcademicYearField(to_field_name='year', widget=autocomplete.ListSelect2(), future_only=True)
    learning_unit_year = forms.CharField(
        label=_("Learning unit"),
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:learning_unit_years',
            attrs={
                'data-html': True,
                'data-minimum-input-length': 2,
                'data-placeholder': _('Search for an EU code (outside the EU of the form)'),
            },
            forward=[dal.forward.Field("academic_year", "annee")],
        ),
    )

    def __init__(self, admission, *args, **kwargs):
        super().__init__(admission, *args, **kwargs)
        self.fields['learning_unit_year'].required = True
        if self.initial.get('learning_unit_year'):
            learning_unit_year = LearningUnitYear.objects.get(pk=self.initial['learning_unit_year'])
            self.initial['academic_year'] = learning_unit_year.academic_year.year
            self.fields['learning_unit_year'].widget.choices = [
                (learning_unit_year.pk, f"{learning_unit_year.acronym} - {learning_unit_year.complete_title_i18n}"),
            ]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('academic_year') and cleaned_data.get('learning_unit_year'):
            cleaned_data['learning_unit_year'] = LearningUnitYear.objects.get(
                academic_year=cleaned_data['academic_year'],
                acronym=cleaned_data['learning_unit_year'],
            )
        return cleaned_data

    class Meta:
        model = Activity
        fields = [
            'context',
            'learning_unit_year',
        ]
