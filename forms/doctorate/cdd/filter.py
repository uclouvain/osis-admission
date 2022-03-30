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
from django.utils.translation import gettext_lazy as _, get_language

from admission.auth.roles.cdd_manager import CddManager
from admission.contrib.models import EntityProxy
from admission.enums.yes_no import YesNo
from admission.ddd.projet_doctoral.preparation.domain.model._enums import (
    ChoixTypeAdmission,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixSousDomaineSciences,
    ChoixCommissionProximiteCDSS,
)
from admission.ddd.projet_doctoral.preparation.domain.model._financement import (
    ChoixTypeFinancement,
    ChoixTypeContratTravail,
    BourseRecherche,
)
from admission.ddd.projet_doctoral.preparation.domain.model.doctorat import (
    ENTITY_CDE,
    ENTITY_CLSM,
    SIGLE_SCIENCES,
    ENTITY_CDSS,
)
from admission.ddd.projet_doctoral.validation.domain.model._enums import ChoixStatutCDD, ChoixStatutSIC
from admission.forms import EMPTY_CHOICE
from base.forms.utils.datefield import DatePickerInput
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from base.templatetags.pagination import PAGINATOR_SIZE_LIST

MINIMUM_SELECTABLE_YEAR = 2004
MAXIMUM_SELECTABLE_YEAR = 2031


class FilterForm(forms.Form):
    numero = forms.RegexField(
        label=_('Dossier numero'),
        regex=re.compile(r'^\d{2}\-\d{6}$'),
        required=False,
        widget=forms.TextInput(
            attrs={
                'data-mask': '00-000000',
                'placeholder': '00-000000',
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
        label=_('Candidate'),
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
        widget=forms.Select(choices=EMPTY_CHOICE + YesNo.choices()),
    )
    date_pre_admission_debut = forms.DateField(
        disabled=True,
        label=_("From"),
        required=False,
        widget=DatePickerInput(
            attrs={
                'placeholder': _("dd/mm/yyyy"),
                **DatePickerInput.defaut_attrs,
            },
        ),
    )
    date_pre_admission_fin = forms.DateField(
        disabled=True,
        label=_("To"),
        required=False,
        widget=DatePickerInput(
            attrs={
                'placeholder': _("dd/mm/yyyy"),
                **DatePickerInput.defaut_attrs,
            },
        ),
    )
    date_admission_debut = forms.DateField(
        disabled=True,
        label=_("From"),
        required=False,
        widget=DatePickerInput(
            attrs={
                'placeholder': _("dd/mm/yyyy"),
                **DatePickerInput.defaut_attrs,
            },
        ),
    )
    date_admission_fin = forms.DateField(
        disabled=True,
        label=_("To"),
        required=False,
        widget=DatePickerInput(
            attrs={
                'placeholder': _("dd/mm/yyyy"),
                **DatePickerInput.defaut_attrs,
            },
        ),
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
        required=True,
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
        choices=EMPTY_CHOICE + BourseRecherche.choices(),
        required=False,
    )
    page_size = forms.ChoiceField(
        label=_("Page size"),
        choices=((size, size) for size in PAGINATOR_SIZE_LIST),
        widget=forms.Select(attrs={'form': 'search_form'}),
        help_text=_("items per page"),
    )

    def __init__(self, user, **kwargs):
        super().__init__(**kwargs)

        self.user = user

        # Get necessary data to initialize the form
        managed_cdds = CddManager.objects.filter(person=self.user.person).values('entity_id')

        cdd_acronyms = (
            EntityProxy.objects.filter(pk__in=managed_cdds)
            .with_acronym()
            .order_by('acronym')
            .values_list('acronym', flat=True)
        )

        title_field = 'title' if get_language() == settings.LANGUAGE_CODE else 'title_english'
        doctorates = (
            EducationGroupYear.objects.filter(
                education_group_type__name=TrainingType.PHD.name,
                management_entity_id__in=managed_cdds,
            )
            .distinct('acronym')
            .values_list('acronym', title_field)
            .order_by('acronym')
        )

        academic_years = AcademicYear.objects.min_max_years(
            min_year=MINIMUM_SELECTABLE_YEAR,
            max_year=MAXIMUM_SELECTABLE_YEAR,
        ).order_by('-year')

        # Initialize the CDDs field and hide it if the user manages only one cdd
        self.fields['cdds'].choices = [(acronym, acronym) for acronym in cdd_acronyms]
        self.fields['cdds'].initial = list(cdd_acronyms)

        if len(cdd_acronyms) <= 1:
            self.fields['cdds'].widget = forms.HiddenInput()

        # Initialize the program field
        self.fields['sigles_formations'].choices = [
            (acronym, '{} - {}'.format(acronym, title)) for acronym, title in doctorates
        ]

        # Initialize the proximity commission field
        proximity_commission_choices = [EMPTY_CHOICE[0]]

        if ENTITY_CDE in cdd_acronyms or ENTITY_CLSM in cdd_acronyms:
            proximity_commission_choices.append(
                ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()]
            )

        if ENTITY_CDSS in cdd_acronyms:
            proximity_commission_choices.append([ENTITY_CDSS, ChoixCommissionProximiteCDSS.choices()])

        if SIGLE_SCIENCES in dict(doctorates):
            proximity_commission_choices.append([SIGLE_SCIENCES, ChoixSousDomaineSciences.choices()])

        self.fields['commission_proximite'].choices = proximity_commission_choices

        # Initialize the academic year field
        self.fields['annee_academique'].choices = [EMPTY_CHOICE[0]] + [
            (academic_year.year, str(academic_year)) for academic_year in academic_years
        ]

    class Media:
        js = [
            # DependsOn
            'js/dependsOn.min.js',
            # Dates
            'js/moment.min.js',
            'js/locales/moment-fr.js',
            'js/bootstrap-datetimepicker.min.js',
            'js/dates-input.js',
            # Mask
            'js/jquery.mask.min.js',
        ]
