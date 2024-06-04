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

import datetime
import json
from collections import defaultdict
from typing import Optional, List

from ckeditor.widgets import CKEditorWidget
from dal import forward
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils.safestring import mark_safe
from django.utils.translation import (
    gettext_lazy as _,
    get_language,
    ngettext_lazy,
    pgettext_lazy,
    pgettext,
    gettext,
    override,
)

from admission.templatetags.admission import CONTEXT_GENERAL
from osis_document.utils import is_uuid

from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.base import training_campus_subquery
from admission.contrib.models.checklist import (
    RefusalReason,
    AdditionalApprovalCondition,
)
from admission.ddd import DUREE_MINIMALE_PROGRAMME, DUREE_MAXIMALE_PROGRAMME
from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.domain.model.enums.condition_acces import recuperer_conditions_acces_par_formation
from admission.ddd.admission.domain.model.enums.equivalence import (
    TypeEquivalenceTitreAcces,
    StatutEquivalenceTitreAcces,
    EtatEquivalenceTitreAcces,
)
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums import TypeSituationAssimilation
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    PoursuiteDeCycle,
    BesoinDeDerogation,
    DroitsInscriptionMontant,
    TypeDeRefus,
    ChoixStatutChecklist,
    DispenseOuDroitsMajores,
    DerogationFinancement,
)
from admission.forms import (
    DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
    FilterFieldWidget,
    EMPTY_CHOICE_AS_LIST,
    get_initial_choices_for_additional_approval_conditions,
    AdmissionHTMLCharField,
)
from admission.forms import get_academic_year_choices
from admission.forms.admission.document import ChangeRequestDocumentForm
from admission.views.autocomplete.learning_unit_years import LearningUnitYearAutocomplete
from admission.views.common.detail_tabs.comments import COMMENT_TAG_SIC, COMMENT_TAG_FAC
from base.forms.utils import EMPTY_CHOICE, get_example_text, FIELD_REQUIRED_MESSAGE, autocomplete
from base.forms.utils.academic_year_field import AcademicYearModelChoiceField
from base.forms.utils.autocomplete import Select2MultipleWithTagWhenNoResultWidget
from base.forms.utils.choice_field import BLANK_CHOICE
from base.forms.utils.datefield import CustomDateInput
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from base.models.learning_unit_year import LearningUnitYear
from ddd.logic.learning_unit.commands import LearningUnitAndPartimSearchCommand
from infrastructure.messages_bus import message_bus_instance

FINANCABILITE_REFUS_CATEGORY = 'Finançabilité'


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

    def __init__(self, form_url, comment=None, label=None, *args, **kwargs):
        disabled = kwargs.pop('disabled', False)

        super().__init__(*args, **kwargs)

        form_for_sic = self.prefix.endswith(f'__{COMMENT_TAG_SIC}')
        form_for_fac = self.prefix.endswith(f'__{COMMENT_TAG_FAC}')

        self.fields['comment'].widget.attrs['hx-post'] = form_url

        if form_for_fac:
            label = _('Faculty comment for the SIC')
            self.permission = 'admission.checklist_change_fac_comment'
        elif form_for_sic:
            label = _('SIC comment for the faculty')
            self.permission = 'admission.checklist_change_sic_comment'
        else:
            if not label:
                label = _('Comment')
            self.permission = 'admission.checklist_change_comment'

        self.fields['comment'].label = label

        if comment:
            self.fields['comment'].initial = comment.content
            self.fields['comment'].label += _(" (last update by {author} on {date} at {time}):").format(
                author=comment.author,
                date=comment.modified_at.strftime("%d/%m/%Y"),
                time=comment.modified_at.strftime("%H:%M"),
            )

        if disabled:
            self.fields['comment'].disabled = True


class DateInput(forms.DateInput):
    input_type = 'date'


class StatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=ChoixStatutChecklist.choices(),
        required=True,
    )


