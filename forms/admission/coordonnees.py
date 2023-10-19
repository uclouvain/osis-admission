# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from dal import forward
from django import forms
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, pgettext_lazy as __, pgettext_lazy

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.ddd import BE_ISO_CODE
from admission.forms import (
    get_example_text,
    AdmissionModelCountryChoiceField,
    DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
    PhoneField,
    autocomplete,
)
from admission.utils import force_title
from base.models.person import Person
from reference.models.country import Country
from reference.models.zipcode import ZipCode


class AdmissionCoordonneesForm(forms.ModelForm):
    show_contact = forms.BooleanField(
        required=False,
        label=_('I would like to receive my mail at an address other than my legal address'),
    )

    private_email = forms.EmailField(
        label=__('admission', 'Personal email'),
        disabled=True,
        required=False,
    )

    phone_mobile = PhoneField(
        required=False,
        label=__('admission', 'Telephone (mobile)'),
        widget=forms.TextInput(
            attrs={
                'placeholder': get_example_text('+32 490 00 00 00'),
            },
        ),
    )

    emergency_contact_phone = PhoneField(
        required=False,
        label=_("Emergency contact (telephone number)"),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text('+32 490 00 00 00'),
            },
        ),
    )

    class Media:
        js = (
            'js/dependsOn.min.js',
            'admission/formatter.js',
        )

    class Meta:
        model = Person
        fields = [
            'private_email',
            'phone_mobile',
            'emergency_contact_phone',
        ]

    def __init__(self, show_contact, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tick the show contact checkbox only if there is data in contact
        self.fields['show_contact'].initial = show_contact


class AdmissionAddressForm(forms.ModelForm):
    street = forms.CharField(
        required=False,
        label=_('Street'),
        widget=forms.TextInput(
            attrs={
                'placeholder': get_example_text('Rue des ponts'),
            },
        ),
    )

    street_number = forms.CharField(
        required=False,
        label=pgettext_lazy('address', 'Number'),
    )

    postal_box = forms.CharField(
        required=False,
        label=_('Box'),
    )

    postal_code = forms.CharField(
        required=False,
        label=_('Postcode'),
    )

    city = forms.CharField(
        required=False,
        label=_('City'),
        help_text=get_example_text('Louvain-la-Neuve <del>louvain-la-neuve</del> <del>LOUVAIN-LA-NEUVE</del>'),
        widget=forms.TextInput(
            attrs={
                'placeholder': get_example_text('Louvain-la-Neuve'),
            },
        ),
    )

    country = AdmissionModelCountryChoiceField(
        required=False,
        label=_('Country'),
    )

    # Enable autocompletion only for Belgium postal codes
    be_postal_code = forms.CharField(
        required=False,
        label=_('Postcode'),
    )

    be_city = forms.CharField(
        required=False,
        label=_('City'),
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:cities',
            forward=(forward.Field('be_postal_code', 'postal_code'),),
            attrs=DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
        ),
    )

    class Meta:
        model = ZipCode
        fields = [
            'street',
            'street_number',
            'postal_box',
            'postal_code',
            'city',
            'country',
        ]

    def __init__(self, check_coordinates_fields=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.check_coordinates_fields = check_coordinates_fields

        country = self.data.get(self.add_prefix('country'), self.initial.get('country'))
        if country:
            country_qs = Country.objects.filter(pk=country)
            self.fields['country'].queryset = country_qs

            if country_qs and country_qs[0].iso_code == BE_ISO_CODE:
                self.initial['be_postal_code'] = self.initial.get('postal_code')
                self.initial['be_city'] = self.initial.get('city')

                be_city = self.data.get(self.add_prefix('be_city'), self.initial.get('be_city'))
                if be_city:
                    self.fields['be_city'].widget.choices = [(be_city, be_city)]

    def clean(self):
        cleaned_data = super().clean()

        mandatory_address_fields = [
            'street_number',
            'country',
            'street',
        ]

        # Either one of following data couple is mandatory :
        # (postal_code / city) or (be_postal_code / be_city)
        if cleaned_data.get('country') and cleaned_data.get('country').iso_code == BE_ISO_CODE:
            mandatory_address_fields.extend(['be_postal_code', 'be_city'])
        else:
            mandatory_address_fields.extend(['postal_code', 'city'])

        if self.check_coordinates_fields:
            for field in mandatory_address_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)

        # Lowercase the specified fields
        for field in ['street', 'city']:
            if cleaned_data.get(field):
                cleaned_data[field] = force_title(cleaned_data[field])

        return cleaned_data

    @cached_property
    def get_prepare_data(self):
        if not self.is_valid():
            return

        prepare_data = self.cleaned_data.copy()

        if prepare_data.get('country') and prepare_data.get('country').iso_code == BE_ISO_CODE:
            prepare_data['postal_code'] = prepare_data['be_postal_code']
            prepare_data['city'] = prepare_data['be_city']

        prepare_data.pop('be_postal_code')
        prepare_data.pop('be_city')

        return prepare_data
