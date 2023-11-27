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
import datetime
import itertools
from collections import defaultdict
from typing import Optional

from ckeditor.widgets import CKEditorWidget
from dal import forward
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, get_language, ngettext_lazy, pgettext_lazy, pgettext

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.base import training_campus_subquery
from admission.contrib.models.checklist import RefusalReason, AdditionalApprovalCondition
from admission.ddd import DUREE_MINIMALE_PROGRAMME, DUREE_MAXIMALE_PROGRAMME
from admission.ddd.admission.domain.model.enums.condition_acces import recuperer_conditions_acces_par_formation
from admission.ddd.admission.domain.model.enums.equivalence import (
    TypeEquivalenceTitreAcces,
    StatutEquivalenceTitreAcces,
    EtatEquivalenceTitreAcces,
)

from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import PoursuiteDeCycle, ChoixStatutChecklist
from admission.forms import (
    DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
    FilterFieldWidget,
    get_initial_choices_for_additionnal_approval_conditions,
    autocomplete,
    get_example_text,
    EMPTY_CHOICE_AS_LIST,
    CustomDateInput,
)
from admission.forms import get_academic_year_choices
from admission.forms.autocomplete import Select2MultipleWithTagWhenNoResultWidget
from admission.forms.doctorate.training.activity import AcademicYearField
from admission.views.autocomplete.learning_unit_years import LearningUnitYearAutocomplete
from admission.views.common.detail_tabs.comments import COMMENT_TAG_SIC, COMMENT_TAG_FAC
from base.forms.utils.choice_field import BLANK_CHOICE
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from base.models.learning_unit_year import LearningUnitYear
from ddd.logic.learning_unit.commands import LearningUnitAndPartimSearchCommand
from infrastructure.messages_bus import message_bus_instance
from osis_document.utils import is_uuid


class CommentForm(forms.Form):
    comment = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 2,
                'hx-trigger': 'keyup changed delay:2s',
                'hx-target': 'closest .form-group',
                'hx-swap': 'outerHTML',
            }
        ),
        required=False,
    )

    def __init__(self, form_url, comment=None, *args, **kwargs):
        user_is_sic = kwargs.pop('user_is_sic', False)
        user_is_fac = kwargs.pop('user_is_fac', False)
        super().__init__(*args, **kwargs)

        form_for_sic = f'__{COMMENT_TAG_SIC}' in self.prefix
        form_for_fac = f'__{COMMENT_TAG_FAC}' in self.prefix

        self.fields['comment'].widget.attrs['hx-post'] = form_url

        label = (
            _("Faculty comment for the SIC")
            if form_for_fac
            else _('SIC comment for the faculty')
            if form_for_sic
            else _('Comment')
        )

        self.fields['comment'].label = label

        if comment:
            self.fields['comment'].initial = comment.content
            self.fields['comment'].label += _(" (last update by {author} on {date} at {time}):").format(
                author=comment.author,
                date=comment.modified_at.strftime("%d/%m/%Y"),
                time=comment.modified_at.strftime("%H:%M"),
            )
        if form_for_sic and not user_is_sic or form_for_fac and not user_is_fac:
            self.fields['comment'].disabled = True


class DateInput(forms.DateInput):
    input_type = 'date'


class StatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=ChoixStatutChecklist.choices(),
        required=True,
    )


