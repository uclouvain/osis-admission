# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
import re

from dal import autocomplete
from django import forms
from django.conf import settings
from django.utils.translation import get_language, gettext_lazy as _

from admission.auth.roles.cdd_manager import CddManager
from admission.contrib.models import EntityProxy, Scholarship
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import (
    ENTITY_CDE,
    ENTITY_CDSS,
    ENTITY_CLSM,
    SIGLE_SCIENCES,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    BourseRecherche,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD, ChoixStatutSIC
from admission.ddd.admission.enums.type_bourse import TypeBourse
from admission.forms import CustomDateInput, EMPTY_CHOICE
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.models.person import Person
from base.templatetags.pagination import PAGINATOR_SIZE_LIST
from reference.models.country import Country

MINIMUM_SELECTABLE_YEAR = 2004
MAXIMUM_SELECTABLE_YEAR = 2031


class BaseFilterForm(forms.Form):
    numero = forms.RegexField(
        label=_('Dossier numero'),
        regex=re.compile(r'^\d{3}\.\d{3}$'),
        required=False,
        widget=forms.TextInput(
            attrs={
                'data-mask': '000.000',
                'placeholder': '000.000',
            },
        ),
    )
    etat_cdd = forms.ChoiceField(
        choices=EMPTY_CHOICE + ChoixStatutCDD.choices(),
        label=_('CDD status'),
        required=False,
    )
    etat_sic = forms.ChoiceField(
        choices=EMPTY_CHOICE + ChoixStatutSIC.choices(),
        label=_('SIC status'),
        required=False,
    )
    matricule_candidat = forms.CharField(
        label=_('Last name / First name / E-mail / NOMA'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:candidates",
            attrs={
                'data-minimum-input-length': 3,
                'data-placeholder': _('Last name / First name / E-mail / NOMA'),
            },
        ),
    )
    nationalite = forms.CharField(
        label=_("Nationality"),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:countries",
            attrs={
                'data-placeholder': _('Country'),
            },
        ),
    )
    type = forms.ChoiceField(
        choices=EMPTY_CHOICE + ChoixTypeAdmission.choices(),
        label=_('Admission type'),
        required=False,
    )
    cotutelle = forms.NullBooleanField(
        label=_("Cotutelle"),
        required=False,
        widget=forms.Select(
            choices=(
                EMPTY_CHOICE[0],
                (True, _('Yes')),
                (False, _('No')),
            ),
        ),
    )
    date_pre_admission_debut = forms.DateField(
        disabled=True,
        label=_("From"),
        required=False,
        widget=CustomDateInput(),
    )
    date_pre_admission_fin = forms.DateField(
        disabled=True,
        label=_("To"),
        required=False,
        widget=CustomDateInput(),
    )
    date_admission_debut = forms.DateField(
        disabled=True,
        label=_("From"),
        required=False,
        widget=CustomDateInput(),
    )
    date_admission_fin = forms.DateField(
        disabled=True,
        label=_("To"),
        required=False,
        widget=CustomDateInput(),
    )
    annee_academique = forms.ChoiceField(
        label=_('Year'),
        required=False,
    )
    commission_proximite = forms.ChoiceField(
        label=_('Proximity commission'),
        required=False,
    )
    cdds = forms.MultipleChoiceField(
        label=_('CDDs'),
        required=False,
        widget=autocomplete.Select2Multiple(),
    )
    matricule_promoteur = forms.CharField(
        label=_('Promoter'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:promoters",
            attrs={
                'data-minimum-input-length': 3,
                'data-placeholder': _('Last name / First name / Global id'),
            },
        ),
    )
    sigles_formations = forms.MultipleChoiceField(
        label=_('Training'),
        required=False,
        widget=autocomplete.Select2Multiple(
            attrs={
                'data-placeholder': _('Acronym / Title'),
            },
        ),
    )
    type_financement = forms.ChoiceField(
        choices=EMPTY_CHOICE + ChoixTypeFinancement.choices(),
        label=_('Financing type'),
        required=False,
    )
    type_contrat_travail = forms.ChoiceField(
        label=_("Work contract type"),
        choices=EMPTY_CHOICE + ChoixTypeContratTravail.choices(),
        required=False,
    )
    bourse_recherche = forms.ChoiceField(
        label=_("Scholarship grant"),
        required=False,
    )
    page_size = forms.ChoiceField(
        label=_("Page size"),
        choices=((size, size) for size in PAGINATOR_SIZE_LIST),
        widget=forms.Select(attrs={'form': 'search_form', 'autocomplete': 'off'}),
        help_text=_("items per page"),
        required=False,
    )

    def get_doctorate_queryset(self):
        return EducationGroupYear.objects.filter(
            education_group_type__name=TrainingType.PHD.name,
        )

    def get_cdd_queryset(self):
        return EntityProxy.objects.filter(
            entityversion__entity_type=EntityType.DOCTORAL_COMMISSION.name,
        )

    def get_proximity_commission_choices(self):
        return [
            EMPTY_CHOICE[0],
            ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()],
            [ENTITY_CDSS, ChoixCommissionProximiteCDSS.choices()],
            [SIGLE_SCIENCES, ChoixSousDomaineSciences.choices()],
        ]

    def get_scholarship_choices(self):
        doctorate_scholarships = Scholarship.objects.filter(
            type=TypeBourse.BOURSE_INTERNATIONALE_DOCTORAT.name,
        ).order_by('short_name')

        return (
            [EMPTY_CHOICE[0]]
            + [(scholarship.uuid, scholarship.short_name) for scholarship in doctorate_scholarships]
            + [(BourseRecherche.OTHER.name, BourseRecherche.OTHER.value)]
        )

    def __init__(self, user, load_labels=False, **kwargs):
        super().__init__(**kwargs)

        self.user = user

        self.fields['bourse_recherche'].choices = self.get_scholarship_choices()

        self.cdd_acronyms = (
            # Initialize the CDDs field
            self.get_cdd_queryset()
            .with_acronym()
            .order_by('acronym')
            .values_list('acronym', flat=True)
        )

        self.fields['cdds'].choices = [(acronym, acronym) for acronym in self.cdd_acronyms]

        # Initialize the program field
        self.doctorates = (
            self.get_doctorate_queryset()
            .distinct('acronym')
            .values_list('acronym', 'title' if get_language() == settings.LANGUAGE_CODE else 'title_english')
            .order_by('acronym')
        )
        self.fields['sigles_formations'].choices = [
            (acronym, '{} - {}'.format(acronym, title)) for acronym, title in self.doctorates
        ]

        # Initialize the proximity commission field
        self.fields['commission_proximite'].choices = self.get_proximity_commission_choices()

        # Initialize the academic year field
        academic_years = AcademicYear.objects.min_max_years(
            min_year=MINIMUM_SELECTABLE_YEAR,
            max_year=MAXIMUM_SELECTABLE_YEAR,
        ).order_by('-year')

        self.fields['annee_academique'].choices = [EMPTY_CHOICE[0]] + [
            (academic_year.year, str(academic_year)) for academic_year in academic_years
        ]

        # Initialize the labels of the autocomplete fields
        if load_labels:
            nationality = self.data.get(self.add_prefix('nationalite'))
            if nationality:
                country = (
                    Country.objects.filter(iso_code=nationality)
                    .values_list('name' if get_language() == settings.LANGUAGE_CODE else 'name_end')
                    .first()
                )
                if country:
                    self.fields['nationalite'].widget.choices = ((nationality, country[0]),)

            candidate = self.data.get(self.add_prefix('matricule_candidat'))
            if candidate:
                person = Person.objects.values('last_name', 'first_name').filter(global_id=candidate).first()
                if person:
                    self.fields['matricule_candidat'].widget.choices = (
                        (candidate, '{}, {}'.format(person['last_name'], person['first_name'])),
                    )

            promoter = self.data.get(self.add_prefix('matricule_promoteur'))
            if promoter:
                person = Person.objects.values('last_name', 'first_name').filter(global_id=promoter).first()
                if person:
                    self.fields['matricule_promoteur'].widget.choices = (
                        (promoter, '{}, {}'.format(person['last_name'], person['first_name'])),
                    )

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        if numero != '':
            return int(numero.replace('.', ''))

    class Media:
        js = [
            # DependsOn
            'js/dependsOn.min.js',
            # Mask
            'js/jquery.mask.min.js',
        ]


