# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from django import forms
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext, pgettext_lazy

from admission.constants import DEFAULT_PAGINATOR_SIZE
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.enums.liste import TardiveModificationReorientationFiltre
from admission.ddd.admission.enums.statut import CHOIX_STATUT_TOUTE_PROPOSITION
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixEdition,
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_continue.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST as ORGANISATION_ONGLETS_CHECKLIST_CONTINUE,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST as ORGANISATION_ONGLETS_CHECKLIST_GENERALE,
)
from admission.forms import (
    ALL_EMPTY_CHOICE,
    DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
    NullBooleanSelectField,
    get_academic_year_choices,
)
from admission.forms.checklist_state_filter import ChecklistStateFilterField
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.models.working_list import ContinuingWorkingList, WorkingList
from admission.views.autocomplete.trainings import (
    ContinuingManagedEducationTrainingsAutocomplete,
)
from base.forms.utils import EMPTY_CHOICE, autocomplete
from base.forms.widgets import Select2MultipleCheckboxesWidget
from base.models.entity_version import EntityVersion
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person
from base.templatetags.pagination_bs5 import PAGINATOR_SIZE_LIST
from education_group.forms.fields import MainCampusChoiceField
from reference.models.enums.scholarship_type import ScholarshipType
from reference.models.scholarship import Scholarship

REGEX_REFERENCE = r'\d{4}\.\d{4}$'


class WorkingListField(forms.ModelChoiceField):
    def label_from_instance(self, obj: WorkingList):
        return obj.name.get(get_language())


