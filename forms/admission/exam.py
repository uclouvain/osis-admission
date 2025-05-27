# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from django import forms
from django.forms import ModelChoiceField

from base.forms.utils.academic_year_field import AcademicYearEndYearLabelModelChoiceField
from base.models.academic_year import AcademicYear
from osis_profile.models import Exam


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'certificate',
            'year',
        ]
        field_classes = {
            'year': AcademicYearEndYearLabelModelChoiceField,
        }

    def __init__(self, certificate_title, certificate_help_text, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['certificate'].label = certificate_title
        self.fields['certificate'].help_text = certificate_help_text
        self.fields['year'].queryset = AcademicYear.objects.filter(start_date__lte=datetime.date.today()).order_by('-year')
