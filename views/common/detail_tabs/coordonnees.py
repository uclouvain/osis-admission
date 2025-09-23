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
from functools import cached_property

from admission.views.common.mixins import LoadDossierViewMixin
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_address import PersonAddress
from osis_profile.views.coordonnees import CoordonneesDetailView

__all__ = ['AdmissionCoordonneesDetailView']



class AdmissionCoordonneesDetailView(LoadDossierViewMixin, CoordonneesDetailView):
    permission_required = 'admission.view_admission_coordinates'
    template_name = 'admission/details/coordonnees_backoffice.html'

    @cached_property
    def person(self) -> Person:
        return self.admission.candidate

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.proposition_fusion:
            known_person = Person.objects.get(global_id=self.proposition_fusion.matricule)
            addresses = {
                address.label: address
                for address in PersonAddress.objects.filter(
                    person=known_person,
                    label__in=[PersonAddressType.CONTACT.name, PersonAddressType.RESIDENTIAL.name],
                ).select_related('country')
            }
            context['coordonnees_fusion'] = {
                'contact': addresses.get(PersonAddressType.CONTACT.name),
                'residential': addresses.get(PersonAddressType.RESIDENTIAL.name),
                'private_email': known_person.private_email,
                'phone_mobile': known_person.phone_mobile,
                'emergency_contact_phone': known_person.emergency_contact_phone,
            }

        context['profil_candidat'] = context['admission'].profil_soumis_candidat

        return context
