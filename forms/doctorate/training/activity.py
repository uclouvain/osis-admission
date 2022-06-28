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
from typing import List, Optional

from django import forms
from django.utils.translation import get_language, gettext_lazy as _, pgettext_lazy

from admission.contrib.models.cdd_config import CddConfiguration
from admission.contrib.models.doctoral_training import Activity
from base.forms.utils.datefield import DatePickerInput

__all__ = [
    "ConfigurableActivityTypeWidget",
    "ConfigurableActivityTypeField",
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
]


class ConfigurableActivityTypeWidget(forms.MultiWidget):
    """Form widget to handle a configurable (from CDDConfiguration) list of choices, or other"""

    template_name = 'admission/doctorate/forms/activity_type_widget.html'
    media = forms.Media(js=['js/dependsOn.min.js'])

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


class ConfigurableActivityTypeField(forms.MultiValueField):
    """Form field to handle a configurable (from CDD) list of choices, or other"""

    widget = ConfigurableActivityTypeWidget

    def __init__(self, source: str = '', choices: Optional[List[str]] = None, *args, **kwargs):
        if not source and not choices:  # pragma: no cover
            raise ValueError("At least source or choices must be specified")
        self.source = source
        self.choices = choices
        fields = [forms.CharField(required=False), forms.CharField(required=False)]
        super().__init__(fields, require_all_fields=False, *args, **kwargs)

    def validate(self, value):
        # We do require all fields, but we want to check the final (compressed value)
        super(forms.MultiValueField, self).validate(value)

    def get_bound_field(self, form, field_name):
        values = self.choices or []
        if self.source:
            # Update radio choices from CDD configuration
            config = CddConfiguration.objects.get_or_create(cdd_id=form.cdd_id)[0]
            values = getattr(config, self.source, {}).get(get_language(), [])
        self.widget.widgets[0].choices = list(zip(values, values)) + [('other', _("Other"))]
        return super().get_bound_field(form, field_name)

    def compress(self, data_list):
        # On save, take the other value if "other" is chosen
        radio, other = data_list
        return radio if radio != "other" else other


class ActivityFormMixin:
    def __init__(self, admission, *args, **kwargs) -> None:
        self.cdd_id = admission.doctorate.management_entity_id
        super().__init__(*args, **kwargs)

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
    type = ConfigurableActivityTypeField(
        label=_("Type of activity"),
        choices=[
            _("National conference"),
            _("International conference"),
        ],
    )

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
            'title': _("Name of the event"),
        }
        widgets = {
            'is_online': forms.RadioSelect(choices=((False, _("In person")), (True, _("Online")))),
            'start_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
            'end_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
        }


class ConferenceCommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/conference_communication.html"
    type = ConfigurableActivityTypeField(
        label=_("Type of communication"),
        choices=[
            _("Poster"),
            _("Oral communication"),
        ],
    )

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
    type = ConfigurableActivityTypeField(
        label=_("Type of publication"),
        choices=[
            _("Article published in a peer-reviewed journal"),
            _("Article published in a non-refereed journal"),
            _("Book chapter"),
            _("Monograph"),
            _("Edition or co-publication"),
            _("Working paper"),
            _("Extended abstract"),
        ],
    )

    class Meta:
        model = Activity
        fields = [
            'type',
            'ects',
            'title',
            'authors',
            'role',
            'keywords',
            'summary',
            'committee',
            'journal',
            'dial_reference',
            'participating_proof',
            'comment',
        ]
        labels = {
            'type': _("Type of publication"),
            'title': _("Title of the publication"),
            'committee': _("Selection committee"),
            'summary': pgettext_lazy("paper summary", "Summary"),
            'participating_proof': _("Proof of acceptation or publication"),
        }


class CommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/communication.html"
    type = ConfigurableActivityTypeField(
        label=_("Type of activity"),
        choices=[
            _("Research seminar"),
            _("PhD students' day"),
        ],
    )
    subtype = ConfigurableActivityTypeField(
        label=_("Type of communication"),
        choices=[
            _("Oral exposé"),
            _("Poster"),
        ],
    )
    subtitle = forms.CharField(label=_("Title of the communication"), max_length=200)

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
            'acceptation_proof': _("Proof of acceptation by the committee"),
            'participating_proof': _("Communication attestation"),
        }
        widgets = {
            'is_online': forms.RadioSelect(choices=((False, _("In person")), (True, _("Online")))),
            'start_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
        }


class PublicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/publication.html"
    type = ConfigurableActivityTypeField(
        label=_("Type of publication"),
        choices=[
            _("Article for a peer-reviewed journal"),
            _("Article for a non-refereed journal"),
            _("Publication in an international scientific journal with peer review"),
            _("Book chapter"),
            _("Monograph"),
            _("Edition or co-publication"),
            _("Patent"),
            _("Review of a scientific work"),
            _("Working paper"),
        ],
    )

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
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the publication"),
            'start_date': _("Date of the publication"),
            'publication_status': _("Publication status"),
        }
        widgets = {
            'start_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
        }


class ResidencyForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/residency.html"
    type = ConfigurableActivityTypeField(
        label=_("Type of activity"),
        choices=[
            _("Research residency (excluding cotutelle)"),
            _("Documentary research residency"),
        ],
    )

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
            'start_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
            'end_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
        }


class ResidencyCommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/residency_communication.html"
    type = ConfigurableActivityTypeField(label=_("Type of activity"), choices=[_("Research seminar")])
    subtype = ConfigurableActivityTypeField(label=_("Type of communication"), choices=[_("Oral exposé")])
    subtitle = forms.CharField(label=_("Title of the communication"), max_length=200)

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
        }
        widgets = {
            'is_online': forms.RadioSelect(choices=((False, _("In person")), (True, _("Online")))),
            'start_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
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
            'subtitle': _("Description of the activity"),
            'participating_proof': _("Proof (if needed)"),
        }
        widgets = {
            'start_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
            'end_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
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
            'participating_proof': _("Proof of participation for the whole activity"),
        }
        widgets = {
            'start_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
            'end_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
        }


class SeminarCommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "admission/doctorate/forms/training/seminar_communication.html"

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
            'is_online': forms.RadioSelect(choices=((False, _("In person")), (True, _("Online")))),
            'start_date': DatePickerInput(attrs={'placeholder': _("dd/mm/yyyy"), **DatePickerInput.defaut_attrs}),
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
        ]
        labels = {
            'title': _("Title"),
            'subtitle': _("Description"),
            'summary': _("Detailed curriculum vitae"),
            'participating_proof': _("Proof"),
        }
