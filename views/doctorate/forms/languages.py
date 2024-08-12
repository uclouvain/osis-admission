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
from django.shortcuts import resolve_url
from django.template import Context, Template
from django.views.generic import FormView

from admission.forms.admission.doctorate.languages import (
    DoctorateAdmissionLanguagesKnowledgeFormSet,
)
from admission.views.common.mixins import LoadDossierViewMixin, AdmissionFormMixin

__all__ = [
    "DoctorateAdmissionLanguagesFormView",
]


class DoctorateAdmissionLanguagesFormView(AdmissionFormMixin, LoadDossierViewMixin, FormView):
    template_name = 'admission/doctorate/forms/languages.html'
    permission_required = 'admission.change_admission_languages'
    form_class = DoctorateAdmissionLanguagesKnowledgeFormSet
    update_admission_author = True
    update_requested_documents = True

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        template_empty_form = """
            {% load bootstrap3 i18n static admission %}
            <div class="form-container">
              {% panel _("Add a language") %}
                {% bootstrap_field language_form.language %}
                {% bootstrap_field language_form.listening_comprehension %}
                {% bootstrap_field language_form.speaking_ability %}
                {% bootstrap_field language_form.writing_ability %}
                {% bootstrap_field_with_tooltip language_form.certificate %}
              {% endpanel %}
            </div>
        """
        template = Template(template_empty_form)
        context = Context({'language_form': context_data["form"].empty_form})

        context_data["empty_form"] = template.render(context)
        context_data["formset"] = context_data["form"]
        context_data["form"] = context_data["form"].empty_form

        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.admission.candidate
        return kwargs

    def form_valid(self, formset):
        formset.save()
        return super().form_valid(formset)

    def get_success_url(self):
        return self.next_url or resolve_url('admission:doctorate:languages', uuid=self.admission_uuid)
