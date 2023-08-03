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
from typing import Optional

from ckeditor.widgets import CKEditorWidget
from dal import forward, autocomplete
from dal_select2 import widgets as autocomplete_widgets
from dal_select2.widgets import I18N_PATH
from django import forms
from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.core.exceptions import ValidationError
from django.db.models import Subquery, OuterRef, F
from django.utils.translation import gettext_lazy as _, get_language, ngettext, ngettext_lazy
from django_filters.fields import ModelChoiceField

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.base import training_campus_subquery
from admission.contrib.models.checklist import RefusalReasonCategory, RefusalReason, AdditionalApprovalCondition
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import PoursuiteDeCycle
from admission.forms import RadioBooleanField
from admission.forms import get_academic_year_choices
from admission.views.autocomplete.learning_unit_years import LearningUnitYearAutocomplete
from admission.views.common.detail_tabs.comments import COMMENT_TAG_SIC, COMMENT_TAG_FAC
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.learning_unit_year import LearningUnitYear
from ddd.logic.learning_unit.commands import LearningUnitAndPartimSearchCommand
from infrastructure.messages_bus import message_bus_instance
from osis_document.utils import is_uuid
from program_management.models.education_group_version import EducationGroupVersion


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

        if comment:
            self.fields['comment'].initial = comment.content
            self.fields['comment'].label = label + _(" (last update by {author} on {date} at {time}):").format(
                author=comment.author,
                date=comment.modified_at.strftime("%d/%m/%Y"),
                time=comment.modified_at.strftime("%H:%M"),
            )
        if form_for_sic and not user_is_sic or form_for_fac and not user_is_fac:
            self.fields['comment'].disabled = True


class DateInput(forms.DateInput):
    input_type = 'date'


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
        label=_("Training"),
        widget=autocomplete.ListSelect2(
            forward=['annee_academique'], url="admission:autocomplete:general-education-trainings"
        ),
    )
    poursuite_cycle = forms.ChoiceField(
        label=_("Cycle pursuit"),
        choices=PoursuiteDeCycle.choices(),
    )

    def __init__(self, *args, **kwargs):
        formation = kwargs.pop('formation')
        super().__init__(*args, **kwargs)
        today = datetime.date.today()
        try:
            current_year = AcademicYear.objects.get(start_date__lte=today, end_date__gt=today).year
        except AcademicYear.DoesNotExist:
            current_year = today.year
        self.fields['annee_academique'].choices = get_academic_year_choices(current_year - 2, current_year + 2)
        self.fields['formation'].widget.choices = [(formation.sigle, f'{formation.sigle} - {formation.intitule}')]


class FacDecisionRefusalForm(forms.Form):
    category = ModelChoiceField(
        label=_('Category'),
        queryset=RefusalReasonCategory.objects.all(),
        null_label=_('Other'),
        null_value='OTHER',
    )

    reason = forms.ModelChoiceField(
        label=_('Reason'),
        queryset=RefusalReason.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='admission:autocomplete:checklist:refusal-reason',
            forward=['category'],
        ),
    )

    other_reason = forms.CharField(
        label=_('Other reason'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})

        if initial:
            reason = initial.get('reason')
            other_reason = initial.get('other_reason')

            kwargs['initial']['category'] = reason.category if reason else 'OTHER' if other_reason else ''

        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        category = cleaned_data.get('category')

        if category:
            if cleaned_data.get('category') == 'OTHER':
                cleaned_data['reason'] = None
                if not cleaned_data.get('other_reason'):
                    self.add_error('other_reason', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['other_reason'] = ''
                if not cleaned_data.get('reason'):
                    self.add_error('reason', FIELD_REQUIRED_MESSAGE)

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
        label=_('Training'),
        queryset=EducationGroupYear.objects.none(),
        to_field_name='uuid',
        required=False,
        widget=autocomplete_widgets.ListSelect2(url="admission:autocomplete:managed-education-trainings"),
    )

    prerequisite_courses = MultipleChoiceFieldWithBetterError(
        label=_('List of LUs of the additional module or others'),
        widget=autocomplete.Select2Multiple(
            url='admission:autocomplete:learning-unit-years',
            attrs={
                'data-token-separators': [SEPARATOR],
                'data-tags': 'true',
            },
        ),
        required=False,
        help_text=_(
            'You can search for an additional training by name or acronym, or paste in a list of acronyms separated '
            'by the "%(separator)s" character.'
        )
        % {'separator': SEPARATOR},
    )

    all_additional_approval_conditions = forms.MultipleChoiceField(
        label=_('Additional conditions'),
        required=False,
        widget=autocomplete_widgets.Select2Multiple(
            url='admission:autocomplete:checklist:additional-approval-condition',
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
            'annual_program_contact_person_email': _('Email'),
            'other_training_accepted_by_fac': _('Other training'),
        }
        widgets = {
            'prerequisite_courses_fac_comment': CKEditorWidget(config_name='link_only'),
            'join_program_fac_comment': CKEditorWidget(config_name='link_only'),
            'with_prerequisite_courses': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
            'with_additional_approval_conditions': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
        }

    def __init__(self, academic_year, *args, **kwargs):
        instance: Optional[GeneralEducationAdmission] = kwargs.get('instance', None)
        data = kwargs.get('data', {})

        existing_approval_conditions = []
        free_approval_conditions = []

        if instance:
            initial = kwargs.setdefault('initial', {})
            initial['another_training'] = bool(instance.other_training_accepted_by_fac_id)

            # Additional conditions
            existing_approval_conditions = instance.additional_approval_conditions.all()
            free_approval_conditions = instance.free_additional_approval_conditions
            initial['all_additional_approval_conditions'] = free_approval_conditions + [
                c.uuid for c in existing_approval_conditions
            ]

        super().__init__(*args, **kwargs)

        # Initialize conditions field
        self.academic_year = academic_year
        self.data_existing_conditions = set()
        self.data_free_conditions = set()
        self.conditions_qs = []

        if data:
            for condition in data.getlist(self.add_prefix('all_additional_approval_conditions'), []):
                if is_uuid(condition):
                    self.data_existing_conditions.add(condition)
                else:
                    self.data_free_conditions.add(condition)

            free_approval_conditions = self.data_free_conditions
            existing_approval_conditions = AdditionalApprovalCondition.objects.filter(
                uuid__in=self.data_existing_conditions
            )
            self.conditions_qs = existing_approval_conditions

        current_language = get_language()
        translated_title = 'name_fr' if current_language == settings.LANGUAGE_CODE_FR else 'name_en'
        self.fields['all_additional_approval_conditions'].choices = [
            (c.uuid, getattr(c, translated_title)) for c in existing_approval_conditions
        ] + [(c, c) for c in free_approval_conditions]

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
        # This field can contain uuids of existing conditions or free condition as strings
        cleaned_data = self.cleaned_data.get('all_additional_approval_conditions', [])

        if len(self.conditions_qs) != len(self.data_existing_conditions):
            self.add_error('all_additional_approval_conditions', _('Not all the conditions have been found.'))

        # Check that the uuids correspond to existing conditions
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
