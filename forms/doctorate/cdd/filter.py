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

from dal import forward
from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils.translation import get_language, gettext_lazy as _, pgettext_lazy

from admission.models import EntityProxy, Scholarship
from admission.models.working_list import WorkingList, DoctorateWorkingList
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import (
    ENTITY_CDE,
    ENTITY_CDSS,
    ENTITY_CLSM,
    SIGLE_SCIENCES,
    ENTITY_SCIENCES,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    BourseRecherche,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixTypeAdmission,
    ChoixTypeFinancement,
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.enums.type_bourse import TypeBourse
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_POUR_LISTING,
)
from admission.forms import (
    DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
    ALL_EMPTY_CHOICE,
    ALL_FEMININE_EMPTY_CHOICE,
)
from admission.forms.admission.filter import BaseAdmissionFilterForm, WorkingListField
from admission.forms.checklist_state_filter import ChecklistStateFilterField
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.forms.utils import autocomplete
from base.forms.utils.datefield import DatePickerInput
from base.models.education_group_year import EducationGroupYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.models.person import Person
from education_group.contrib.models import EducationGroupRoleModel
from osis_role.contrib.models import EntityRoleModel
from osis_role.contrib.permissions import _get_relevant_roles
from reference.models.country import Country


class DoctorateListFilterForm(BaseAdmissionFilterForm):
    statuses_choices = ChoixStatutPropositionDoctorale.choices()

    nationalite = forms.CharField(
        label=_("Nationality"),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:countries",
            attrs={
                'data-placeholder': _('Country'),
                **DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
            },
            forward=[forward.Const('iso_code', 'id_field')],
        ),
    )
    type = forms.ChoiceField(
        choices=ALL_EMPTY_CHOICE + ChoixTypeAdmission.choices(),
        label=pgettext_lazy('doctorate-filter', 'Admission type'),
        required=False,
    )
    cotutelle = forms.NullBooleanField(
        label=_("Cotutelle"),
        required=False,
        widget=forms.Select(
            choices=(
                ALL_EMPTY_CHOICE[0],
                (True, _('Yes')),
                (False, _('No')),
            ),
        ),
    )
    date_soumission_debut = forms.DateField(
        label=_("From"),
        required=False,
        widget=DatePickerInput(),
    )
    date_soumission_fin = forms.DateField(
        label=_("To"),
        required=False,
        widget=DatePickerInput(),
    )
    commission_proximite = forms.ChoiceField(
        label=_('Proximity commission'),
        required=False,
    )
    cdds = forms.MultipleChoiceField(
        label=_('Doctoral commissions'),
        required=False,
        widget=autocomplete.Select2Multiple(),
    )
    matricule_promoteur = forms.CharField(
        label=pgettext_lazy('gender', 'Supervisor'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:promoters",
            attrs={
                **DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
                'data-placeholder': _('Last name / First name / Global id'),
            },
        ),
    )
    sigles_formations = forms.MultipleChoiceField(
        label=pgettext_lazy('admission', 'Courses'),
        required=False,
        widget=autocomplete.Select2Multiple(
            attrs={
                'data-placeholder': _('Acronym / Title'),
            },
        ),
    )
    type_financement = forms.ChoiceField(
        choices=ALL_EMPTY_CHOICE + ChoixTypeFinancement.choices(),
        label=_('Funding type'),
        required=False,
    )
    bourse_recherche = forms.ChoiceField(
        label=_("Research scholarship"),
        required=False,
    )
    fnrs_fria_fresh = forms.BooleanField(
        label=_("FNRS, FRIA, FRESH"),
        required=False,
    )
    mode_filtres_etats_checklist = forms.ChoiceField(
        choices=ModeFiltrageChecklist.choices(),
        label=_('Include or exclude the checklist filters'),
        required=False,
        initial=ModeFiltrageChecklist.INCLUSION.name,
        widget=forms.RadioSelect(),
    )
    filtres_etats_checklist = ChecklistStateFilterField(
        configurations=ORGANISATION_ONGLETS_CHECKLIST_POUR_LISTING,
        label=_('Checklist filters'),
        required=False,
    )
    liste_travail = WorkingListField(
        label=_('Working list'),
        queryset=DoctorateWorkingList.objects.all(),
        required=False,
        empty_label=_('Personalized'),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:doctorate-working-lists",
            attrs={
                'data-placeholder': _('Personalized'),
                'data-allow-clear': 'true',
            },
        ),
    )

    class Media:
        js = [
            # Dates
            'js/moment.min.js',
            'js/locales/moment-fr.js',
            'js/bootstrap-datetimepicker.min.js',
            'js/dates-input.js',
        ]

    def get_doctorate_queryset(self):
        """Used to determine which training to filter on"""
        qs = EducationGroupYear.objects.filter(education_group_type__name=TrainingType.FORMATION_PHD.name)
        conditions = Q()
        for entity_aware_role in [r for r in self.relevant_roles if issubclass(r, EntityRoleModel)]:
            conditions |= Q(
                management_entity_id__in=entity_aware_role.objects.filter(person=self.user.person).get_entities_ids()
            )
        for education_aware_role in [r for r in self.relevant_roles if issubclass(r, EducationGroupRoleModel)]:
            conditions |= Q(
                education_group_id__in=education_aware_role.objects.filter(
                    person=self.user.person
                ).get_education_groups_affected()
            )
        return (
            qs.filter(conditions)
            .distinct('acronym')
            .values_list('acronym', 'title' if get_language() == settings.LANGUAGE_CODE_FR else 'title_english')
            .order_by('acronym')
        )

    def get_cdd_queryset(self):
        """Used to determine which doctoral commission to filter on"""
        qs = EntityProxy.objects.filter(entityversion__entity_type=EntityType.DOCTORAL_COMMISSION.name)
        conditions = Q()
        for entity_aware_role in [r for r in self.relevant_roles if issubclass(r, EntityRoleModel)]:
            conditions |= Q(pk__in=entity_aware_role.objects.filter(person=self.user.person).get_entities_ids())
        for education_aware_role in [r for r in self.relevant_roles if issubclass(r, EducationGroupRoleModel)]:
            conditions |= Q(
                management_entity__education_group_id__in=education_aware_role.objects.filter(
                    person=self.user.person
                ).values_list('education_group_id')
            )
        return (
            qs.filter(conditions)
            .with_acronym()
            .distinct('acronym')
            .order_by('acronym')
            .values_list(
                'acronym',
                flat=True,
            )
        )

    def get_proximity_commission_choices(self):
        proximity_commission_choices = [ALL_FEMININE_EMPTY_CHOICE[0]]

        if ENTITY_CDE in self.cdd_acronyms or ENTITY_CLSM in self.cdd_acronyms:
            proximity_commission_choices.append(
                ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()]
            )

        if ENTITY_CDSS in self.cdd_acronyms:
            proximity_commission_choices.append([ENTITY_CDSS, ChoixCommissionProximiteCDSS.choices()])

        if SIGLE_SCIENCES in dict(self.doctorates):
            proximity_commission_choices.append([ENTITY_SCIENCES, ChoixSousDomaineSciences.choices()])

        return proximity_commission_choices

    def get_scholarship_choices(self):
        doctorate_scholarships = Scholarship.objects.filter(
            type=TypeBourse.BOURSE_INTERNATIONALE_DOCTORAT.name,
        ).order_by('short_name')

        return (
            [ALL_FEMININE_EMPTY_CHOICE[0]]
            + [(scholarship.uuid, scholarship.short_name) for scholarship in doctorate_scholarships]
            + [(BourseRecherche.OTHER.name, BourseRecherche.OTHER.value)]
        )

    def __init__(self, user, load_labels=False, **kwargs):
        super().__init__(load_labels, **kwargs)

        self.user = user
        self.relevant_roles = _get_relevant_roles(user, 'admission.view_doctorate_enrolment_applications')

        self.fields['bourse_recherche'].choices = self.get_scholarship_choices()

        # Initialize the CDDs field
        self.cdd_acronyms = self.get_cdd_queryset()
        self.fields['cdds'].choices = [(acronym, acronym) for acronym in self.cdd_acronyms]
        # Hide the CDDs field if the user manages only one cdd
        if len(self.cdd_acronyms) <= 1:
            self.fields['cdds'].widget = forms.MultipleHiddenInput()

        # Initialize the program field
        self.doctorates = self.get_doctorate_queryset()
        self.fields['sigles_formations'].choices = [
            (acronym, '{} - {}'.format(acronym, title)) for acronym, title in self.doctorates
        ]

        # Initialize the proximity commission field
        self.fields['commission_proximite'].choices = self.get_proximity_commission_choices()
        # Hide the proximity commission field if there is only one choice
        if len(self.fields['commission_proximite'].choices) == 1:
            self.fields['commission_proximite'].widget = forms.HiddenInput()

        # Initialize the academic year field
        current_academic_year = AnneeInscriptionFormationTranslator().recuperer(
            AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT
        )
        if current_academic_year:
            self.fields['annee_academique'].initial = current_academic_year + 1

        # Change the label of the candidate field
        self.fields['matricule_candidat'].label = _('Last name / First name / Email / NOMA')

        # Initialize the labels of the autocomplete fields
        if load_labels:
            nationality = self.data.get(self.add_prefix('nationalite'))
            if nationality:
                country = (
                    Country.objects.filter(iso_code=nationality)
                    .values_list('name' if get_language() == settings.LANGUAGE_CODE_FR else 'name_en')
                    .first()
                )
                if country:
                    self.fields['nationalite'].widget.choices = ((nationality, country[0]),)

            promoter = self.data.get(self.add_prefix('matricule_promoteur'))
            if promoter:
                person = Person.objects.values('last_name', 'first_name').filter(global_id=promoter).first()
                if person:
                    self.fields['matricule_promoteur'].widget.choices = (
                        (promoter, '{}, {}'.format(person['last_name'], person['first_name'])),
                    )

    def clean(self):
        cleaned_data = super().clean()

        # Check that the start date is before the end date
        submission_date_start = cleaned_data.get('date_soumission_debut')
        submission_date_end = cleaned_data.get('date_soumission_fin')
        if submission_date_start and submission_date_end and submission_date_start > submission_date_end:
            self.add_error(None, _("The start date must be earlier than or the same as the end date."))

        return cleaned_data