class ExperienceStatusForm(StatusForm):
    authentification = forms.TypedChoiceField(
        required=False,
        coerce=lambda val: val == '1',
        empty_value=None,
        choices=(('0', 'No'), ('1', _('Yes'))),
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

        if formation:
            # The bachelor cycle continuation field is shown and required if the training is a bachelor
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
        label=_('Reasons'),
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

        all_reasons = RefusalReason.objects.select_related('category').all().order_by('category__order', 'order')
        category = getattr(self, 'reasons_category', None)
        if category:
            all_reasons = all_reasons.filter(category__name=category)

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
        elif self.fields['reasons'].required:
            self.add_error('reasons', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['other_reasons'] = []
            cleaned_data['reasons'] = []

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


class FreeAdditionalApprovalConditionForm(forms.Form):
    name_fr = forms.CharField(
        label=_('FR'),
        widget=forms.Textarea(attrs={'rows': 1}),
        required=False,
    )

    name_en = forms.CharField(
        label=_('EN'),
        widget=forms.Textarea(attrs={'rows': 1}),
        required=False,
    )

    def __init__(self, candidate_language, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.empty_permitted = False
        self.with_en_translation = candidate_language != settings.LANGUAGE_CODE_FR

        if not self.with_en_translation:
            self.fields['name_en'].widget.attrs['readonly'] = True

    def clean_name_fr(self):
        name = self.cleaned_data.get('name_fr')
        if not name:
            self.add_error('name_fr', FIELD_REQUIRED_MESSAGE)
        return name

    def clean_name_en(self):
        name = self.cleaned_data.get('name_en')
        if not name and self.with_en_translation:
            self.add_error('name_en', FIELD_REQUIRED_MESSAGE)
        return name


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
        help_text=_('You can only select courses that are managed by the program manager.'),
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

    def __init__(
        self,
        academic_year,
        educational_experience_program_name_by_uuid,
        current_training_uuid,
        *args,
        **kwargs,
    ):
        instance: Optional[GeneralEducationAdmission] = kwargs.get('instance', None)
        data = kwargs.get('data', {})
        initial = kwargs.setdefault('initial', {})

        if instance:
            initial['another_training'] = bool(instance.other_training_accepted_by_fac_id)

        super().__init__(*args, **kwargs)

        # Initialize conditions field
        self.academic_year = academic_year
        self.educational_experience_program_name_by_uuid = educational_experience_program_name_by_uuid
        self.data_existing_conditions = set()
        self.data_cv_experiences_conditions = set()
        self.predefined_approval_conditions = []
        self.predefined_approval_conditions = AdditionalApprovalCondition.objects.all()

        # Initialize additional approval conditions field
        if data:
            for condition in data.getlist(self.add_prefix('all_additional_approval_conditions'), []):
                if condition in educational_experience_program_name_by_uuid:
                    # UUID of the experience
                    self.data_cv_experiences_conditions.add(condition)
                else:
                    # UUID of the approval condition
                    self.data_existing_conditions.add(condition)

        elif instance:
            # Additional conditions
            existing_approval_conditions = instance.additional_approval_conditions.all()
            cv_experiences_conditions = instance.freeadditionalapprovalcondition_set.filter(
                related_experience__isnull=False
            )
            self.initial['all_additional_approval_conditions'] = [c.uuid for c in existing_approval_conditions] + [
                c.related_experience_id for c in cv_experiences_conditions
            ]

        all_additional_approval_conditions_choices = get_initial_choices_for_additional_approval_conditions(
            predefined_approval_conditions=self.predefined_approval_conditions,
            cv_experiences_conditions=educational_experience_program_name_by_uuid,
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

        other_training_forwarded_params = [forward.Const(academic_year, 'annee_academique')]

        if current_training_uuid:
            other_training_forwarded_params.append(forward.Const(current_training_uuid, 'excluded_training'))

        self.fields['other_training_accepted_by_fac'].widget.forward = other_training_forwarded_params
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

        cv_experiences_conditions = []

        base_translation_by_language = {}

        for language in [settings.LANGUAGE_CODE_FR, settings.LANGUAGE_CODE_EN]:
            with override(language):
                base_translation_by_language[language] = gettext('Graduation of {program_name}')

        for experience_uuid in self.data_cv_experiences_conditions:
            xp_name = self.educational_experience_program_name_by_uuid.get(experience_uuid, '')

            cv_experiences_conditions.append(
                {
                    'related_experience_id': experience_uuid,
                    'name_fr': str(base_translation_by_language[settings.LANGUAGE_CODE_FR]).format(
                        program_name=xp_name
                    ),
                    'name_en': str(base_translation_by_language[settings.LANGUAGE_CODE_EN]).format(
                        program_name=xp_name
                    ),
                }
            )

        self.cleaned_data['cv_experiences_additional_approval_conditions'] = cv_experiences_conditions

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
            cleaned_data['cv_experiences_additional_approval_conditions'] = []

        if cleaned_data.get('with_prerequisite_courses'):
            if cleaned_data.get('prerequisite_courses'):
                cleaned_data['prerequisite_courses'] = LearningUnitYear.objects.filter(
                    acronym__in=cleaned_data.get('prerequisite_courses', []),
                    academic_year__year=self.academic_year,
                ).values_list('uuid', flat=True)

        else:
            cleaned_data['prerequisite_courses'] = []
            cleaned_data['prerequisite_courses_fac_comment'] = ''

        if not cleaned_data.get('program_planned_years_number'):
            self.add_error('program_planned_years_number', FIELD_REQUIRED_MESSAGE)

        return cleaned_data


class PastExperiencesAdmissionRequirementForm(forms.ModelForm):
    admission_requirement_year = AcademicYearModelChoiceField(
        past_only=True,
        required=False,
        label=_('Admission requirement year'),
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
            'with_prerequisite_courses',
        ]
        widgets = {
            'with_prerequisite_courses': forms.RadioSelect(choices=[(True, _('Yes')), (False, _('No'))]),
        }


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
            'foreign_access_title_equivalency_restriction_about',
            'foreign_access_title_equivalency_state',
            'foreign_access_title_equivalency_effective_date',
        ]
        widgets = {
            'foreign_access_title_equivalency_effective_date': CustomDateInput,
            'foreign_access_title_equivalency_restriction_about': forms.TextInput,
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
        optional_fields = {
            'foreign_access_title_equivalency_restriction_about',
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
            if field in optional_fields:
                continue
            if field in displayed_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data[field] = self.default_values[field]

        return cleaned_data


class SicDecisionApprovalDocumentsForm(forms.Form):
    def __init__(
        self,
        documents: List[EmplacementDocumentDTO],
        instance: GeneralEducationAdmission,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        # Documents
        documents_choices = []
        initial_document_choices = []
        self.documents = {}

        for document in documents:
            if document.est_a_reclamer:
                label = document.libelle_avec_icone
                document_field = ChangeRequestDocumentForm.create_change_request_document_field(
                    label=label,
                    document_identifier=document.identifiant,
                    request_status=document.statut_reclamation,
                    proposition_uuid=instance.uuid,
                    only_limited_request_choices=False,
                    context=CONTEXT_GENERAL,
                )

                self.fields[document.identifiant] = document_field
                self.documents[document.identifiant] = document_field

                initial_document_choices.append(document.identifiant)
                documents_choices.append((document.identifiant, mark_safe(label)))


class SicDecisionApprovalForm(forms.ModelForm):
    SEPARATOR = ';'

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
            },
        ),
    )

    class Media:
        js = ('js/dependsOn.min.js',)

    class Meta:
        model = GeneralEducationAdmission
        fields = [
            'prerequisite_courses',
            'prerequisite_courses_fac_comment',
            'program_planned_years_number',
            'annual_program_contact_person_name',
            'annual_program_contact_person_email',
            'with_additional_approval_conditions',
            'with_prerequisite_courses',
            'tuition_fees_amount',
            'tuition_fees_amount_other',
            'tuition_fees_dispensation',
            'particular_cost',
            'rebilling_or_third_party_payer',
            'first_year_inscription_and_status',
            'is_mobility',
            'mobility_months_amount',
            'must_report_to_sic',
            'communication_to_the_candidate',
            'must_provide_student_visa_d',
        ]
        labels = {
            'annual_program_contact_person_name': _('First name and last name'),
            'annual_program_contact_person_email': pgettext_lazy('admission', 'Email'),
        }
        widgets = {
            'prerequisite_courses_fac_comment': CKEditorWidget(config_name='comment_link_only'),
            'with_prerequisite_courses': forms.RadioSelect(choices=[(True, _('Yes')), (False, _('No'))]),
            'with_additional_approval_conditions': forms.RadioSelect(choices=[(True, _('Yes')), (False, _('No'))]),
            'program_planned_years_number': forms.Select(
                choices=EMPTY_CHOICE_AS_LIST
                + [(number, number) for number in range(DUREE_MINIMALE_PROGRAMME, DUREE_MAXIMALE_PROGRAMME + 1)],
            ),
            'particular_cost': forms.TextInput(),
            'rebilling_or_third_party_payer': forms.TextInput(),
            'first_year_inscription_and_status': forms.TextInput(),
            'is_mobility': forms.Select(choices=[(None, '-'), (True, _('Yes')), (False, _('No'))]),
            'must_report_to_sic': forms.RadioSelect(choices=[(True, _('Yes')), (False, _('No'))]),
            'communication_to_the_candidate': CKEditorWidget(config_name='comment_link_only'),
            'must_provide_student_visa_d': forms.CheckboxInput,
        }

    def __init__(
        self,
        academic_year,
        educational_experience_program_name_by_uuid,
        candidate_nationality_is_no_ue_5: bool,
        *args,
        **kwargs,
    ):
        instance: Optional[GeneralEducationAdmission] = kwargs.get('instance', None)
        data = kwargs.get('data', {})

        super().__init__(*args, **kwargs)

        # Initialize conditions field
        self.is_admission = self.instance.type_demande == TypeDemande.ADMISSION.name
        self.is_vip = (
            self.instance.international_scholarship_id is not None
            or self.instance.erasmus_mundus_scholarship_id is not None
            or self.instance.double_degree_scholarship_id is not None
        )
        self.is_hue = not self.instance.candidate.country_of_citizenship.european_union
        self.is_assimilation = (
            self.instance.accounting
            and self.instance.accounting.assimilation_situation != TypeSituationAssimilation.AUCUNE_ASSIMILATION.name
        )
        self.academic_year = academic_year
        self.educational_experience_program_name_by_uuid = educational_experience_program_name_by_uuid
        self.data_existing_conditions = set()
        self.data_cv_experiences_conditions = set()
        self.predefined_approval_conditions = []
        self.predefined_approval_conditions = AdditionalApprovalCondition.objects.all()

        # Initialize additional approval conditions field
        if data:
            for condition in data.getlist(self.add_prefix('all_additional_approval_conditions'), []):
                if condition in educational_experience_program_name_by_uuid:
                    # UUID of the experience
                    self.data_cv_experiences_conditions.add(condition)
                else:
                    # UUID of the approval condition
                    self.data_existing_conditions.add(condition)

        elif instance:
            # Additional conditions
            existing_approval_conditions = instance.additional_approval_conditions.all()
            cv_experiences_conditions = instance.freeadditionalapprovalcondition_set.filter(
                related_experience__isnull=False
            )
            self.initial['all_additional_approval_conditions'] = [c.uuid for c in existing_approval_conditions] + [
                c.related_experience_id for c in cv_experiences_conditions
            ]

        all_additional_approval_conditions_choices = get_initial_choices_for_additional_approval_conditions(
            predefined_approval_conditions=self.predefined_approval_conditions,
            cv_experiences_conditions=educational_experience_program_name_by_uuid,
        )
        self.fields['all_additional_approval_conditions'].choices = all_additional_approval_conditions_choices
        self.fields['all_additional_approval_conditions'].widget.choices = all_additional_approval_conditions_choices

        # Initialize additional approval conditions field
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

        self.fields['tuition_fees_amount'].required = True
        self.fields['tuition_fees_amount'].choices = [(None, '-')] + self.fields['tuition_fees_amount'].choices

        self.fields['tuition_fees_dispensation'].required = True
        self.fields['tuition_fees_dispensation'].choices = [(None, '-')] + self.fields[
            'tuition_fees_dispensation'
        ].choices
        if not self.is_hue or self.is_assimilation:
            self.initial['tuition_fees_dispensation'] = DispenseOuDroitsMajores.NON_CONCERNE.name

        if not self.is_vip:
            del self.fields['particular_cost']
            del self.fields['rebilling_or_third_party_payer']
            del self.fields['first_year_inscription_and_status']

        if not self.is_hue:
            del self.fields['is_mobility']
            del self.fields['mobility_months_amount']
        else:
            self.fields['is_mobility'].required = False
            self.fields['mobility_months_amount'].required = False

        if self.is_admission and candidate_nationality_is_no_ue_5:
            self.initial['must_provide_student_visa_d'] = True
        else:
            del self.fields['must_provide_student_visa_d']

        if not self.is_admission:
            self.fields.pop('tuition_fees_amount', None)
            self.fields.pop('tuition_fees_amount_other', None)
            self.fields.pop('tuition_fees_dispensation', None)
            self.fields.pop('particular_cost', None)
            self.fields.pop('rebilling_or_third_party_payer', None)
            self.fields.pop('first_year_inscription_and_status', None)
            self.fields.pop('is_mobility', None)
            self.fields.pop('mobility_months_amount', None)
            self.fields.pop('must_report_to_sic', None)
            self.fields.pop('communication_to_the_candidate', None)
            self.fields.pop('must_provide_student_visa_d', None)
        else:
            self.initial['must_report_to_sic'] = False
            self.fields['must_report_to_sic'].required = True
            self.fields['program_planned_years_number'].required = True
            self.fields['communication_to_the_candidate'].required = False
            self.fields['with_additional_approval_conditions'].required = True
            self.fields['with_prerequisite_courses'].required = True

    def clean_all_additional_approval_conditions(self):
        # This field can contain uuids of existing conditions or free conditions as strings
        cleaned_data = self.cleaned_data.get('all_additional_approval_conditions', [])

        self.cleaned_data['additional_approval_conditions'] = list(self.data_existing_conditions)

        cv_experiences_conditions = []

        base_translation_by_language = {}

        for language in [settings.LANGUAGE_CODE_FR, settings.LANGUAGE_CODE_EN]:
            with override(language):
                base_translation_by_language[language] = gettext('Graduation of {program_name}')

        for experience_uuid in self.data_cv_experiences_conditions:
            xp_name = self.educational_experience_program_name_by_uuid.get(experience_uuid, '')

            cv_experiences_conditions.append(
                {
                    'related_experience_id': experience_uuid,
                    'name_fr': str(base_translation_by_language[settings.LANGUAGE_CODE_FR]).format(
                        program_name=xp_name
                    ),
                    'name_en': str(base_translation_by_language[settings.LANGUAGE_CODE_EN]).format(
                        program_name=xp_name
                    ),
                }
            )

        self.cleaned_data['cv_experiences_additional_approval_conditions'] = cv_experiences_conditions

        return cleaned_data

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get('with_additional_approval_conditions'):
            cleaned_data['all_additional_approval_conditions'] = []
            cleaned_data['additional_approval_conditions'] = []
            cleaned_data['cv_experiences_additional_approval_conditions'] = []

        if cleaned_data.get('with_prerequisite_courses'):
            if cleaned_data.get('prerequisite_courses'):
                cleaned_data['prerequisite_courses'] = LearningUnitYear.objects.filter(
                    acronym__in=cleaned_data.get('prerequisite_courses', []),
                    academic_year__year=self.academic_year,
                ).values_list('uuid', flat=True)

        else:
            cleaned_data['prerequisite_courses'] = []
            cleaned_data['prerequisite_courses_fac_comment'] = ''

        if cleaned_data.get('tuition_fees_amount') == DroitsInscriptionMontant.AUTRE.name:
            if not cleaned_data.get('tuition_fees_amount_other'):
                self.add_error(
                    'tuition_fees_amount_other',
                    ValidationError(
                        self.fields['tuition_fees_amount_other'].error_messages['required'],
                        code='required',
                    ),
                )

        if cleaned_data.get('is_mobility'):
            if not cleaned_data.get('mobility_months_amount'):
                self.add_error(
                    'mobility_months_amount',
                    ValidationError(
                        self.fields['mobility_months_amount'].error_messages['required'],
                        code='required',
                    ),
                )

        return cleaned_data


class SicDecisionRefusalForm(FacDecisionRefusalForm):
    refusal_type = forms.ChoiceField(
        label=_('Refusal type'),
        choices=EMPTY_CHOICE + TypeDeRefus.choices(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reasons'].required = False


class SicDecisionDerogationForm(forms.Form):
    dispensation_needed = forms.ChoiceField(
        label=_('Dispensation needed'),
        choices=BesoinDeDerogation.choices(),
        widget=forms.RadioSelect(
            attrs={
                'hx-trigger': 'changed',
            }
        ),
    )


class SicDecisionFinalRefusalForm(forms.Form):
    subject = forms.CharField(
        label=_('Message subject'),
    )
    body = AdmissionHTMLCharField(
        label=_('Message for the candidate'),
        widget=forms.Textarea(),
    )

    def __init__(self, with_email, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if with_email:
            self.fields['body'].widget.attrs['data-config'] = json.dumps(
                {
                    **settings.CKEDITOR_CONFIGS['osis_mail_template'],
                    'language': get_language(),
                }
            )
        else:
            del self.fields['body']
            del self.fields['subject']


class SicDecisionFinalApprovalForm(forms.Form):
    subject = forms.CharField(
        label=_('Message subject'),
    )
    body = AdmissionHTMLCharField(
        label=_('Message for the candidate'),
        widget=forms.Textarea(),
    )

    def __init__(self, *args, **kwargs):
        is_inscription = kwargs.pop('is_inscription')
        super().__init__(*args, **kwargs)
        if is_inscription:
            del self.fields['subject']
            del self.fields['body']
        else:
            self.fields['body'].widget.attrs['data-config'] = json.dumps(
                {
                    **settings.CKEDITOR_CONFIGS['osis_mail_template'],
                    'language': get_language(),
                }
            )


class FinancabilityDispensationRefusalForm(FacDecisionRefusalForm):
    def __init__(self, *args, **kwargs):
        self.reasons_category = FINANCABILITE_REFUS_CATEGORY

        super().__init__(*args, **kwargs)

        self.fields['reasons'].widget.free_options_placeholder = _(
            'Your past experiences does not ensure the expected garanties for success'
        )


class FinancabiliteApprovalForm(forms.ModelForm):
    class Meta:
        model = GeneralEducationAdmission
        fields = [
            'financability_rule',
        ]


class FinancabiliteDispensationForm(forms.Form):
    dispensation_status = forms.ChoiceField(
        label=_('Financability dispensation needed'),
        choices=DerogationFinancement.choices(),
        widget=forms.RadioSelect(),
    )

    def __init__(self, is_central_manager, is_program_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_central_manager and not is_program_manager:
            self.fields['dispensation_status'].disabled = True
        elif (
            not is_central_manager
            and self.initial['dispensation_status'] != DerogationFinancement.CANDIDAT_NOTIFIE.name
        ):
            self.fields['dispensation_status'].disabled = True


class FinancabiliteNotificationForm(forms.Form):
    subject = forms.CharField(
        label=_('Message subject'),
    )
    body = forms.CharField(
        label=_('Message for the candidate'),
        widget=forms.Textarea(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].widget.attrs['data-config'] = json.dumps(
            {
                **settings.CKEDITOR_CONFIGS['osis_mail_template'],
                'language': get_language(),
            }
        )


def can_edit_experience_authentication(checklist_experience_data):
    checklist_experience_data = checklist_experience_data or {}

    extra = checklist_experience_data.get('extra', {})

    return (
        checklist_experience_data.get('statut') == ChoixStatutChecklist.GEST_EN_COURS.name
        and extra.get('authentification') == '1'
    )


class SinglePastExperienceAuthenticationForm(forms.Form):
    state = forms.ChoiceField(
        label=_('Past experiences authentication'),
        choices=EtatAuthentificationParcours.choices(),
        required=False,
        widget=forms.RadioSelect,
    )

    def __init__(self, checklist_experience_data, *args, **kwargs):

        super().__init__(*args, **kwargs)

        checklist_experience_data = checklist_experience_data or {}

        extra = checklist_experience_data.get('extra', {})

        self.initial['state'] = extra.get('etat_authentification')

        self.prefix = extra.get('identifiant', '')

        self.fields['state'].disabled = not can_edit_experience_authentication(checklist_experience_data)
