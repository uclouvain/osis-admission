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
import re

from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _, ngettext

from admission.constants import DEFAULT_PAGINATOR_SIZE
from admission.contrib.models import Scholarship
from admission.ddd.admission.enums import TypeBourse
from admission.ddd.admission.enums.statut import CHOIX_STATUT_TOUTE_PROPOSITION
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.forms import ALL_EMPTY_CHOICE, get_academic_year_choices
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.forms.widgets import Select2MultipleCheckboxesWidget
from base.models.academic_year import current_academic_year
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_types import TrainingType
from base.templatetags.pagination import PAGINATOR_SIZE_LIST
from education_group.forms.fields import MainCampusChoiceField

REGEX_REFERENCE = r'\d{3}\.\d{3}$'


class AllAdmissionsFilterForm(forms.Form):
    annee_academique = forms.TypedChoiceField(
        label=_('Year'),
        coerce=int,
    )

    numero = forms.RegexField(
        label=_('Application numero'),
        regex=re.compile(REGEX_REFERENCE),
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'L-ESPO22-001.234',
            },
        ),
    )

    noma = forms.RegexField(
        required=False,
        label=_('Noma'),
        regex=re.compile(r'^\d{8}$'),
        widget=forms.TextInput(
            attrs={
                "data-mask": "00000000",
            },
        ),
    )

    matricule_candidat = forms.CharField(
        label=_('Last name / First name / E-mail'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:candidates",
            attrs={
                'data-minimum-input-length': 3,
            },
        ),
    )

    etat = forms.ChoiceField(
        choices=[ALL_EMPTY_CHOICE[0]] + CHOIX_STATUT_TOUTE_PROPOSITION,
        label=_('Application status'),
        required=False,
    )

    type = forms.ChoiceField(
        choices=ALL_EMPTY_CHOICE + TypeDemande.choices(),
        label=_('Application type'),
        required=False,
    )

    site_inscription = MainCampusChoiceField(
        empty_label=_('All'),
        label=_('Enrolment campus'),
        queryset=None,
        required=False,
        to_field_name='uuid',
    )

    entites = forms.CharField(
        label=_('Entities'),
        required=False,
        widget=autocomplete.TagSelect2(),
    )

    types_formation = forms.MultipleChoiceField(
        choices=[
            (key, TrainingType.get_value(key))
            for key in AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE
        ],
        label=_('Training type'),
        required=False,
        widget=Select2MultipleCheckboxesWidget(),
    )

    formation = forms.CharField(
        label=_('Training'),
        required=False,
    )

    bourse_internationale = forms.ModelChoiceField(
        label=_('International scholarship'),
        empty_label=_('All'),
        queryset=Scholarship.objects.filter(
            type__in=[
                TypeBourse.BOURSE_INTERNATIONALE_DOCTORAT.name,
                TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name,
            ]
        ).order_by('short_name'),
        required=False,
        to_field_name='uuid',
    )

    bourse_erasmus_mundus = forms.ModelChoiceField(
        label=_('Erasmus Mundus'),
        empty_label=_('All'),
        queryset=Scholarship.objects.filter(type=TypeBourse.ERASMUS_MUNDUS.name).order_by('short_name'),
        required=False,
        to_field_name='uuid',
    )

    bourse_double_diplomation = forms.ModelChoiceField(
        label=_('Double degree scholarship'),
        empty_label=_('All'),
        queryset=Scholarship.objects.filter(type=TypeBourse.DOUBLE_TRIPLE_DIPLOMATION.name).order_by('short_name'),
        required=False,
        to_field_name='uuid',
    )

    taille_page = forms.TypedChoiceField(
        label=_("Page size"),
        choices=((size, size) for size in PAGINATOR_SIZE_LIST),
        widget=forms.Select(attrs={'form': 'search_form', 'autocomplete': 'off'}),
        help_text=_("items per page"),
        required=False,
        initial=DEFAULT_PAGINATOR_SIZE,
        coerce=int,
    )

    page = forms.IntegerField(
        label=_("Page"),
        widget=forms.HiddenInput(),
        required=False,
        initial=1,
    )

    def __init__(self, user, load_labels=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['annee_academique'].choices = get_academic_year_choices()
        self.fields['annee_academique'].initial = current_academic_year().year
        self.fields['types_formation'].initial = list(
            AnneeInscriptionFormationTranslator.GENERAL_EDUCATION_TYPES
            | AnneeInscriptionFormationTranslator.DOCTORATE_EDUCATION_TYPES
        )

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        return re.search(REGEX_REFERENCE, numero).group(0).replace('.', '') if numero else ''

    def clean_site_inscription(self):
        site_inscription = self.cleaned_data.get('site_inscription')
        return site_inscription.uuid if site_inscription else ''

    def clean_bourse_internationale(self):
        bourse_internationale = self.cleaned_data.get('bourse_internationale')
        return bourse_internationale.uuid if bourse_internationale else ''

    def clean_bourse_erasmus_mundus(self):
        bourse_erasmus_mundus = self.cleaned_data.get('bourse_erasmus_mundus')
        return bourse_erasmus_mundus.uuid if bourse_erasmus_mundus else ''

    def clean_bourse_double_diplomation(self):
        bourse_double_diplomation = self.cleaned_data.get('bourse_double_diplomation')
        return bourse_double_diplomation.uuid if bourse_double_diplomation else ''

    def clean_taille_page(self):
        return self.cleaned_data.get('taille_page') or self.fields['taille_page'].initial

    def clean_page(self):
        return self.cleaned_data.get('page') or self.fields['page'].initial

    def clean_entites(self):
        entities = self.cleaned_data.get('entites')
        if entities:
            entities = entities.split(',')
            existing_entities = set(
                EntityVersion.objects.filter(acronym__in=entities).values_list('acronym', flat=True)
            )
            not_existing_entities = [entity for entity in entities if entity not in existing_entities]
            if not_existing_entities:
                self.add_error(
                    'entites',
                    ngettext(
                        'Attention, the following entity doesn\'t exist at UCLouvain: %(entities)s',
                        'Attention, the following entities don\'t exist at UCLouvain: %(entities)s',
                        len(not_existing_entities),
                    )
                    % {'entities': ', '.join(not_existing_entities)},
                )
            return entities
        return []

    class Media:
        js = [
            # DependsOn
            'js/dependsOn.min.js',
            # Mask
            'js/jquery.mask.min.js',
        ]
