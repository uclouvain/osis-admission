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

from copy import deepcopy
from datetime import datetime

from dal import autocomplete
from django import forms
from django.forms import BaseFormSet
from django.utils.dates import MONTHS_ALT
from django.utils.translation import gettext_lazy as _, pgettext_lazy as __, pgettext_lazy

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.ddd import BE_ISO_CODE, REGIMES_LINGUISTIQUES_SANS_TRADUCTION
from admission.forms import (
    EMPTY_CHOICE,
    AdmissionFileUploadField as FileUploadField,
    RadioBooleanField,
    CustomDateInput,
    get_example_text,
    FORM_SET_PREFIX,
    AdmissionModelCountryChoiceField,
)
from admission.forms.doctorate.training.activity import AcademicYearField
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.organization import Organization
from osis_profile.models import EducationalExperience
from osis_profile.models.enums.curriculum import (
    ActivityType,
    ActivitySector,
    EvaluationSystem,
    TranscriptType,
    Grade,
    Result,
)
from reference.models.country import Country
from reference.models.diploma_title import DiplomaTitle
from reference.models.language import Language

MINIMUM_YEAR = 1900


def year_choices():
    return [EMPTY_CHOICE[0]] + [(year, year) for year in range(datetime.today().year, MINIMUM_YEAR, -1)]


def month_choices():
    return [EMPTY_CHOICE[0]] + [(index, month) for index, month in MONTHS_ALT.items()]


