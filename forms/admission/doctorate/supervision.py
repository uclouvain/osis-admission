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
from dal import autocomplete
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from osis_document.contrib import FileUploadField

from admission.models.enums.actor_type import ActorType
from admission.utils import get_country_initial_choices
from base.forms.utils import EMPTY_CHOICE
from osis_profile import BE_ISO_CODE

ACTOR_EXTERNAL = "EXTERNAL"

EXTERNAL_FIELDS = [
    'prenom',
    'nom',
    'email',
    'institution',
    'ville',
    'pays',
    'langue',
]


class DoctorateAdmissionMemberSupervisionForm(forms.Form):
    prenom = forms.CharField(
        label=_("First name"),
        required=False,
        max_length=50,
    )
    nom = forms.CharField(
        label=_("Surname"),
        required=False,
        max_length=50,
    )
    email = forms.EmailField(
        label=pgettext_lazy("admission", "Email"),
        required=False,
        max_length=255,
    )
    est_docteur = forms.BooleanField(
        label=_("Holder of a PhD with thesis"),
        required=False,
        initial=True,
    )
    institution = forms.CharField(
        label=_("Institution"),
        required=False,
        max_length=255,
    )
    ville = forms.CharField(
        label=_("City"),
        required=False,
        max_length=255,
    )
    pays = forms.CharField(
        label=_("Country"),
        required=False,
        widget=autocomplete.ListSelect2(
            url="country-autocomplete",
            attrs={
                "data-html": True,
            },
        ),
        initial=BE_ISO_CODE,
    )
    langue = forms.ChoiceField(
        label=_("Contact language"),
        required=False,
        choices=EMPTY_CHOICE + tuple(settings.LANGUAGES),
        initial=settings.LANGUAGE_CODE,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pays'].widget.choices = get_country_initial_choices(
            self.data.get(self.add_prefix("pays"), self.initial.get("pays", self.fields['pays'].initial)),
        )

    def clean(self):
        data = super().clean()
        self.clean_external_fields(data)
        return data

    def clean_external_fields(self, data):
        all_external_fields_filled = all(data.get(field) for field in EXTERNAL_FIELDS)
        if not all_external_fields_filled:
            for field in EXTERNAL_FIELDS:
                if not data.get(field):
                    self.add_error(field, _("This field is required."))


class DoctorateAdmissionSupervisionForm(DoctorateAdmissionMemberSupervisionForm):
    type = forms.ChoiceField(
        label="",
        choices=ActorType.choices(),
        widget=forms.RadioSelect(),
        initial=ActorType.PROMOTER.name,
    )
    internal_external = forms.ChoiceField(
        label="",
        choices=(
            ("INTERNAL", _("Internal")),
            (ACTOR_EXTERNAL, _("External")),
        ),
        initial="INTERNAL",
        widget=forms.RadioSelect(),
    )
    person = forms.CharField(
        label=_("Search a person by surname"),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:person",
        ),
        required=False,
    )

    def clean(self):
        data = self.cleaned_data
        is_external = data.get('internal_external') == ACTOR_EXTERNAL
        if not is_external and not data.get('person'):
            self.add_error(None, _("You must reference a person in UCLouvain."))
        elif is_external:
            self.clean_external_fields(data)
        return data

    class Media:
        js = (
            'js/dependsOn.min.js',
            # Add osis-document script in case of approved-by-pdf documents
            'osis_document/osis-document.umd.min.js',
        )
        css = {'all': ('osis_document/osis-document.css',)}


class DoctorateAdmissionApprovalByPdfForm(forms.Form):
    uuid_membre = forms.CharField(
        widget=forms.HiddenInput,
        required=True,
    )
    pdf = FileUploadField(
        label=_("PDF file"),
        required=True,
        min_files=1,
        max_files=1,
        mimetypes=['application/pdf'],
    )
