# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.views.common.mixins import AdmissionFormMixin, LoadDossierViewMixin
from base.models.person import Person
from osis_profile.views.coordonnees import CoordonneesFormView

__all__ = ['AdmissionCoordonneesFormView']


class AdmissionCoordonneesFormView(AdmissionFormMixin, LoadDossierViewMixin, CoordonneesFormView):
    template_name = 'admission/forms/coordonnees.html'
    permission_required = 'admission.change_admission_coordinates'
    update_admission_author = True

    @property
    def person(self) -> Person:
        return self.admission.candidate

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['proposition_fusion'] = self.proposition_fusion
        return context_data

    def update_current_admission_on_form_valid(self, form, admission):
        # Update submitted profile with newer data
        if admission.submitted_profile:
            address = (
                form['contact'].address_data_to_save
                if form['main_form'].cleaned_data['show_contact']
                else form['residential'].address_data_to_save
            )
            admission.submitted_profile['coordinates'] = {
                'country': address.get('country').iso_code,
                'postal_code': address.get('postal_code'),
                'city': address.get('city'),
                'street': address.get('street'),
                'street_number': address.get('street_number'),
                'postal_box': address.get('postal_box'),
            }

    def get_success_url(self):
        return self.next_url or reverse(
            f'admission:{self.current_context}:coordonnees',
            kwargs=self.kwargs,
        )
