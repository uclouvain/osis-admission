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

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.ddd.admission.formation_generale.domain.model.enums import CHOIX_DIPLOME_OBTENU
from admission.forms import (
    AdmissionFileUploadField as FileUploadField,
    AdmissionModelCountryChoiceField,
)
from admission.forms import autocomplete
from admission.forms.doctorate.training.activity import AcademicYearField
from admission.forms.specific_question import ConfigurableFormMixin
from admission.utils import format_academic_year
from base.forms.utils import EMPTY_CHOICE
from base.models.academic_year import AcademicYear
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.enums.got_diploma import GotDiploma
from base.models.organization import Organization
from osis_profile.models import BelgianHighSchoolDiploma, ForeignHighSchoolDiploma
from osis_profile.models.enums.education import (
    BelgianCommunitiesOfEducation,
    HighSchoolDiplomaTypes,
    Equivalence,
    ForeignDiplomaTypes,
    EducationalType,
)
from reference.models.country import Country
from reference.models.language import Language


def got_diploma_dynamic_choices(current_year):
    """Return the choices with a dynamic value for the choice THIS_YEAR."""
    specific_values = {
        GotDiploma.THIS_YEAR.name: _('I will be graduating from secondary school during the %s academic year')
        % format_academic_year(current_year)
    }
    return tuple((x.name, specific_values.get(x.name, x.value)) for x in GotDiploma)


