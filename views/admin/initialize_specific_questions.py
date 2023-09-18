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
from django import forms
from django.contrib import messages
from django.core.management import call_command
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import FormView

from admission.management.commands.initialize_specific_questions import EducationGroupNotFoundException
from base.models.academic_year import AcademicYear
from osis_role.contrib.views import PermissionRequiredMixin

__all__ = ['InitializeSpecificQuestionsFormView']


class InitializeSpecificQuestionsForm(forms.Form):
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all().order_by('-year'),
        label=_('Academic year'),
    )


class InitializeSpecificQuestionsFormView(PermissionRequiredMixin, FormView):
    urlpatterns = 'initialize-specific-questions'
    form_class = InitializeSpecificQuestionsForm
    template_name = 'admission/admin/initialize_specific_questions.html'
    permission_required = 'admission.initialize_specific_questions'

    def get_success_url(self) -> str:
        return reverse('admin:admission_admissionformitem_changelist')

    def form_valid(self, form):
        try:
            call_command('initialize_specific_questions', form.cleaned_data.get('academic_year').year)
            messages.success(self.request, gettext('Initialization of the predefined specific questions completed.'))
        except EducationGroupNotFoundException as e:
            messages.warning(
                self.request,
                f'{gettext("Initialization of the predefined specific questions completed.")} {e.message}',
            )
        return super().form_valid(form)
