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
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutProposition
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.forms.select2 import Select2MultipleWithCheckboxes
from base.models.academic_year import AcademicYear
from base.models.campus import Campus
from base.models.enums.education_group_types import TrainingType
from base.templatetags.pagination import PAGINATOR_SIZE_LIST

EMPTY_CHOICE_FILTER = (('', _("All")),)


class AllListFiltersForm(forms.Form):
    page_size = forms.ChoiceField(
        label=_("Page size"),
        choices=((size, size) for size in PAGINATOR_SIZE_LIST),
        widget=forms.Select(attrs={'form': 'search_form', 'autocomplete': 'off'}),
        help_text=_("items per page"),
    )

    # Basic filters
    annee = forms.ModelChoiceField(
        label=_("Year"),
        queryset=AcademicYear.objects.filter(year__gte=now().date().year),  # TODO date de bascule
        empty_label=_("All"),
    )
    reference = forms.CharField(
        label=_("N# demand"),
        widget=forms.TextInput({'placeholder': "L-LSM22-001.234"}),
    )
    noma = forms.CharField(
        label=_("NOMA"),
    )
    candidat = forms.CharField(
        label=_('Last name / First name / E-mail'),
        # TODO duplicate and remove NOMA
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:candidates",
            attrs={
                'data-minimum-input-length': 3,
            },
        ),
    )
    etat = forms.ChoiceField(
        label=_('State'),
        # TODO states for all contexts
        choices=EMPTY_CHOICE_FILTER + ChoixStatutProposition.choices(),
    )
    type_demande = forms.ChoiceField(
        label=_('Demand type'),
        choices=EMPTY_CHOICE_FILTER + TypeDemande.choices(),
    )
    site = forms.ModelChoiceField(
        label=_('Site'),
        queryset=Campus.objects.filter(organization__name="UCLouvain").distinct(),
        empty_label=_("All"),
    )
    entite = forms.CharField(
        label=_('Entity'),
        widget=autocomplete.TagSelect2(
            attrs={
                'data-minimum-input-length': 2,
            },
        ),
        # TODO notify on clean() when entity does not exist
    )
    types_formation = forms.MultipleChoiceField(
        label=_('Training type(s)'),
        choices=TrainingType.choices(),
        widget=Select2MultipleWithCheckboxes(
            attrs={
                "data-dropdown-parent-selector": '#search_form',
                "data-selection-template": _("{items} types selected"),
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].required = False

    class Media:
        js = [
            'js/jquery.mask.min.js',
        ]
