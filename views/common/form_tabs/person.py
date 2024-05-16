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
from django.urls import reverse
from django.views.generic import UpdateView

from admission.ddd.admission.commands import ValiderTicketPersonneCommand
from admission.forms.admission.person import AdmissionPersonForm
from admission.views.common.mixins import AdmissionFormMixin, LoadDossierViewMixin
from osis_profile import BE_ISO_CODE
from reference.models.country import Country

__all__ = ['AdmissionPersonFormView']


class AdmissionPersonFormView(AdmissionFormMixin, LoadDossierViewMixin, UpdateView):
    template_name = 'admission/forms/person.html'
    permission_required = 'admission.change_admission_person'
    form_class = AdmissionPersonForm
    update_requested_documents = True
    update_admission_author = True

    def get_object(self):
        return self.admission.candidate

    def get_success_url(self):
        return self.next_url or reverse(
            f'admission:{self.current_context}:person',
            kwargs=self.kwargs,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['BE_ISO_CODE'] = Country.objects.get(iso_code=BE_ISO_CODE).pk
        return context

    def update_current_admission_on_form_valid(self, form, admission):
        # Update submitted profile with newer data
        if admission.submitted_profile:
            admission.submitted_profile['identification'] = {
                'last_name': form.cleaned_data.get('last_name'),
                'first_name': form.cleaned_data.get('first_name'),
                'gender': form.cleaned_data.get('gender'),
                'country_of_citizenship': form.cleaned_data.get('country_of_citizenship').iso_code
                if form.cleaned_data.get('country_of_citizenship')
                else '',
                'birth_date': form.cleaned_data.get('birth_date').isoformat()
                if form.cleaned_data.get('birth_date')
                else '',
            }

    def form_valid(self, form):
        form_valid = super().form_valid(form)

        from infrastructure.messages_bus import message_bus_instance
        message_bus_instance.invoke(ValiderTicketPersonneCommand(global_id=self.admission.candidate.global_id))

        return form_valid
