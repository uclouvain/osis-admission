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
from django import forms
from django.utils.translation import gettext_lazy as _
from osis_document.contrib import FileUploadField

from admission.forms import REQUIRED_FIELD_CLASS
from admission.forms.specific_question import ConfigurableFormMixin
from base.forms.utils.file_field import MaxOneFileUploadField
from osis_profile.forms.experience_academique import (
    CurriculumAcademicExperienceForm,
    CurriculumEducationalExperienceYearForm, BaseFormSetWithCustomFormIndex,
)


class GlobalCurriculumForm(ConfigurableFormMixin):
    configurable_form_field_name = 'reponses_questions_specifiques'

    curriculum = MaxOneFileUploadField(
        label=_('Detailed curriculum vitae, dated and signed'),
        required=False,
    )
    equivalence_diplome = MaxOneFileUploadField(
        label=_(
            "Copy of equivalency decision issued by the French Community of Belgium making your bachelor's "
            "diploma (bac+5) equivalent to the academic rank of a corresponding master's degree."
        ),
        help_text=_(
            'You can find more information on the French Community webpage '
            '<a href="https://equisup.cfwb.be/" target="_blank">https://equisup.cfwb.be/</a>'
        ),
        required=False,
    )

    def __init__(
        self,
        display_equivalence: bool,
        display_curriculum: bool,
        require_equivalence: bool,
        require_curriculum: bool,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        if not display_equivalence:
            del self.fields['equivalence_diplome']

        elif require_equivalence:
            self.fields['equivalence_diplome'].widget.attrs['class'] = REQUIRED_FIELD_CLASS

        if not display_curriculum:
            del self.fields['curriculum']

        elif require_curriculum:
            self.fields['curriculum'].widget.attrs['class'] = REQUIRED_FIELD_CLASS

    def clean(self):
        cleaned_data = super().clean()

        cleaned_data.setdefault('curriculum', [])
        cleaned_data.setdefault('equivalence_diplome', [])
        cleaned_data.setdefault('reponses_questions_specifiques', {})

        return cleaned_data


class CurriculumAcademicExperienceAdmissionForm(CurriculumAcademicExperienceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, FileUploadField):
                field.required = True


class CurriculumEducationalExperienceYearAdmissionForm(CurriculumEducationalExperienceYearForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, FileUploadField):
                field.required = True


CurriculumEducationalExperienceYearAdmissionFormSet = forms.formset_factory(
    form=CurriculumEducationalExperienceYearAdmissionForm,
    formset=BaseFormSetWithCustomFormIndex,
    extra=0,
)
