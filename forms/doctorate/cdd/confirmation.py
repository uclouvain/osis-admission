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
    demande_renouvellement_bourse = FileUploadField(
        label=_('Thesis funding renewal'),
        required=False,
        max_files=1,
        help_text=_("Only for FNRS, FRIA and FRESH scholarship students"),
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