class BaseAdmissionFilterForm(forms.Form):
    statuses_choices = []

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
                'placeholder': 'L-ESPO22-0001.2345',
            },
        ),
    )

    matricule_candidat = forms.CharField(
        label=_('Last name / First name / Email'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:candidates",
            attrs=DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
        ),
    )

    etats = forms.MultipleChoiceField(
        choices=[],
        label=_('Application status'),
        required=False,
        widget=Select2MultipleCheckboxesWidget(
            attrs={
                'data-dropdown-auto-width': True,
                'data-selection-template': _("{items} types out of {total}"),
            }
        ),
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

    def __init__(self, load_labels=False, *args, **kwargs):
        if kwargs.get('data'):
            kwargs['data'] = kwargs['data'].copy()
            kwargs['data'].setdefault('taille_page', DEFAULT_PAGINATOR_SIZE)

        super().__init__(*args, **kwargs)

        self.fields['annee_academique'].choices = get_academic_year_choices()
        self.fields['etats'].choices = self.statuses_choices
        self.fields['etats'].initial = [choice[0] for choice in self.fields['etats'].choices]

        # Initialize the labels of the autocomplete fields
        if load_labels:
            candidate = self.data.get(self.add_prefix('matricule_candidat'))
            if candidate:
                person = Person.objects.values('last_name', 'first_name').filter(global_id=candidate).first()
                if person:
                    self.fields['matricule_candidat'].widget.choices = (
                        (candidate, '{}, {}'.format(person['last_name'], person['first_name'])),
                    )

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        return re.search(REGEX_REFERENCE, numero).group(0).replace('.', '') if numero else ''

    def clean_taille_page(self):
        return self.cleaned_data.get('taille_page') or self.fields['taille_page'].initial

    def clean_page(self):
        return self.cleaned_data.get('page') or self.fields['page'].initial

    class Media:
        js = [
            # DependsOn
            'js/dependsOn.min.js',
            # Mask
            'js/jquery.mask.min.js',
        ]


class AdmissionFilterWithEntitiesAndTrainingTypesForm(BaseAdmissionFilterForm):
    training_types = []

    entites = forms.CharField(
        label=pgettext_lazy('admission', 'Entities'),
        required=False,
        widget=autocomplete.TagSelect2(),
    )

    types_formation = forms.MultipleChoiceField(
        choices=[],
        label=_('Course type'),
        required=False,
        widget=Select2MultipleCheckboxesWidget(
            attrs={
                'data-dropdown-auto-width': True,
                'data-selection-template': _("{items} types out of {total}"),
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['types_formation'].choices = [(key, TrainingType.get_value(key)) for key in self.training_types]

    def clean_entites(self):
        entities = self.cleaned_data.get('entites')
        if entities:
            entities = entities.upper()
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


class AllAdmissionsFilterForm(AdmissionFilterWithEntitiesAndTrainingTypesForm):
    statuses_choices = CHOIX_STATUT_TOUTE_PROPOSITION
    training_types = AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.keys()

    scholarship_types_by_field = {
        'bourse_internationale': {
            ScholarshipType.BOURSE_INTERNATIONALE_DOCTORAT.name,
            ScholarshipType.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name,
        },
        'bourse_erasmus_mundus': {ScholarshipType.ERASMUS_MUNDUS.name},
        'bourse_double_diplomation': {ScholarshipType.DOUBLE_TRIPLE_DIPLOMATION.name},
    }

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

    formation = forms.CharField(
        label=pgettext_lazy('admission', 'Course'),
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

    bourse_internationale = forms.TypedChoiceField(
        label=_('International scholarship'),
        empty_value=None,
        required=False,
    )

    bourse_erasmus_mundus = forms.TypedChoiceField(
        label=_('Erasmus Mundus'),
        empty_value=None,
        required=False,
    )

    bourse_double_diplomation = forms.TypedChoiceField(
        label=_('Dual degree scholarship'),
        empty_value=None,
        required=False,
    )

    quarantaine = forms.TypedChoiceField(
        label=_('Quarantine'),
        coerce=lambda x: x == 'True',
        required=False,
        choices=(
            (None, ' - '),
            (True, _('Yes')),
            (False, _('No')),
        ),
        widget=forms.Select(attrs={"class": "form-control"}),
        empty_value=None,
    )

    tardif_modif_reorientation = forms.ChoiceField(
        choices=EMPTY_CHOICE + TardiveModificationReorientationFiltre.choices(),
        label=_('Late/Modif./Reor.'),
        required=False,
    )

    liste_travail = WorkingListField(
        label=_('Working list'),
        queryset=WorkingList.objects.all(),
        required=False,
        empty_label=_('Personalized'),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:working-lists",
            attrs={
                'data-placeholder': _('Personalized'),
                'data-allow-clear': 'true',
            },
        ),
    )

    mode_filtres_etats_checklist = forms.ChoiceField(
        choices=ModeFiltrageChecklist.choices(),
        label=_('Include or exclude the checklist filters'),
        required=False,
        initial=ModeFiltrageChecklist.INCLUSION.name,
        widget=forms.RadioSelect(),
    )

    filtres_etats_checklist = ChecklistStateFilterField(
        configurations=ORGANISATION_ONGLETS_CHECKLIST_GENERALE,
        label=_('Checklist filters'),
        required=False,
    )

    def __init__(self, user, load_labels=False, *args, **kwargs):
        super().__init__(load_labels, *args, **kwargs)

        self.fields['annee_academique'].initial = AnneeInscriptionFormationTranslator().recuperer(
            AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT
        )
        self.fields['types_formation'].initial = list(
            AnneeInscriptionFormationTranslator.GENERAL_EDUCATION_TYPES
            | AnneeInscriptionFormationTranslator.DOCTORATE_EDUCATION_TYPES
        )

        scholarships_objects = Scholarship.objects.order_by('short_name')
        scholarships = {str(scholarship.uuid): scholarship for scholarship in scholarships_objects}

        for scholarship_field, scholarship_types in self.scholarship_types_by_field.items():
            self.fields[scholarship_field].coerce = scholarships.get
            self.fields[scholarship_field].choices = EMPTY_CHOICE + tuple(
                (scholarship.uuid, str(scholarship))
                for scholarship_uuid, scholarship in scholarships.items()
                if scholarship.type in scholarship_types
            )

        # Initialize the labels of the autocomplete fields
        if load_labels:
            working_list_id = self.data.get(self.add_prefix('liste_travail'))
            if working_list_id:
                working_list = WorkingList.objects.filter(id=working_list_id).first()
                if working_list:
                    self.fields['liste_travail'].widget.choices = (
                        (str(working_list.id), working_list.name.get(get_language())),
                    )

    def clean_site_inscription(self):
        site_inscription = self.cleaned_data.get('site_inscription')
        return str(site_inscription.uuid) if site_inscription else ''

    def clean_bourse_internationale(self):
        bourse_internationale = self.cleaned_data.get('bourse_internationale')
        return str(bourse_internationale.uuid) if bourse_internationale else ''

    def clean_bourse_erasmus_mundus(self):
        bourse_erasmus_mundus = self.cleaned_data.get('bourse_erasmus_mundus')
        return str(bourse_erasmus_mundus.uuid) if bourse_erasmus_mundus else ''

    def clean_bourse_double_diplomation(self):
        bourse_double_diplomation = self.cleaned_data.get('bourse_double_diplomation')
        return str(bourse_double_diplomation.uuid) if bourse_double_diplomation else ''


class ContinuingAdmissionsFilterForm(AdmissionFilterWithEntitiesAndTrainingTypesForm):
    statuses_choices = ChoixStatutPropositionContinue.choices()
    training_types = AnneeInscriptionFormationTranslator.CONTINUING_EDUCATION_TYPES

    edition = forms.MultipleChoiceField(
        label=_('Edition'),
        choices=ChoixEdition.choices(),
        required=False,
        widget=autocomplete.Select2Multiple(attrs={'data-placeholder': pgettext_lazy("feminine", "All")}),
    )

    inscription_requise = NullBooleanSelectField(
        label=_('Registration required'),
        required=False,
        empty_label=pgettext_lazy("feminine", "All"),
    )

    paye = NullBooleanSelectField(
        label=_('Paid'),
        required=False,
        empty_label=pgettext_lazy("feminine", "All"),
    )

    sigles_formations = forms.MultipleChoiceField(
        label=pgettext_lazy('admission', 'Course'),
        required=False,
        widget=autocomplete.Select2Multiple(
            url="admission:autocomplete:continuing-managed-education-trainings",
            attrs={
                'data-placeholder': _('Acronym / Title'),
                **DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
            },
        ),
    )

    marque_d_interet = forms.BooleanField(
        label=_('Interested mark'),
        required=False,
    )

    liste_travail = WorkingListField(
        label=_('Working list'),
        queryset=ContinuingWorkingList.objects.all(),
        required=False,
        empty_label=_('Personalized'),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:continuing-working-lists",
            attrs={
                'data-placeholder': _('Personalized'),
                'data-allow-clear': 'true',
            },
        ),
    )

    mode_filtres_etats_checklist = forms.ChoiceField(
        choices=ModeFiltrageChecklist.choices(),
        label=_('Include or exclude the checklist filters'),
        required=False,
        initial=ModeFiltrageChecklist.INCLUSION.name,
        widget=forms.RadioSelect(),
    )

    filtres_etats_checklist = ChecklistStateFilterField(
        configurations=ORGANISATION_ONGLETS_CHECKLIST_CONTINUE,
        label=_('Checklist filters'),
        required=False,
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['annee_academique'].initial = AnneeInscriptionFormationTranslator().recuperer(
            AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT
        )

        self.fields['entites'].label = _('Faculty')
        self.fields['matricule_candidat'].label = _('Last name / First name / Email / NOMA')

        selected_trainings = self.data.getlist(
            self.add_prefix('sigles_formations'), self.initial.get('sigles_formations', [])
        )

        if selected_trainings:
            available_selected_trainings_qs = ContinuingManagedEducationTrainingsAutocomplete.get_base_queryset(
                user=user,
                acronyms=selected_trainings,
            )
            self.fields['sigles_formations'].choices = [
                (selected_training.acronym, selected_training.formatted_title)
                for selected_training in available_selected_trainings_qs
            ]

    def clean(self):
        cleaned_data = super().clean()

        # Alias
        cleaned_data['facultes'] = cleaned_data.pop('entites', [])

        return cleaned_data
