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
from dal import autocomplete, forward
from django import forms
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from osis_document.contrib import FileUploadField

from admission.views.autocomplete.superior_institute import format_school_title
from base.forms.utils import FIELD_REQUIRED_MESSAGE, EMPTY_CHOICE
from base.models.entity_version import EntityVersion


class DoctorateAdmissionCotutelleForm(forms.Form):
    cotutelle = forms.ChoiceField(
        label=_("Would you like to carry out your thesis under joint supervision with another institution?"),
        help_text=_(
            "Your joint supervision information can be completed later."
            " Please input \"No\" if you don't have information yet."
        ),
        choices=[
            ('YES', _("Yes")),
            ('NO', _("No")),
        ],
        widget=forms.RadioSelect,
    )
    motivation = forms.CharField(
        label=_("Motivation for joint supervision"),
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        max_length=255,
    )

    institution_fwb = forms.NullBooleanField(
        label=_("Is it a Wallonia-Brussels Federation institution?"),
        required=False,
        widget=forms.RadioSelect(
            choices=(
                ('true', _('Yes')),
                ('false', _('No')),
            ),
        ),
    )
    institution = forms.CharField(
        empty_value=None,
        label=_('Institute'),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:superior-institute-uuid',
            forward=[
                forward.Field('institution_fwb', 'is_belgian'),
            ],
            attrs={
                'data-html': True,
            },
        ),
    )
    autre_institution = forms.BooleanField(
        label=_('Other institute'),
        required=False,
    )
    autre_institution_nom = forms.CharField(
        label=_('Institute name'),
        required=False,
        max_length=255,
    )
    autre_institution_adresse = forms.CharField(
        label=_('Institute address'),
        required=False,
        max_length=255,
    )

    demande_ouverture = FileUploadField(
        label=_("Joint supervision request"),
        required=False,
        max_files=1,
        help_text=_("Please look up the website of your domain doctoral committee on how to download the document."),
    )
    convention = FileUploadField(
        label=_("Joint supervision agreement"),
        required=False,
        max_files=1,
    )
    autres_documents = FileUploadField(
        label=_("Other documents relating to joint supervision"),
        required=False,
    )

    class Media:
        js = ('js/dependsOn.min.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['institution'].widget.choices = self.get_superior_institute_initial_choices(
            self.data.get(self.add_prefix('institution'), self.initial.get('institution'))
        )

    def get_superior_institute_initial_choices(self, institute_id):
        if not institute_id:
            return EMPTY_CHOICE

        institute = EntityVersion.objects.annotate(
            organization_uuid=F('entity__organization__uuid'),
            name=F('entity__organization__name'),
            city=F('entityversionaddress__city'),
            street=F('entityversionaddress__street'),
            street_number=F('entityversionaddress__street_number'),
            zipcode=F('entityversionaddress__postal_code'),
        ).get(organization_uuid=institute_id)

        return EMPTY_CHOICE + ((institute.organization_uuid, format_school_title(school=institute)),)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("cotutelle") == "YES":
            for field in ['motivation', 'demande_ouverture']:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
            if cleaned_data.get('institution_fwb') is None:
                self.add_error('institution_fwb', FIELD_REQUIRED_MESSAGE)
            if cleaned_data.get('autre_institution'):
                if not cleaned_data.get('autre_institution_nom'):
                    self.add_error('autre_institution_nom', FIELD_REQUIRED_MESSAGE)
                if not cleaned_data.get('autre_institution_adresse'):
                    self.add_error('autre_institution_adresse', FIELD_REQUIRED_MESSAGE)
            elif not cleaned_data.get('institution'):
                self.add_error('institution', FIELD_REQUIRED_MESSAGE)
        return cleaned_data