class AssimilationForm(forms.Form):
    date_debut = forms.DateField(
        widget=DateInput(
            attrs={
                'hx-trigger': 'change changed delay:2s',
                'hx-target': 'closest .form-group',
                'hx-validate': 'true',
                'hx-swap': 'outerHTML',
            },
        ),
        label=_("Assimilation start date"),
    )

    def __init__(self, form_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_debut'].widget.attrs['hx-post'] = form_url


class ChoixFormationForm(forms.Form):
    type_demande = forms.ChoiceField(
        label=_("Proposition type"),
        choices=TypeDemande.choices(),
    )
    annee_academique = forms.ChoiceField(
        label=_("Academic year"),
    )
    formation = forms.CharField(
        label=pgettext_lazy("admission", "Course"),
        widget=autocomplete.ListSelect2(
            forward=['annee_academique'],
            url="admission:autocomplete:general-education-trainings",
            attrs=DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
        ),
    )
    poursuite_cycle = forms.ChoiceField(
        label=_("Cycle pursuit"),
        choices=PoursuiteDeCycle.choices(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        formation = kwargs.pop('formation')
        self.has_success_be_experience = kwargs.pop('has_success_be_experience')
        super().__init__(*args, **kwargs)
        today = datetime.date.today()
        try:
            current_year = AcademicYear.objects.get(start_date__lte=today, end_date__gt=today).year
        except AcademicYear.DoesNotExist:
            current_year = today.year
        self.fields['annee_academique'].choices = get_academic_year_choices(current_year - 2, current_year + 2)

        if self.data.get(self.add_prefix('formation')):
            training = (
                EducationGroupYear.objects.select_related('education_group_type')
                .filter(
                    acronym=self.data.get('formation'),
                )
                .first()
            )
            training_title = training.title if get_language() == settings.LANGUAGE_CODE_FR else training.title_english
            self.fields['formation'].widget.choices = [
                (training.acronym, f'{training.acronym} - {training_title}'),
            ]
            self.initial_training_type = training.education_group_type.name
        else:
            self.fields['formation'].widget.choices = [(formation.sigle, f'{formation.sigle} - {formation.intitule}')]
            self.initial_training_type = formation.type

    def clean(self):
        cleaned_data = super().clean()
        formation = cleaned_data.get('formation')

        if formation and self.has_success_be_experience:
            # The bachelor cycle continuation field is shown and required if the training is a bachelor and the user has
            # successfully completed a belgian academic experience
            if self.initial_training_type == TrainingType.BACHELOR.name:
                if not cleaned_data.get('poursuite_cycle'):
                    self.add_error('poursuite_cycle', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['poursuite_cycle'] = PoursuiteDeCycle.TO_BE_DETERMINED.name
        else:
            cleaned_data['poursuite_cycle'] = PoursuiteDeCycle.TO_BE_DETERMINED.name
        return cleaned_data


def get_group_by_choices(
    queryset,
    item_category_field,
    item_category_name_field,
    item_identifier_field,
    item_name_field,
):
    """Get choices grouped by an attribute from the queryset.
    :param queryset: A list of items to group by.
    :param item_category_field: The name of the attribute to group the items by (i.e. the category).
    :param item_category_name_field: The name of the attribute of the category name.
    :param item_identifier_field: The name of the attribute identifying the items.
    :param item_name_field: The name of the attribute of the the item name.
    :return: The hierarchy of choices as list of lists.
    """
    item_by_category = defaultdict(list)
    for item in queryset:
        item_by_category[getattr(getattr(item, item_category_field), item_category_name_field)].append(
            [getattr(item, item_identifier_field), mark_safe(getattr(item, item_name_field))]
        )

    return [[category_name, category_choices] for category_name, category_choices in item_by_category.items()]


class FacDecisionRefusalForm(forms.Form):
    reasons = forms.MultipleChoiceField(
        label=pgettext_lazy('admission', 'Reasons'),
        widget=FilterFieldWidget(
            with_search=True,
            with_free_options=True,
            free_options_placeholder=get_example_text(
                _('Your training does not cover the useful prerequisites in mathematics.'),
            ),
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        all_reasons = RefusalReason.objects.select_related('category').all().order_by('category__name', 'name')

        choices = get_group_by_choices(
            queryset=all_reasons,
            item_category_field='category',
            item_category_name_field='name',
            item_identifier_field='uuid',
            item_name_field='name',
        )

        selected_reasons = self.data.getlist(self.add_prefix('reasons'), self.initial.get('reasons')) or []

        self.categorized_reasons = []
        self.other_reasons = []
        other_reasons_choices = []

        for reason in selected_reasons:
            if is_uuid(reason):
                self.categorized_reasons.append(reason)
            else:
                self.other_reasons.append(reason)
                other_reasons_choices.append([reason, reason])

        choices.append([pgettext('admission', 'Other reasons'), other_reasons_choices])

        self.fields['reasons'].choices = choices
        self.fields['reasons'].widget.choices = choices

    def clean(self):
        cleaned_data = super().clean()

        reasons = cleaned_data.get('reasons')

        if reasons:
            cleaned_data['other_reasons'] = sorted(self.other_reasons)
            cleaned_data['reasons'] = self.categorized_reasons
        else:
            self.add_error('reasons', FIELD_REQUIRED_MESSAGE)

        return cleaned_data


class TrainingModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: EducationGroupYear) -> str:
        return f'{obj.acronym} - {obj.translated_title} ({obj.teaching_campus})'


class MultipleChoiceFieldWithBetterError(forms.MultipleChoiceField):
    """
    Same as forms.MultipleChoiceField, but display the list of the invalid values if there are any
    (and not only the first one).
    """

    default_error_messages = {
        'invalid_choice': ngettext_lazy(
            'Select valid choices. %(value)s is not one of the available choices.',
            'Select valid choices. %(value)s are not among the available choices.',
            'count',
        ),
        'invalid_list': _('Enter a list of values.'),
    }

    def validate(self, value):
        """Validate that the input is a list or tuple."""
        if self.required and not value:
            raise ValidationError(self.error_messages['required'], code='required')

        # Validate that each value in the value list is in self.choices.
        invalid_values = [f'"{val}"' for val in value if not self.valid_value(val)]

        if invalid_values:
            raise ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice',
                params={'value': ', '.join(invalid_values), 'count': len(invalid_values)},
            )


class FacDecisionApprovalForm(forms.ModelForm):
    SEPARATOR = ';'

    another_training = forms.BooleanField(
        label=_('Approval for another training'),
        required=False,
    )

    other_training_accepted_by_fac = TrainingModelChoiceField(
        label=_('Other course'),
        queryset=EducationGroupYear.objects.none(),
        to_field_name='uuid',
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:managed-education-trainings",
            attrs=DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
        ),
    )

    prerequisite_courses = MultipleChoiceFieldWithBetterError(
        label=_('List of LUs of the additional module or others'),
        widget=Select2MultipleWithTagWhenNoResultWidget(
            url='admission:autocomplete:learning-unit-years',
            attrs={
                'data-token-separators': '[{}]'.format(SEPARATOR),
                'data-tags': 'true',
                'data-allow-clear': 'false',
                **DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
            },
        ),
        required=False,
        help_text=_(
            'You can search for an additional training by name or acronym, or paste in a list of acronyms separated '
            'by the "%(separator)s" character and ending with the same character.'
        )
        % {'separator': SEPARATOR},
    )

    all_additional_approval_conditions = forms.MultipleChoiceField(
        label=_('Additional conditions'),
        required=False,
        widget=autocomplete.Select2Multiple(
            attrs={
                'data-allow-clear': 'false',
                'data-tags': 'true',
            },
        ),
    )

    class Meta:
        model = GeneralEducationAdmission
        fields = [
            'other_training_accepted_by_fac',
            'prerequisite_courses',
            'prerequisite_courses_fac_comment',
            'program_planned_years_number',
            'annual_program_contact_person_name',
            'annual_program_contact_person_email',
            'join_program_fac_comment',
            'with_additional_approval_conditions',
            'with_prerequisite_courses',
        ]
        labels = {
            'annual_program_contact_person_name': _('First name and last name'),
            'annual_program_contact_person_email': pgettext_lazy('admission', 'Email'),
        }
        widgets = {
            'prerequisite_courses_fac_comment': CKEditorWidget(config_name='comment_link_only'),
            'join_program_fac_comment': CKEditorWidget(config_name='comment_link_only'),
            'with_prerequisite_courses': forms.RadioSelect(choices=[(True, _('Yes')), (False, _('No'))]),
            'with_additional_approval_conditions': forms.RadioSelect(choices=[(True, _('Yes')), (False, _('No'))]),
            'program_planned_years_number': forms.Select(
                choices=EMPTY_CHOICE_AS_LIST
                + [(number, number) for number in range(DUREE_MINIMALE_PROGRAMME, DUREE_MAXIMALE_PROGRAMME + 1)],
            ),
        }

    def __init__(self, academic_year, additional_approval_conditions_for_diploma, *args, **kwargs):
        instance: Optional[GeneralEducationAdmission] = kwargs.get('instance', None)
        data = kwargs.get('data', {})
        initial = kwargs.setdefault('initial', {})

        if instance:
            initial['another_training'] = bool(instance.other_training_accepted_by_fac_id)

        super().__init__(*args, **kwargs)

        # Initialize conditions field
        self.academic_year = academic_year
        self.data_existing_conditions = set()
        self.data_free_conditions = set()
        self.predefined_approval_conditions = []
        free_approval_conditions = []

        # Initialize additional approval conditions field
        if data:
            for condition in data.getlist(self.add_prefix('all_additional_approval_conditions'), []):
                if is_uuid(condition):
                    self.data_existing_conditions.add(condition)
                else:
                    self.data_free_conditions.add(condition)

            free_approval_conditions = self.data_free_conditions

        elif instance:
            # Additional conditions
            existing_approval_conditions = instance.additional_approval_conditions.all()
            free_approval_conditions = instance.free_additional_approval_conditions
            self.initial['all_additional_approval_conditions'] = [
                c.uuid for c in existing_approval_conditions
            ] + free_approval_conditions

        self.predefined_approval_conditions = AdditionalApprovalCondition.objects.all()

        all_additional_approval_conditions_choices = get_initial_choices_for_additionnal_approval_conditions(
            predefined_approval_conditions=self.predefined_approval_conditions,
            free_approval_conditions=itertools.chain(
                additional_approval_conditions_for_diploma,
                free_approval_conditions,
            ),
        )
        self.fields['all_additional_approval_conditions'].choices = all_additional_approval_conditions_choices
        self.fields['all_additional_approval_conditions'].widget.choices = all_additional_approval_conditions_choices

        # Initialize other training field
        if self.data.get(self.add_prefix('other_training_accepted_by_fac')):
            other_trainings_search_params = {'uuid': self.data[self.add_prefix('other_training_accepted_by_fac')]}
        elif instance and instance.other_training_accepted_by_fac_id:
            other_trainings_search_params = {
                'pk': instance.other_training_accepted_by_fac_id,
            }
        else:
            other_trainings_search_params = {}

        if other_trainings_search_params:
            training_qs = EducationGroupYear.objects.filter(**other_trainings_search_params).annotate(
                teaching_campus=training_campus_subquery(training_field='pk'),
                translated_title=F('title' if get_language() == settings.LANGUAGE_CODE_FR else 'title_english'),
            )

            self.fields['other_training_accepted_by_fac'].queryset = training_qs
            self.initial['other_training_accepted_by_fac'] = training_qs[0].uuid if training_qs else ''

        self.fields['other_training_accepted_by_fac'].widget.forward = [
            forward.Const(academic_year, 'annee_academique')
        ]
        self.fields['prerequisite_courses'].widget.forward = [forward.Const(academic_year, 'year')]

        # Initialize additional trainings fields
        lue_acronyms = {}

        if self.is_bound:
            lue_acronyms = {
                (acronym, academic_year) for acronym in self.data.getlist(self.add_prefix('prerequisite_courses'))
            }

        elif self.instance:
            lue_acronyms = set(self.instance.prerequisite_courses.all().values_list('acronym', 'academic_year__year'))
            self.initial['prerequisite_courses'] = [acronym[0] for acronym in lue_acronyms]

        learning_units = (
            message_bus_instance.invoke(LearningUnitAndPartimSearchCommand(code_annee_values=lue_acronyms))
            if lue_acronyms
            else []
        )

        self.fields['prerequisite_courses'].choices = LearningUnitYearAutocomplete.dtos_to_choices(learning_units)

    def clean_all_additional_approval_conditions(self):
        # This field can contain uuids of existing conditions or free conditions as strings
        cleaned_data = self.cleaned_data.get('all_additional_approval_conditions', [])

        self.cleaned_data['additional_approval_conditions'] = list(self.data_existing_conditions)
        self.cleaned_data['free_additional_approval_conditions'] = list(self.data_free_conditions)

        return cleaned_data

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('another_training'):
            if not cleaned_data.get('other_training_accepted_by_fac'):
                self.add_error('other_training_accepted_by_fac', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['other_training_accepted_by_fac'] = None

        if not cleaned_data.get('with_additional_approval_conditions'):
            cleaned_data['all_additional_approval_conditions'] = []
            cleaned_data['additional_approval_conditions'] = []
            cleaned_data['free_additional_approval_conditions'] = []

        if cleaned_data.get('with_prerequisite_courses'):
            if cleaned_data.get('prerequisite_courses'):
                cleaned_data['prerequisite_courses'] = LearningUnitYear.objects.filter(
                    acronym__in=cleaned_data.get('prerequisite_courses', []),
                    academic_year__year=self.academic_year,
                ).values_list('uuid', flat=True)

        else:
            cleaned_data['prerequisite_courses'] = []
            cleaned_data['prerequisite_courses_fac_comment'] = ''

        return cleaned_data


class PastExperiencesAdmissionRequirementForm(forms.ModelForm):
    admission_requirement_year = AcademicYearField(
        past_only=True,
        required=False,
        label=_('Admission requirement'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['admission_requirement'].choices = BLANK_CHOICE + recuperer_conditions_acces_par_formation(
            type_formation=self.instance.training.education_group_type.name,
        )

        for field in self.fields.values():
            field.widget.attrs['class'] = 'past-experiences-admission-requirement-field'

    class Meta:
        model = GeneralEducationAdmission
        fields = [
            'admission_requirement',
            'admission_requirement_year',
        ]


class PastExperiencesAdmissionAccessTitleForm(forms.ModelForm):
    default_values = {
        'foreign_access_title_equivalency_type': '',
        'foreign_access_title_equivalency_status': '',
        'foreign_access_title_equivalency_state': '',
        'foreign_access_title_equivalency_effective_date': None,
    }

    class Meta:
        model = GeneralEducationAdmission
        fields = [
            'foreign_access_title_equivalency_type',
            'foreign_access_title_equivalency_status',
            'foreign_access_title_equivalency_state',
            'foreign_access_title_equivalency_effective_date',
        ]
        widgets = {
            'foreign_access_title_equivalency_effective_date': CustomDateInput,
        }

    class Media:
        js = [
            'js/dependsOn.min.js',
        ]

    def clean(self):
        cleaned_data = super().clean()

        equivalency_type = cleaned_data.get('foreign_access_title_equivalency_type')
        equivalency_status = cleaned_data.get('foreign_access_title_equivalency_status')
        equivalency_state = cleaned_data.get('foreign_access_title_equivalency_state')

        displayed_fields = {
            'foreign_access_title_equivalency_type',
        }

        if equivalency_type in {
            TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
            TypeEquivalenceTitreAcces.EQUIVALENCE_GRADE_ACADEMIQUE_FWB.name,
            TypeEquivalenceTitreAcces.EQUIVALENCE_DE_NIVEAU.name,
        }:
            displayed_fields.add('foreign_access_title_equivalency_status')

            if equivalency_status in {
                StatutEquivalenceTitreAcces.COMPLETE.name,
                StatutEquivalenceTitreAcces.RESTRICTIVE.name,
            }:
                displayed_fields.add('foreign_access_title_equivalency_state')

                if equivalency_state in {
                    EtatEquivalenceTitreAcces.PROVISOIRE.name,
                    EtatEquivalenceTitreAcces.DEFINITIVE.name,
                }:
                    displayed_fields.add('foreign_access_title_equivalency_effective_date')

        for field in self.fields:
            if field in displayed_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data[field] = self.default_values[field]

        return cleaned_data


class FinancabiliteApprovalForm(forms.ModelForm):
    class Meta:
        model = GeneralEducationAdmission
        fields = [
            'financability_rule',
        ]
