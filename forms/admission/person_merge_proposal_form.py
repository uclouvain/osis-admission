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
from django.forms import HiddenInput
from django.utils.translation import gettext as _

from admission.forms.admission.person import AdmissionPersonForm
from base.models.person import Person


class PersonMergeProposalForm(AdmissionPersonForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for exclude_fields in self._meta.exclude:
            self.fields.pop(exclude_fields)

        # some adjustments to initial form
        self.fields['middle_name'].help_text = None
        self.fields['country_of_citizenship'].required = True
        self.fields['identification_type'].required = False
        self.fields['identification_type'].widget = HiddenInput()

    class Meta:
        model = Person
        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'gender',
            'birth_date',
            'civil_state',
            'birth_place',
            'country_of_citizenship',
            'national_number',
            'id_card_number',
            'id_card_expiry_date',
            'passport_number',
            'last_registration_id',
            'identification_type',
        ]
        exclude = [
            'birth_country',
            'birth_year',
            'sex',
            'language',
            'id_photo',
            'id_card',
            'passport',
            'passport_expiry_date',
            'last_registration_year',
            'has_national_number',
            'unknown_birth_date',
            'already_registered',
        ]
        force_translations = [
            _('Civil state'),
            _('Middle name'),
            _('Country of citizenship name')
        ]
