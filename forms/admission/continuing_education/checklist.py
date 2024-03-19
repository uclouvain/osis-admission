# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django import forms

from admission.contrib.models import ContinuingEducationAdmission


class StudentReportForm(forms.ModelForm):
    class Meta:
        model = ContinuingEducationAdmission
        fields = [
            'interested_mark',
            'edition',
            'in_payement_order',
            'reduced_rights',
            'payed_by_training_cheque',
            'cep',
            'payement_spread',
            'training_spread',
            'experience_knowledge_valorisation',
            'assessment_test_presented',
            'assessment_test_succeeded',
            'certificate_provided',
            'tff_label',
        ]
        widgets = {
            'interested_mark': forms.CheckboxInput(),
            'in_payement_order': forms.CheckboxInput(),
            'reduced_rights': forms.CheckboxInput(),
            'payed_by_training_cheque': forms.CheckboxInput(),
            'cep': forms.CheckboxInput(),
            'payement_spread': forms.CheckboxInput(),
            'training_spread': forms.CheckboxInput(),
            'experience_knowledge_valorisation': forms.CheckboxInput(),
            'assessment_test_presented': forms.CheckboxInput(),
            'assessment_test_succeeded': forms.CheckboxInput(),
            'certificate_provided': forms.CheckboxInput(),
            'tff_label': forms.TextInput(),
        }
