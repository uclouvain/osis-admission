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
from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from admission.ddd.parcours_doctoral.jury.domain.model.enums import GenreMembre, TitreMembre
from admission.forms import AdmissionModelCountryChoiceField, EMPTY_CHOICE
from base.models.person import Person
from base.models.utils.utils import ChoiceEnum
from reference.models.country import Country


class JuryMembreForm(forms.Form):
    class InstitutionPrincipaleChoices(ChoiceEnum):
        UCL = _('UCLouvain')
        OTHER = _('Other')

    matricule = forms.CharField(
        label=_('Lookup somebody'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:jury-members",
            attrs={
                'data-minimum-input-length': 3,
                'data-placeholder': _('Last name / First name / Global id'),
            },
        ),
    )

    institution_principale = forms.ChoiceField(
        label=_("Main institute"),
        choices=InstitutionPrincipaleChoices.choices(),
        widget=forms.RadioSelect(),
        initial=InstitutionPrincipaleChoices.UCL.name,
        required=True,
    )

    institution = forms.CharField(
        label=_("Specify if other"),
        required=False,
    )

    autre_institution = forms.CharField(
        label=_("Other institute (if necessary)"),
        required=False,
    )

    pays = AdmissionModelCountryChoiceField(
        label=_('Country'),
        queryset=Country.objects.all(),
        required=False,
    )

    nom = forms.CharField(
        label=_("Last name"),
        required=False,
    )

    prenom = forms.CharField(
        label=_("First name"),
        required=False,
    )

    titre = forms.ChoiceField(
        label=pgettext_lazy("jury", "Title"),
        choices=TitreMembre.choices(),
        required=False,
    )

    justification_non_docteur = forms.CharField(
        label=_("Please justify why the member does not have a doctor title"),
        widget=forms.Textarea(),
        required=False,
    )

    genre = forms.ChoiceField(
        label=_("Gender"),
        choices=GenreMembre.choices(),
        required=False,
    )

    email = forms.EmailField(
        label=_("Email"),
        required=False,
    )

    class Media:
        js = [
            'js/dependsOn.min.js',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pays = self.initial.get('pays', None)
        if pays:
            self.fields['pays'].widget.choices = EMPTY_CHOICE + ((pays.id, str(pays)),)
        matricule = self.initial.get('matricule', None)
        if matricule:
            person = Person.objects.get(global_id=matricule)
            self.fields['matricule'].widget.choices = EMPTY_CHOICE + ((matricule, str(person)),)

    def clean(self):
        if 'institution_principale' in self.cleaned_data:
            del self.cleaned_data['institution_principale']
        return self.cleaned_data
