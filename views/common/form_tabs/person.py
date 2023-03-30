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
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import UpdateView

from admission.ddd import BE_ISO_CODE
from admission.forms.admission.person import AdmissionPersonForm
from admission.templatetags.admission import CONTEXT_GENERAL, CONTEXT_DOCTORATE, CONTEXT_CONTINUING
from admission.views.doctorate.mixins import LoadDossierViewMixin
from base.models.enums.person_address_type import PersonAddressType
from base.models.person_address import PersonAddress
from reference.models.country import Country

__all__ = ['AdmissionPersonFormView']


class AdmissionPersonFormView(LoadDossierViewMixin, UpdateView):
    template_name = 'admission/forms/person.html'
    permission_required_by_context = {
        CONTEXT_DOCTORATE: 'admission.change_doctorateadmission_person',
        CONTEXT_GENERAL: 'admission.change_generaleducationadmission_person',
        CONTEXT_CONTINUING: 'admission.change_continuingeducationadmission_person',
    }
    form_class = AdmissionPersonForm

    def get_object(self):
        return self.admission.candidate

    def get_success_url(self):
        return reverse(f'admission:{self.current_context}:person', kwargs=self.kwargs)

    @cached_property
    def resides_in_belgium(self):
        return PersonAddress.objects.filter(
            person=self.admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
            country__iso_code=BE_ISO_CODE,
        ).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resides_in_belgium'] = self.resides_in_belgium
        context['BE_ISO_CODE'] = Country.objects.get(iso_code=BE_ISO_CODE).pk
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['resides_in_belgium'] = self.resides_in_belgium
        return kwargs
