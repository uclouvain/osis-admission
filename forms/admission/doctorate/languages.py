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
import json
from collections import defaultdict

from dal import forward
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Case, When
from django.forms import ModelChoiceField
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, get_language

from base.forms.utils.autocomplete import ModelSelect2
from base.forms.utils.file_field import MaxOneFileUploadField
from osis_profile.models.education import LanguageKnowledge
from osis_profile.models.enums.education import LanguageKnowledgeGrade
from reference.models.language import Language

MANDATORY_LANGUAGES = ['EN', 'FR']


class SliderWidget(forms.widgets.TextInput):
    def __init__(self, choices=None, attrs=None):
        self.mapping_enum_key_index = {}
        self.mapping_index_enum_key = {}

        for index, choice in enumerate(choices):
            current_index = str(index + 1)
            self.mapping_index_enum_key[current_index] = choice.name
            self.mapping_enum_key_index[choice.name] = current_index

        self.min_value = '1'

        attrs = attrs or {}
        attrs.update(
            {
                'data-provide': 'slider',
                'data-slider-ticks': json.dumps(list(self.mapping_index_enum_key.keys())),
                'data-slider-ticks-labels': json.dumps([choice.name for choice in choices]),
                'data-slider-min': self.min_value,
                'data-slider-max': str(len(choices)),
                'data-slider-step': '1',
            }
        )

        super().__init__(attrs)

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if value is None:
            return value
        return self.mapping_index_enum_key[value]

    def format_value(self, value):
        if value:
            value = self.mapping_enum_key_index[value]
        else:
            value = self.min_value
        self.attrs['data-slider-value'] = value
        return value

    class Media:
        js = ('admission/bootstrap-slider.min.js',)
        css = {
            'all': ('admission/bootstrap-slider.min.css',),
        }


class LanguageModelChoiceField(ModelChoiceField):
    @cached_property
    def translated_label_name(self):
        return {
            settings.LANGUAGE_CODE_FR: 'name',
            settings.LANGUAGE_CODE_EN: 'name_en',
        }[get_language()]

    def label_from_instance(self, obj):
        return getattr(obj, self.translated_label_name)


class DoctorateAdmissionLanguageForm(forms.ModelForm):
    language = LanguageModelChoiceField(
        label=_('Language'),
        widget=ModelSelect2(url='admission:autocomplete:language', forward=[forward.Const(val='id', dst='id_field')]),
        queryset=Language.objects.all(),
    )

    certificate = MaxOneFileUploadField(
        label=_('Certificate of language knowledge'),
        help_text=_(
            'If applicable, upload a language proficiency certificate in the format required by the specific '
            'provisions of your PhD committee.'
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_permitted = False

        if self.instance and self.instance.language:
            self.instance_language = self.fields['language'].label_from_instance(self.instance.language)
            self.is_required = self.instance.language.code in MANDATORY_LANGUAGES

            if self.is_required:
                self.fields['language'].widget = forms.HiddenInput()
                self.fields['language'].disabled = True

    class Meta:
        model = LanguageKnowledge
        widgets = {
            'listening_comprehension': SliderWidget(choices=LanguageKnowledgeGrade),
            'speaking_ability': SliderWidget(choices=LanguageKnowledgeGrade),
            'writing_ability': SliderWidget(choices=LanguageKnowledgeGrade),
        }
        fields = [
            'language',
            'listening_comprehension',
            'speaking_ability',
            'writing_ability',
            'certificate',
        ]

    class Media:
        js = ('js/jquery.formset.js',)


class DoctorateAdmissionLanguagesBaseFormset(forms.BaseModelFormSet):
    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.person = person
        self.queryset = (
            LanguageKnowledge.objects.filter(person=self.person)
            .select_related('language')
            .alias(
                relevancy=Case(
                    When(language__code='EN', then=2),
                    When(language__code='FR', then=1),
                    default=0,
                ),
            )
            .order_by('-relevancy', 'language__code')
        )

    def clean(self):
        if any(self.errors):
            return

        forms_by_language = defaultdict(list)
        missing_mandatory_languages = set(MANDATORY_LANGUAGES)

        for form in self.forms:
            # Associate the form with the current person
            if not form.instance.pk:
                form.instance.person = self.person

            code = form.cleaned_data.get('language').code
            forms_by_language[code].append(form)
            missing_mandatory_languages.discard(code)

        # Check that mandatory languages are set
        if missing_mandatory_languages:
            raise ValidationError(
                _('Mandatory languages are missing (%(languages)s).')
                % {'languages': ', '.join(missing_mandatory_languages)}
            )

        # Check that no language have been set more than once
        with_duplicates = False
        for language, current_forms in forms_by_language.items():
            if len(current_forms) > 1:
                with_duplicates = True
                for form in current_forms:
                    form.add_error('language', _('This language is set more than once.'))

        if with_duplicates:
            raise ValidationError(_('You cannot enter a language more than once, please correct the form.'))


DoctorateAdmissionLanguagesKnowledgeFormSet = forms.modelformset_factory(
    form=DoctorateAdmissionLanguageForm,
    formset=DoctorateAdmissionLanguagesBaseFormset,
    model=LanguageKnowledge,
    can_delete=True,
    extra=0,
)