class BaseAdmissionEducationForm(ConfigurableFormMixin):
    graduated_from_high_school = forms.ChoiceField(
        label=_('Do you have a secondary school diploma?'),
        widget=forms.RadioSelect,
        help_text='{}<br><br>{}'.format(
            _(
                'Secondary education in Belgium is the level of education between the end of primary school and the '
                'beginning of higher education.'
            ),
            _(
                'The secondary school diploma is the Certificat d\'Enseignement Secondaire Superieur '
                '(CESS, Certificate of Higher Secondary Education). It is commonly referred to in many countries as '
                'the baccalaureat.'
            ),
        ),
    )
    graduated_from_high_school_year = AcademicYearField(
        label=_('Please indicate the academic year in which you obtained your degree'),
        widget=autocomplete.Select2,
        required=False,
        to_field_name='year',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_year = AcademicYear.objects.current()
        self.fields['graduated_from_high_school'].choices = got_diploma_dynamic_choices(self.current_year.year)
        self.fields['graduated_from_high_school_year'].queryset = self.fields[
            'graduated_from_high_school_year'
        ].queryset.filter(end_date__lte=datetime.date.today())

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('graduated_from_high_school') == GotDiploma.YES.name:

            if not cleaned_data.get('graduated_from_high_school_year'):
                self.add_error('graduated_from_high_school_year', FIELD_REQUIRED_MESSAGE)

        elif cleaned_data.get('graduated_from_high_school') == GotDiploma.THIS_YEAR.name:
            cleaned_data['graduated_from_high_school_year'] = self.current_year

        else:
            cleaned_data['graduated_from_high_school_year'] = None

        return cleaned_data

    class Media:
        js = ('js/dependsOn.min.js',)


class BachelorAdmissionEducationForm(BaseAdmissionEducationForm):
    diploma_type = forms.ChoiceField(
        label=pgettext_lazy('diploma_type', 'It is a diploma'),
        choices=HighSchoolDiplomaTypes.choices(),
        widget=forms.RadioSelect,
        required=False,
    )
    high_school_diploma = FileUploadField(
        label=_('Secondary school diploma'),
        max_files=1,
        required=False,
        help_text=_('Secondary school diploma or, if not available, a certificate of enrolment or school attendance.'),
    )
    first_cycle_admission_exam = FileUploadField(
        label=_('Certificate of passing the bachelor\'s course entrance exam'),
        max_files=1,
        required=False,
    )

    class Media:
        js = ('js/dependsOn.min.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        belgian_diploma = self.initial.get('belgian_diploma')
        foreign_diploma = self.initial.get('foreign_diploma')
        high_school_diploma_alternative = self.initial.get('high_school_diploma_alternative')

        diploma = belgian_diploma or foreign_diploma
        # Select the correct diploma type if one has been saved
        if diploma:
            self.fields['diploma_type'].initial = (
                HighSchoolDiplomaTypes.BELGIAN.name if belgian_diploma else HighSchoolDiplomaTypes.FOREIGN.name
            )
            self.fields['high_school_diploma'].initial = diploma.high_school_diploma
        elif high_school_diploma_alternative:
            self.fields[
                'first_cycle_admission_exam'
            ].initial = high_school_diploma_alternative.first_cycle_admission_exam

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('graduated_from_high_school') in CHOIX_DIPLOME_OBTENU and not cleaned_data.get(
            'diploma_type'
        ):
            self.add_error('diploma_type', FIELD_REQUIRED_MESSAGE)

        return cleaned_data


class BachelorAdmissionEducationBelgianDiplomaForm(forms.ModelForm):
    community = forms.ChoiceField(
        label=_('Belgian education community'),
        choices=EMPTY_CHOICE + BelgianCommunitiesOfEducation.choices(),
        widget=autocomplete.ListSelect2,
    )
    educational_type = forms.ChoiceField(
        label=_('Secondary education type'),
        choices=EMPTY_CHOICE + EducationalType.choices(),
        widget=autocomplete.ListSelect2,
        required=False,
    )
    has_other_educational_type = forms.BooleanField(
        label=_('Other education type'),
        required=False,
    )
    educational_other = forms.CharField(
        label=_('Name of the education type'),
        required=False,
    )
    institute = forms.ModelChoiceField(
        label=pgettext_lazy('curriculum', 'Institute'),
        required=False,
        help_text=_('You can specify the locality or postcode in your search.'),
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:high-school-institute',
            attrs={
                'data-html': True,
            },
            forward=['community'],
        ),
        queryset=Organization.objects.filter(establishment_type=EstablishmentTypeEnum.HIGH_SCHOOL.name),
    )
    other_institute = forms.BooleanField(
        label=_('My institute is not on this list'),
        required=False,
    )
    other_institute_name = forms.CharField(
        label=_('Other institute name'),
        required=False,
    )
    other_institute_address = forms.CharField(
        label=_('Other institute address'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['other_institute'] = bool(self.initial.get('other_institute_name'))
        self.initial['has_other_educational_type'] = bool(self.initial.get('educational_other'))

    class Meta:
        model = BelgianHighSchoolDiploma
        fields = [
            'community',
            'educational_type',
            'has_other_educational_type',
            'educational_other',
            'institute',
            'other_institute',
            'other_institute_name',
            'other_institute_address',
        ]

    def clean(self):
        cleaned_data = super().clean()
        community = cleaned_data.get('community')
        has_other_educational_type = cleaned_data.get('has_other_educational_type')

        if has_other_educational_type:
            cleaned_data['educational_type'] = ''
        else:
            cleaned_data['educational_other'] = ''

        if community == BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name:
            if has_other_educational_type:
                if not cleaned_data.get('educational_other'):
                    self.add_error('educational_other', FIELD_REQUIRED_MESSAGE)
            elif not cleaned_data.get('educational_type'):
                self.add_error('educational_type', FIELD_REQUIRED_MESSAGE)

        other_institute = cleaned_data.get('other_institute')
        if other_institute:
            if not cleaned_data['other_institute_name']:
                self.add_error('other_institute_name', FIELD_REQUIRED_MESSAGE)
            if not cleaned_data['other_institute_address']:
                self.add_error('other_institute_address', FIELD_REQUIRED_MESSAGE)

        elif not cleaned_data.get('institute'):
            institute_error_msg = _('Please choose the institute or specify another institute')
            self.add_error('institute', institute_error_msg)
            self.add_error('other_institute', '')

        return cleaned_data


class BachelorAdmissionEducationForeignDiplomaForm(forms.ModelForm):
    foreign_diploma_type = forms.ChoiceField(
        label=_('What diploma have you obtained (or will obtain)?'),
        choices=ForeignDiplomaTypes.choices(),
        widget=forms.RadioSelect,
        help_text=mark_safe(
            "- <a href='https://www.eursc.eu/fr' target='_blank'>Schola Europae</a><br>"
            "- <a href='https://www.ibo.org/fr/programmes/find-an-ib-school' target='_blank'>IBO</a>"
        ),
    )
    equivalence = forms.ChoiceField(
        label=_('Has this diploma been recognised as equivalent by the French Community of Belgium?'),
        required=False,
        choices=Equivalence.choices(),
        widget=forms.RadioSelect,
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
    other_linguistic_regime = forms.CharField(
        label=_('If other language regime, specify'),
        required=False,
    )
    country = AdmissionModelCountryChoiceField(
        label=_('Organising country'),
        queryset=Country.objects.all(),
        to_field_name='iso_code',
    )
    high_school_transcript = FileUploadField(
        label=_('A transcript for your last year of secondary school'),
        max_files=1,
        required=False,
    )
    high_school_transcript_translation = FileUploadField(
        label=_(
            'A translation of your official transcript of marks for your final year of secondary school '
            'by a sworn translator'
        ),
        max_files=1,
        required=False,
    )
    high_school_diploma_translation = FileUploadField(
        label=_('A translation of your secondary school diploma by a sworn translator'),
        max_files=1,
        required=False,
    )
    final_equivalence_decision_not_ue = FileUploadField(
        label=_(
            'Copy of both sides of the definitive equivalency decision by the Ministry of the French-speaking '
            'Community of Belgium (possibly accompanied by the DAES or the undergraduate studies exam, if your '
            'equivalency does not confer eligibility for the desired programme)'
        ),
        help_text=_(
            'For any secondary school diploma from a country outside the European Union, the application for admission '
            '<strong>must contain the equivalency</strong> of your diploma issued by the '
            '<a href="http://www.equivalences.cfwb.be/" target="_blank">French Community</a> of Belgium.'
        ),
        max_files=2,
        required=False,
    )
    final_equivalence_decision_ue = FileUploadField(
        label=_(
            'Copy of both sides of the definitive equivalency decision (accompanied, where applicable, by the DAES '
            'or undergraduate exam, in the case of restrictive equivalency)'
        ),
        help_text=_(
            'If you have a final equivalence decision issued by the '
            '<a href="http://www.equivalences.cfwb.be/" target="_blank">French Community</a> of Belgium, you must '
            'provide a double-sided copy of this document.'
        ),
        max_files=2,
        required=False,
    )
    equivalence_decision_proof = FileUploadField(
        label=_('Proof of equivalency request'),
        help_text=_(
            'If you do not yet have a final equivalency decision from the <a href="http://www.equivalences.cfwb.be/" '
            'target="_blank">French Community</a> of Belgium, provide a copy of both sides of it as soon as you '
            'receive it. In the meantime, you will be asked to provide proof that you have indeed requested it: postal '
            'receipt and proof of payment, acknowledgement of receipt of the application, etc.'
        ),
        max_files=1,
        required=False,
    )

    class Meta:
        model = ForeignHighSchoolDiploma
        fields = [
            'foreign_diploma_type',
            'equivalence',
            'linguistic_regime',
            'other_linguistic_regime',
            'country',
            'high_school_transcript',
            'high_school_transcript_translation',
            'high_school_diploma_translation',
            'final_equivalence_decision_not_ue',
            'final_equivalence_decision_ue',
            'equivalence_decision_proof',
        ]

    def __init__(self, is_med_dent_training, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.is_med_dent_training = is_med_dent_training

        # Initialize the fields which are not automatically mapped and add additional data
        if self.instance:
            if self.instance.country_id:
                self.fields['country'].is_ue_country = self.instance.country.european_union
                self.initial['country'] = self.instance.country.iso_code

            if self.instance.linguistic_regime_id:
                self.initial['linguistic_regime'] = self.instance.linguistic_regime.code

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get('linguistic_regime') and not cleaned_data.get('other_linguistic_regime'):
            self.add_error('linguistic_regime', _('Please choose the language regime or specify another regime.'))

        if cleaned_data.get('country'):
            self.fields['country'].is_ue_country = cleaned_data['country'].european_union

        if cleaned_data.get('foreign_diploma_type') == ForeignDiplomaTypes.NATIONAL_BACHELOR.name:
            # Equivalence
            if (
                getattr(self.fields['country'], 'is_ue_country', False) or self.is_med_dent_training
            ) and not cleaned_data.get('equivalence'):
                self.add_error('equivalence', FIELD_REQUIRED_MESSAGE)

        return cleaned_data
