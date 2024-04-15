# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django import forms
from django.conf import settings
from django.core import validators
from django.utils.translation import gettext_lazy as _

from admission.constants import IMAGE_MIME_TYPES
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixSexe, ChoixGenre
from admission.forms import (
    AdmissionModelCountryChoiceField,
    AdmissionModelForm,
    get_year_choices,
)
from admission.utils import force_title
from base.forms.utils import EMPTY_CHOICE, get_example_text, FIELD_REQUIRED_MESSAGE
from base.forms.utils.academic_year_field import AcademicYearModelChoiceField
from base.forms.utils.datefield import CustomDateInput
from base.forms.utils.fields import RadioBooleanField
from base.forms.utils.file_field import MaxOneFileUploadField
from base.models.enums.civil_state import CivilState
from base.models.person import Person
from base.models.utils.utils import ChoiceEnum
from osis_profile import BE_ISO_CODE
from reference.models.country import Country


class IdentificationType(ChoiceEnum):
    ID_CARD_NUMBER = _('Identity card number')
    PASSPORT_NUMBER = _('Passport number')


class AdmissionPersonForm(AdmissionModelForm):
    # Identification
    first_name = forms.CharField(
        required=False,
        label=_('First name'),
        widget=forms.TextInput(
            attrs={
                'placeholder': get_example_text('Maria'),
            },
        ),
    )

    middle_name = forms.CharField(
        required=False,
        label=_('Other given names'),
        help_text=_(
            "Please indicate your other given names in accordance with your identity document. "
            "If there are no other given names on your identity document, you do not need to enter anything."
        ),
        widget=forms.TextInput(
            attrs={
                'placeholder': get_example_text('Pierre, Paul, Jacques'),
            },
        ),
    )

    last_name = forms.CharField(
        required=False,
        label=_('Surname'),
        widget=forms.TextInput(
            attrs={
                'placeholder': get_example_text('Smith'),
            },
        ),
    )

    sex = forms.ChoiceField(
        label=_('Sex'),
        choices=EMPTY_CHOICE + ChoixSexe.choices(),
    )

    gender = forms.ChoiceField(
        label=_('Gender'),
        choices=EMPTY_CHOICE + ChoixGenre.choices(),
    )

    unknown_birth_date = forms.BooleanField(
        required=False,
        label=_('Unknown date of birth'),
    )

    birth_date = forms.DateField(
        required=False,
        label=_('Date of birth'),
        widget=CustomDateInput(),
    )

    birth_year = forms.TypedChoiceField(
        required=False,
        label=_('Year of birth'),
        coerce=int,
        widget=forms.Select,
    )

    civil_state = forms.ChoiceField(
        label=_('Civil status'),
        choices=EMPTY_CHOICE + CivilState.choices(),
    )

    birth_country = AdmissionModelCountryChoiceField(
        label=_('Country of birth'),
    )

    birth_place = forms.CharField(
        label=_('Place of birth'),
        widget=forms.TextInput(
            attrs={
                'placeholder': get_example_text('Louvain-la-Neuve'),
            },
        ),
    )

    country_of_citizenship = AdmissionModelCountryChoiceField(
        label=_('Country of citizenship'),
    )

    language = forms.ChoiceField(
        label=_('Contact language'),
        required=False,
        choices=settings.LANGUAGES,
        help_text=_('This choice will define the language of communication throughout your admission process.'),
    )

    # Proof of identity
    id_card = MaxOneFileUploadField(
        required=False,
        label=_('Identity card (both sides)'),
        max_files=2,
    )

    passport = MaxOneFileUploadField(
        required=False,
        label=_('Passport'),
        max_files=2,
    )

    id_card_expiry_date = forms.DateField(
        required=False,
        label=_('Identity card expiry date'),
        widget=CustomDateInput(),
    )

    passport_expiry_date = forms.DateField(
        required=False,
        label=_('Passport expiry date'),
        widget=CustomDateInput(),
    )

    has_national_number = RadioBooleanField(
        label=_('Do you have a Belgian National Register Number (NISS)?'),
        help_text=_(
            'The Belgian national register number (or NISS, Social Security Identification Number) is a '
            'number composed of 11 digits, the first 6 of which refer to the date of birth of the concerned '
            'person. This number is assigned to every person living in Belgium when they register with '
            'the municipality (or other official body). It can be found on the Belgian identity card or on the '
            'residence permit.'
        ),
    )

    identification_type = forms.ChoiceField(
        label=_('Please provide one of these two pieces of identification information:'),
        required=False,
        choices=IdentificationType.choices(),
        widget=forms.RadioSelect,
    )

    national_number = forms.CharField(
        required=False,
        label=_('Belgian national registry number (NISS)'),
        validators=[
            validators.RegexValidator(
                r'^(\d{2}[.-]?\d{2}[.-]?\d{2}[.-]?\d{3}[.-]?\d{2})$',
                message=_('The Belgian national register number must consist of 11 digits.'),
            ),
        ],
        widget=forms.TextInput(
            attrs={
                'data-mask': '00.00.00-000.00',
                'placeholder': get_example_text('85.07.30-001.33'),
            },
        ),
    )

    id_card_number = forms.CharField(
        required=False,
        label=_('Identity card number'),
    )

    passport_number = forms.CharField(
        required=False,
        label=_('Passport number'),
    )

    id_photo = MaxOneFileUploadField(
        required=False,
        label=_('Identification photo'),
        max_files=1,
        forced_mimetypes=IMAGE_MIME_TYPES,
        mimetypes=IMAGE_MIME_TYPES,
        with_cropping=True,
        cropping_options={'aspectRatio': 0.766},
    )

    # Already registered
    last_registration_year = AcademicYearModelChoiceField(
        required=False,
        label=_('What was the most recent year you were enrolled at UCLouvain?'),
        past_only=True,
    )

    already_registered = RadioBooleanField(
        required=False,
        label=_("Have you previously enrolled at UCLouvain?"),
    )

    last_registration_id = forms.CharField(
        required=False,
        label=_('What was your NOMA (matriculation number)?'),
        widget=forms.TextInput(
            attrs={
                'data-mask': '00000000',
                'placeholder': get_example_text('10581300'),
            },
        ),
        validators=[
            validators.RegexValidator(r'^[0-9]{8}$', _('The NOMA must contain 8 digits.')),
        ],
    )

    class Media:
        js = [
            'js/jquery.mask.min.js',
            'js/dependsOn.min.js',
            'admission/formatter.js',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.initial['already_registered'] = True if self.initial.get('last_registration_year') else False

        if self.initial.get('birth_year'):
            self.initial['unknown_birth_date'] = True

        birth_country = self.data.get(
            self.add_prefix('birth_country'),
            self.initial.get('birth_country'),
        )
        country_of_citizenship = self.data.get(
            self.add_prefix('country_of_citizenship'),
            self.initial.get('country_of_citizenship'),
        )

        countries = set()
        if birth_country:
            countries.add(birth_country)
        if country_of_citizenship:
            countries.add(country_of_citizenship)

        if countries:
            countries_qs = Country.objects.filter(pk__in=countries)
            self.fields['birth_country'].queryset = countries_qs
            self.fields['country_of_citizenship'].queryset = countries_qs

        if self.initial.get('id_card_number'):
            self.initial['identification_type'] = IdentificationType.ID_CARD_NUMBER.name
        elif self.initial.get('passport_number'):
            self.initial['identification_type'] = IdentificationType.PASSPORT_NUMBER.name
        else:
            self.initial['identification_type'] = ''

        if self.initial.get('national_number'):
            self.initial['has_national_number'] = True
        elif self.initial.get('identification_type'):
            self.initial['has_national_number'] = False

        self.fields['birth_year'].choices = get_year_choices()

    def clean(self):
        data = super().clean()

        # Check the fields which are required if others are specified
        if data.get('unknown_birth_date'):
            data['birth_date'] = None
            if not data.get('birth_year'):
                self.add_error('birth_year', FIELD_REQUIRED_MESSAGE)
        else:
            data['birth_year'] = None
            if not data.get('birth_date'):
                self.add_error('birth_date', FIELD_REQUIRED_MESSAGE)

        if data.get('already_registered'):
            if not data.get('last_registration_year'):
                self.add_error('last_registration_year', FIELD_REQUIRED_MESSAGE)
        else:
            data['last_registration_year'] = None
            data['last_registration_id'] = ''

        if not data.get('first_name') and not data.get('last_name'):
            self.add_error('first_name', _('This field is required if the surname is missing.'))
            self.add_error('last_name', _('This field is required if the first name is missing.'))

        is_belgian = data.get('country_of_citizenship') and data.get('country_of_citizenship').iso_code == BE_ISO_CODE

        if is_belgian or data.get('has_national_number'):
            data['id_card_number'] = ''
            data['passport_number'] = ''
            data['passport'] = []
            data['passport_expiry_date'] = None

            if not data.get('national_number'):
                self.add_error('national_number', FIELD_REQUIRED_MESSAGE)
            if not data.get('id_card_expiry_date'):
                self.add_error('id_card_expiry_date', FIELD_REQUIRED_MESSAGE)

        elif data.get('identification_type') == IdentificationType.ID_CARD_NUMBER.name:
            data['national_number'] = ''
            data['passport_number'] = ''
            data['passport'] = []
            data['passport_expiry_date'] = None

            if not data.get('id_card_number'):
                self.add_error('id_card_number', FIELD_REQUIRED_MESSAGE)
            if not data.get('id_card_expiry_date'):
                self.add_error('id_card_expiry_date', FIELD_REQUIRED_MESSAGE)

        elif data.get('identification_type') == IdentificationType.PASSPORT_NUMBER.name:
            data['national_number'] = ''
            data['id_card_number'] = ''
            data['id_card'] = []
            data['id_card_expiry_date'] = None

            if not data.get('passport_number'):
                self.add_error('passport_number', FIELD_REQUIRED_MESSAGE)
            if not data.get('passport_expiry_date'):
                self.add_error('passport_expiry_date', FIELD_REQUIRED_MESSAGE)

        else:
            data['national_number'] = ''
            data['id_card_number'] = ''
            data['passport_number'] = ''
            data['passport'] = []
            data['id_card'] = []
            data['id_card_expiry_date'] = None
            data['passport_expiry_date'] = None

            self.add_error('identification_type', FIELD_REQUIRED_MESSAGE)

        # Lowercase the specified names
        for field in ['first_name', 'last_name', 'middle_name', 'birth_place']:
            if data.get(field):
                data[field] = force_title(data[field])

        return data

    class Meta:
        model = Person
        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'birth_date',
            'birth_year',
            'birth_country',
            'birth_place',
            'country_of_citizenship',
            'language',
            'sex',
            'gender',
            'civil_state',
            'id_photo',
            'id_card',
            'id_card_expiry_date',
            'passport',
            'passport_expiry_date',
            'national_number',
            'id_card_number',
            'passport_number',
            'last_registration_year',
            'last_registration_id',
            'has_national_number',
            'unknown_birth_date',
            'identification_type',
        ]
        fields_to_init = [
            'birth_year',
            'national_number',
            'identification_type',
            'id_card_number',
            'id_card',
            'passport',
            'passport_number',
            'last_registration_year',
            'last_registration_id',
        ]
