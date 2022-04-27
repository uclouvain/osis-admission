# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from osis_document.contrib import FileUploadField

from base.forms.utils.datefield import DatePickerInput


class ConfirmationForm(forms.Form):
    date_limite = forms.DateField(
        label=_('Deadline for confirmation'),
        required=True,
        widget=DatePickerInput(
            attrs={
                'placeholder': _("dd/mm/yyyy"),
                **DatePickerInput.defaut_attrs,
            },
        ),
    )
    date = forms.DateField(
        label=_('Date of confirmation'),
        required=True,
        widget=DatePickerInput(
            attrs={
                'placeholder': _("dd/mm/yyyy"),
                **DatePickerInput.defaut_attrs,
            },
        ),
    )
    rapport_recherche = FileUploadField(
        label=_('Research report'),
        required=False,
        max_files=1,
    )
    proces_verbal_ca = FileUploadField(
        label=_('Report of the supervisory panel'),
        required=False,
        max_files=1,
    )
    avis_renouvellement_mandat_recherche = FileUploadField(
        label=_('Opinion on the renewal of the research mandate'),
        required=False,
        max_files=1,
    )

    def clean(self):
        cleaned_data = super().clean()

        # Check dates
        date = cleaned_data.get('date')
        deadline = cleaned_data.get('date_limite')

        if date and deadline and date > deadline:
            raise ValidationError(_('The date of the confirmation paper cannot be later than its deadline.'))

        return cleaned_data

    class Media:
        js = [
            # Dates
            'js/moment.min.js',
            'js/locales/moment-fr.js',
            'js/bootstrap-datetimepicker.min.js',
            'js/dates-input.js',
        ]
