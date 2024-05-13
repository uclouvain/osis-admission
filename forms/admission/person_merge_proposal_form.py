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
from datetime import datetime

from django.forms import HiddenInput
from django.utils.translation import gettext as _

from admission.forms.admission.person import AdmissionPersonForm, IdentificationType
from base.models.person import Person


class PersonMergeProposalForm(AdmissionPersonForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for exclude_fields in self._meta.exclude:
            self.fields.pop(exclude_fields)

        # some adjustments to initial form
        self.fields['middle_name'].help_text = None
        self.fields['country_of_citizenship'].required = True
        self.fields['last_registration_id'].label = _("Last registration id")
        self.fields['email'].label = _("Private email")

    def clean(self):
        last_registration_id = self.data.get('last_registration_id')

        data = super().clean()
        data['last_registration_id'] = last_registration_id

        id_type = self.data.get('identification_type')

        if not id_type and (self.data['passport_number'] or self.data['passport_expiry_date']):
            data['identification_type'] = IdentificationType.PASSPORT_NUMBER.name
            data['passport_number'] = self.data['passport_number']
            data['passport_expiry_date'] = self.data['passport_expiry_date']

        if not id_type and (self.data['national_number'] or self.data['id_card_number'] or self.data['id_card_expiry_date']):
            data['identification_type'] = IdentificationType.ID_CARD_NUMBER.name
            data['national_number'] = self.data['national_number']
            data['id_card_number'] = self.data['id_card_number']
            data['id_card_expiry_date'] = self.data['id_card_expiry_date']

        if data['identification_type'] == IdentificationType.PASSPORT_NUMBER.name:
            self.errors.pop('id_card_number', None)
            self.errors.pop('id_card_expiry_date', None)

        if data['identification_type'] == IdentificationType.ID_CARD_NUMBER.name:
            self.errors.pop('passport_number', None)
            self.errors.pop('passport_expiry_date', None)

        if data['identification_type'] == IdentificationType.ID_CARD_NUMBER.name and not all(
                [data['national_number'], data['id_card_number'], data['id_card_expiry_date']]
        ):
            for field in ['national_number', 'id_card_number', 'id_card_expiry_date']:
                if not data[field]:
                    self.add_error(field, "This field is required.")

        if data['identification_type'] == IdentificationType.PASSPORT_NUMBER.name and not all(
                [data['passport_number'], data['passport_expiry_date']]
        ):
            for field in ['passport_number', 'passport_expiry_date']:
                if not data[field]:
                    self.add_error(field, "This field is required.")

        if self.data['passport_expiry_date']:
            data['passport_expiry_date'] = self._to_YYYYMMDD(self.data['passport_expiry_date'])

        if self.data['id_card_expiry_date']:
            data['id_card_expiry_date'] = self._to_YYYYMMDD(self.data['id_card_expiry_date'])

        return data

    def _to_YYYYMMDD(self, date_str):
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d") if date_str else None


    class Meta:
        model = Person
        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'national_number',
            'last_registration_id',
            'gender',
            'birth_date',
            'email',
            'civil_state',
            'birth_place',
            'country_of_citizenship',
            'id_card_number',
            'passport_number',
            'id_card_expiry_date',
            'passport_expiry_date',
        ]
        exclude = [
            'birth_country',
            'birth_year',
            'sex',
            'language',
            'id_photo',
            'id_card',
            'passport',
            'last_registration_year',
            'has_national_number',
            'unknown_birth_date',
            'already_registered',
            'identification_type',
        ]
        force_translations = [
            _('Civil state'),
            _('Middle name'),
            _('Country of citizenship name'),
            _('National number'),
            _('Id card number'),
            _('Id card expiry date'),
        ]