class CddFilterForm(BaseFilterForm):
    def get_cdd_queryset(self):
        return super().get_cdd_queryset().filter(pk__in=self.managed_cdds)

    def get_doctorate_queryset(self):
        return super().get_doctorate_queryset().filter(management_entity_id__in=self.managed_cdds)

    def get_proximity_commission_choices(self):
        proximity_commission_choices = [EMPTY_CHOICE[0]]

        if ENTITY_CDE in self.cdd_acronyms or ENTITY_CLSM in self.cdd_acronyms:
            proximity_commission_choices.append(
                ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()]
            )

        if ENTITY_CDSS in self.cdd_acronyms:
            proximity_commission_choices.append([ENTITY_CDSS, ChoixCommissionProximiteCDSS.choices()])

        if SIGLE_SCIENCES in dict(self.doctorates):
            proximity_commission_choices.append([SIGLE_SCIENCES, ChoixSousDomaineSciences.choices()])

        return proximity_commission_choices

    def __init__(self, user, **kwargs):
        self.managed_cdds = CddManager.objects.filter(person=user.person).values('entity_id')

        super().__init__(user, **kwargs)

        # Hide the CDDs field if the user manages only one cdd
        if len(self.cdd_acronyms) <= 1:
            self.fields['cdds'].widget = forms.MultipleHiddenInput()

        # Hide the proximity commission field if there is only one choice
        if len(self.fields['commission_proximite'].choices) == 1:
            self.fields['commission_proximite'].widget = forms.HiddenInput()

    def clean_cdds(self):
        cdds = self.cleaned_data['cdds']
        if not cdds:
            cdds = self.cdd_acronyms
        return cdds