class AdmissionCurriculumProfessionalExperienceForm(forms.Form):
    start_date_month = forms.ChoiceField(
        choices=month_choices,
        label=_('Month'),
        widget=autocomplete.Select2(),
    )
    end_date_month = forms.ChoiceField(
        choices=month_choices,
        label=_('Month'),
        widget=autocomplete.Select2(),
    )
    start_date_year = forms.ChoiceField(
        choices=year_choices,
        label=_('Year'),
        widget=autocomplete.Select2(),
    )
    end_date_year = forms.ChoiceField(
        choices=year_choices,
        label=_('Year'),
        widget=autocomplete.Select2(),
    )
    type = forms.ChoiceField(
        choices=EMPTY_CHOICE + ActivityType.choices(),
        label=pgettext_lazy('admission', 'Type'),
    )
    role = forms.CharField(
        label=__('curriculum', 'Function'),
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _('e.g.: Librarian'),
            },
        ),
    )
    sector = forms.ChoiceField(
        choices=EMPTY_CHOICE + ActivitySector.choices(),
        label=_('Sector'),
        required=False,
    )
    institute_name = forms.CharField(
        label=_('Employer'),
        required=False,
    )
    certificate = FileUploadField(
        label=_('Certificate'),
        required=False,
    )
    activity = forms.CharField(
        label=_('Activity'),
        required=False,
    )

    def __init__(self, is_continuing, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_continuing = is_continuing
        if self.is_continuing:
            self.fields['certificate'].disabled = True
            self.fields['certificate'].widget = forms.MultipleHiddenInput()

    class Media:
        js = ('js/dependsOn.min.js',)

    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data.get('start_date_month')
            and cleaned_data.get('end_date_month')
            and cleaned_data.get('start_date_year')
            and cleaned_data.get('start_date_month')
        ):
            start_date_month = int(cleaned_data.get('start_date_month'))
            end_date_month = int(cleaned_data.get('end_date_month'))
            start_date_year = int(cleaned_data.get('start_date_year'))
            end_date_year = int(cleaned_data.get('end_date_year'))

            if start_date_year > end_date_year or (
                start_date_year == end_date_year and start_date_month > end_date_month
            ):
                self.add_error(None, _("The start date must be earlier than or the same as the end date."))

        activity_type = cleaned_data.get('type')

        work_fields = ['role', 'sector', 'institute_name']

        if activity_type == ActivityType.WORK.name:
            for field in work_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
        else:
            for field in work_fields:
                cleaned_data[field] = ''

        if activity_type == ActivityType.OTHER.name:
            if not cleaned_data['activity']:
                self.add_error('activity', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['activity'] = ''

        return cleaned_data


class ByContextAdmissionFormMixin:
    """
    Hide and disable the fields that are not in the current context.
    """

    def __init__(self, current_context, fields_by_context, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields_by_context = fields_by_context
        self.current_context_fields = self.fields_by_context[current_context]

        self.disable_fields_other_contexts()

    def disable_fields_other_contexts(self):
        """Disable and hide fields specific to other contexts."""
        for field in self.fields:
            if field not in self.current_context_fields:
                self.fields[field].disabled = True
                self.fields[field].widget = self.fields[field].hidden_widget()

    def add_error(self, field, error):
        if field and self.fields[field].disabled:
            return
        super().add_error(field, error)


EDUCATIONAL_EXPERIENCE_BASE_FIELDS = {
    'start',
    'end',
    'country',
    'other_institute',
    'institute_name',
    'institute_address',
    'institute',
    'program',
    'fwb_equivalent_program',
    'other_program',
    'education_name',
    'obtained_diploma',
    'graduate_degree',
}

EDUCATIONAL_EXPERIENCE_GENERAL_FIELDS = {
    'evaluation_type',
    'linguistic_regime',
    'transcript_type',
    'obtained_grade',
    'graduate_degree_translation',
    'transcript',
    'transcript_translation',
}

EDUCATIONAL_EXPERIENCE_DOCTORATE_FIELDS = {
    'expected_graduation_date',
    'rank_in_diploma',
    'dissertation_title',
    'dissertation_score',
    'dissertation_summary',
}

EDUCATIONAL_EXPERIENCE_FIELDS_BY_CONTEXT = {
    'doctorate': EDUCATIONAL_EXPERIENCE_BASE_FIELDS
    | EDUCATIONAL_EXPERIENCE_GENERAL_FIELDS
    | EDUCATIONAL_EXPERIENCE_DOCTORATE_FIELDS,
    'general-education': EDUCATIONAL_EXPERIENCE_BASE_FIELDS | EDUCATIONAL_EXPERIENCE_GENERAL_FIELDS,
    'continuing-education': EDUCATIONAL_EXPERIENCE_BASE_FIELDS,
}


class AdmissionCurriculumAcademicExperienceForm(ByContextAdmissionFormMixin, forms.ModelForm):
    start = AcademicYearField(
        label=_('Start'),
        widget=autocomplete.Select2(),
        past_only=True,
        to_field_name='year',
    )

    end = AcademicYearField(
        label=pgettext_lazy('admission', 'End'),
        widget=autocomplete.Select2(),
        past_only=True,
        to_field_name='year',
    )

    country = AdmissionModelCountryChoiceField(
        label=_('Country'),
        queryset=Country.objects.all(),
        to_field_name='iso_code',
    )

    other_institute = forms.BooleanField(
        label=_('Other institute'),
        required=False,
    )

    institute_name = forms.CharField(
        label=_('Institute name'),
        required=False,
    )

    institute_address = forms.CharField(
        label=_('Institute address'),
        required=False,
    )

    institute = forms.ModelChoiceField(
        label=_('Institute'),
        required=False,
        queryset=Organization.objects.filter(
            establishment_type__in=[
                EstablishmentTypeEnum.NON_UNIVERSITY_HIGHER.name,
                EstablishmentTypeEnum.UNIVERSITY.name,
            ],
        ),
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:superior-institute',
            forward=['country'],
            attrs={
                'data-html': True,
            },
        ),
    )

    program = forms.ModelChoiceField(
        label=pgettext_lazy('admission', 'Course'),
        required=False,
        queryset=DiplomaTitle.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='admission:autocomplete:diploma-title',
        ),
    )

    fwb_equivalent_program = forms.ModelChoiceField(
        label=_('FWB equivalent course'),
        required=False,
        queryset=DiplomaTitle.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='admission:autocomplete:diploma-title',
        ),
    )

    other_program = forms.BooleanField(
        label=_('Other programme'),
        required=False,
    )

    education_name = forms.CharField(
        label=_('Course name'),
        required=False,
    )

    evaluation_type = forms.ChoiceField(
        choices=EMPTY_CHOICE + EvaluationSystem.choices(),
        label=_('Evaluation system'),
    )

    linguistic_regime = forms.ModelChoiceField(
        label=_('Language regime'),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='admission:autocomplete:language',
        ),
        queryset=Language.objects.all(),
        to_field_name='code',
    )

    transcript_type = forms.ChoiceField(
        choices=EMPTY_CHOICE + TranscriptType.choices(),
        label=_('Transcript type'),
    )
    obtained_diploma = RadioBooleanField(
        label=_('Did you graduate from this course?'),
    )
    obtained_grade = forms.ChoiceField(
        choices=EMPTY_CHOICE + Grade.choices(),
        label=pgettext_lazy('admission', 'Grade'),
        required=False,
    )
    graduate_degree = FileUploadField(
        label=_('Diploma'),
        required=False,
    )
    graduate_degree_translation = FileUploadField(
        label=_('Diploma translation'),
        required=False,
    )
    transcript = FileUploadField(
        label=_('Transcript'),
        required=False,
    )
    transcript_translation = FileUploadField(
        label=_('Transcript translation'),
        required=False,
    )
    rank_in_diploma = forms.CharField(
        label=_('Rank in diploma'),
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _('e.g.: 5th out of 30'),
            },
        ),
    )
    expected_graduation_date = forms.DateField(
        help_text=_('Date on which you expect to graduate.'),
        label=_('Expected graduation date (signed diploma)'),
        required=False,
        widget=CustomDateInput(),
    )
    dissertation_title = forms.CharField(
        label=pgettext_lazy('admission', 'Dissertation title'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 3,
            },
        ),
    )
    dissertation_score = forms.CharField(
        label=_('Dissertation mark'),
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': get_example_text('15/20'),
            },
        ),
    )
    dissertation_summary = FileUploadField(
        label=_('Dissertation summary'),
        required=False,
    )

    class Media:
        js = [
            'js/dependsOn.min.js',
            'js/jquery.mask.min.js',
        ]

    class Meta:
        model = EducationalExperience
        exclude = [
            'person',
            'uuid',
            'external_id',
            'study_system',
        ]

    def __init__(self, start, end, *args, **kwargs):
        kwargs['fields_by_context'] = deepcopy(EDUCATIONAL_EXPERIENCE_FIELDS_BY_CONTEXT)

        kwargs.setdefault('initial', {})

        kwargs['initial'].setdefault('start', start)
        kwargs['initial'].setdefault('end', end)

        super().__init__(*args, **kwargs)

        if self.instance:
            # Initialize the fields which are not automatically mapped and add additional data
            if self.instance.country_id:
                self.fields['country'].is_ue_country = self.instance.country.european_union
                self.initial['country'] = self.instance.country.iso_code
            if self.instance.program_id:
                self.fields['program'].cycle = self.instance.program.cycle
            if self.instance.fwb_equivalent_program_id:
                self.fields['fwb_equivalent_program'].cycle = self.instance.fwb_equivalent_program.cycle
            if self.instance.institute_id:
                self.fields['institute'].community = self.instance.institute.community
            if self.instance.linguistic_regime_id:
                self.initial['linguistic_regime'] = self.instance.linguistic_regime.code

            self.initial['other_program'] = bool(self.instance.education_name)
            self.initial['other_institute'] = bool(self.instance.institute_name)

    def clean(self):
        cleaned_data = super().clean()

        country = cleaned_data.get('country')
        be_country = bool(country and country.iso_code == BE_ISO_CODE)

        obtained_diploma = cleaned_data.get('obtained_diploma')

        global_transcript = cleaned_data.get('transcript_type') == TranscriptType.ONE_FOR_ALL_YEARS.name

        # Date fields
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        if start and end and start.year > end.year:
            self.add_error(None, _("The start date must be earlier than or the same as the end date."))

        # Institute fields
        self.clean_data_institute(cleaned_data)

        # Transcript field
        if not global_transcript:
            cleaned_data['transcript'] = []
            cleaned_data['transcript_translation'] = []

        self.clean_data_diploma(cleaned_data, obtained_diploma)

        if be_country:
            self.clean_data_be(cleaned_data)
        elif country:
            self.clean_data_foreign(cleaned_data)

        if cleaned_data.get('country'):
            self.fields['country'].is_ue_country = cleaned_data['country'].european_union

        if cleaned_data.get('program'):
            self.fields['program'].cycle = cleaned_data['program'].cycle

        if cleaned_data.get('fwb_equivalent_program'):
            self.fields['fwb_equivalent_program'].cycle = cleaned_data['fwb_equivalent_program'].cycle

        if cleaned_data.get('institute'):
            self.fields['institute'].community = cleaned_data['institute'].community
            cleaned_data['study_system'] = cleaned_data['institute'].teaching_type

        return cleaned_data

    def clean_data_diploma(self, cleaned_data, obtained_diploma):
        if obtained_diploma:
            for field in [
                'obtained_grade',
                'expected_graduation_date',
                'dissertation_title',
                'dissertation_score',
            ]:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['expected_graduation_date'] = None
            cleaned_data['dissertation_title'] = ''
            cleaned_data['dissertation_score'] = ''
            cleaned_data['dissertation_summary'] = []
            cleaned_data['graduate_degree'] = []
            cleaned_data['graduate_degree_translation'] = []
            cleaned_data['rank_in_diploma'] = ''

    def clean_data_institute(self, cleaned_data):
        institute = cleaned_data.get('institute')
        other_institute = cleaned_data.get('other_institute')
        if other_institute:
            if not cleaned_data.get('institute_name'):
                self.add_error('institute_name', FIELD_REQUIRED_MESSAGE)
            if not cleaned_data.get('institute_address'):
                self.add_error('institute_address', FIELD_REQUIRED_MESSAGE)

            cleaned_data['institute'] = None

        else:
            if not institute:
                self.add_error('institute', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['institute'] = institute

            cleaned_data['institute_address'] = ''
            cleaned_data['institute_name'] = ''

    def clean_data_foreign(self, cleaned_data):
        # Program field
        if not cleaned_data.get('education_name'):
            self.add_error('education_name', FIELD_REQUIRED_MESSAGE)
        # Linguistic fields
        linguistic_regime = cleaned_data.get('linguistic_regime')
        if not linguistic_regime:
            self.add_error('linguistic_regime', FIELD_REQUIRED_MESSAGE)
        if not linguistic_regime or linguistic_regime.code in REGIMES_LINGUISTIQUES_SANS_TRADUCTION:
            cleaned_data['graduate_degree_translation'] = []
            cleaned_data['transcript_translation'] = []
        # Clean belgian fields
        cleaned_data['program'] = None

    def clean_data_be(self, cleaned_data):
        # Program fields
        if cleaned_data.get('other_program'):
            if not cleaned_data.get('education_name'):
                self.add_error('education_name', FIELD_REQUIRED_MESSAGE)
            cleaned_data['program'] = None
        else:
            if not cleaned_data.get('program'):
                self.add_error('program', FIELD_REQUIRED_MESSAGE)
            cleaned_data['fwb_equivalent_program'] = None
            cleaned_data['education_name'] = ''
        # Clean foreign fields
        cleaned_data['linguistic_regime'] = None
        cleaned_data['graduate_degree_translation'] = []
        cleaned_data['transcript_translation'] = []


MINIMUM_CREDIT_NUMBER = 0


EDUCATIONAL_EXPERIENCE_YEAR_CONTINUING_FIELDS = {
    'academic_year',
}

EDUCATIONAL_EXPERIENCE_YEAR_FIELDS = {
    'academic_year',
    'is_enrolled',
    'result',
    'registered_credit_number',
    'acquired_credit_number',
    'transcript',
    'transcript_translation',
    'with_block_1',
    'with_complement',
    'fwb_registered_credit_number',
    'fwb_acquired_credit_number',
    'with_reduction',
    'is_102_change_of_course',
}

EDUCATIONAL_EXPERIENCE_YEAR_FIELDS_BY_CONTEXT = {
    'doctorate': EDUCATIONAL_EXPERIENCE_YEAR_FIELDS,
    'general-education': EDUCATIONAL_EXPERIENCE_YEAR_FIELDS,
    'continuing-education': EDUCATIONAL_EXPERIENCE_YEAR_CONTINUING_FIELDS,
}


class AdmissionCurriculumEducationalExperienceYearForm(ByContextAdmissionFormMixin, forms.Form):
    academic_year = forms.IntegerField(
        initial=FORM_SET_PREFIX,
        label=_('Academic year'),
        widget=forms.HiddenInput(),
    )
    is_enrolled = forms.BooleanField(
        initial=True,
        label=_('Enrolled'),
        required=False,
    )
    result = forms.ChoiceField(
        choices=EMPTY_CHOICE + Result.choices(),
        label=_('Result'),
        required=False,
    )
    registered_credit_number = forms.FloatField(
        label=_('Registered credits'),
        required=False,
        localize=True,
    )
    acquired_credit_number = forms.FloatField(
        label=_('Credits earned'),
        required=False,
        localize=True,
    )
    transcript = FileUploadField(
        label=_('Transcript'),
        max_files=1,
        required=False,
    )
    transcript_translation = FileUploadField(
        label=_('Transcript translation'),
        max_files=1,
        required=False,
    )
    with_block_1 = forms.BooleanField(
        label=_('Block 1'),
        required=False,
    )
    with_complement = forms.BooleanField(
        label=_('Complement'),
        required=False,
    )
    fwb_registered_credit_number = forms.FloatField(
        label=_('FWB - Registered credits'),
        required=False,
        localize=True,
    )
    fwb_acquired_credit_number = forms.FloatField(
        label=_('FWB - Credits earned'),
        required=False,
        localize=True,
    )
    with_reduction = forms.BooleanField(
        label=_('Reduction'),
        required=False,
    )
    is_102_change_of_course = forms.BooleanField(
        label=_('102 change of course'),
        required=False,
    )

    def __init__(self, current_year, prefix_index_start=0, **kwargs):
        kwargs['fields_by_context'] = EDUCATIONAL_EXPERIENCE_YEAR_FIELDS_BY_CONTEXT
        super().__init__(**kwargs)
        academic_year = self.data.get(self.add_prefix('academic_year'), self.initial.get('academic_year'))
        if academic_year and int(academic_year) < current_year:
            self.fields['result'].choices = EMPTY_CHOICE + Result.choices_for_past_years()

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('is_enrolled') and not cleaned_data.get('result'):
            self.add_error('result', FIELD_REQUIRED_MESSAGE)

        with_block_1 = cleaned_data.get('with_block_1')
        with_complement = cleaned_data.get('with_complement')

        if not with_block_1 and not with_complement:
            cleaned_data['fwb_registered_credit_number'] = None
            cleaned_data['fwb_acquired_credit_number'] = None

        fwb_registered_credit_number = cleaned_data.get('fwb_registered_credit_number')
        fwb_acquired_credit_number = cleaned_data.get('fwb_acquired_credit_number')

        if fwb_acquired_credit_number is not None:
            if fwb_acquired_credit_number < MINIMUM_CREDIT_NUMBER:
                self.add_error(
                    'fwb_acquired_credit_number',
                    _("The number of credits earned must be greater than or equal to 0."),
                )
            elif fwb_registered_credit_number and fwb_acquired_credit_number > fwb_registered_credit_number:
                self.add_error(
                    'fwb_acquired_credit_number',
                    _("The number of credits earned must be less than or equal to the number of credits registered."),
                )

        if fwb_registered_credit_number is not None and fwb_registered_credit_number <= MINIMUM_CREDIT_NUMBER:
            self.add_error(
                'fwb_registered_credit_number',
                _("The number of credits registered must be greater than 0."),
            )

        return cleaned_data


class BaseFormSetWithCustomFormIndex(BaseFormSet):
    def add_prefix(self, index):
        return super().add_prefix(
            self.form_kwargs.get('prefix_index_start') - index if isinstance(index, int) else index
        )


AdmissionCurriculumEducationalExperienceYearFormSet = forms.formset_factory(
    form=AdmissionCurriculumEducationalExperienceYearForm,
    formset=BaseFormSetWithCustomFormIndex,
    extra=0,
)
