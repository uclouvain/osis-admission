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
from django.core import validators
from django.utils.translation import gettext_lazy as _

from base.forms.utils import get_example_text, FIELD_REQUIRED_MESSAGE
from base.forms.utils.academic_year_field import AcademicYearModelChoiceField
from base.forms.utils.fields import RadioBooleanField
from osis_profile.forms.personne import PersonForm


class AdmissionPersonForm(PersonForm):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.initial['already_registered'] = True if self.initial.get('last_registration_year') else False

    def clean(self):
        data = super().clean()

        # Check the fields which are required if others are specified
        if data.get('already_registered'):
            if not data.get('last_registration_year'):
                self.add_error('last_registration_year', FIELD_REQUIRED_MESSAGE)
        else:
            data['last_registration_year'] = None
            data['last_registration_id'] = ''

    class Meta(PersonForm.Meta):
        fields = PersonForm.Meta.fields + [
            'last_registration_year',
            'last_registration_id',
        ]
        fields_to_init = PersonForm.Meta.fields_to_init + [
            'last_registration_year',
            'last_registration_id',
        ]
