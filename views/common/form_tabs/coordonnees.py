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
from django.views.generic import FormView

from admission.forms.admission.coordonnees import AdmissionAddressForm, AdmissionCoordonneesForm
from admission.views.common.mixins import AdmissionFormMixin, LoadDossierViewMixin
from base.models.enums.person_address_type import PersonAddressType
from base.models.person_address import PersonAddress
from osis_profile import BE_ISO_CODE
from reference.models.country import Country

__all__ = ['AdmissionCoordonneesFormView']


class AdmissionCoordonneesFormView(AdmissionFormMixin, LoadDossierViewMixin, FormView):
    template_name = 'admission/forms/coordonnees.html'
    permission_required = 'admission.change_admission_coordinates'
    update_requested_documents = True
    update_admission_author = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.forms = None

    def get_context_data(self, **kwargs):
        kwargs['force_form'] = True
        kwargs['form'] = True
        context_data = super().get_context_data(**kwargs)
        context_data.update(self.get_forms())
        context_data['BE_ISO_CODE'] = Country.objects.get(iso_code=BE_ISO_CODE).pk
        return context_data

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        if all(form.is_valid() for form in forms.values()):
            return self.form_valid(forms)
        return self.form_invalid(forms)

    def form_valid(self, forms):
        # Update person
        self.forms['main_form'].save()
        # Update person addresses
        PersonAddress.objects.update_or_create(
            person=self.admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
            defaults=forms['residential'].get_prepare_data,
        )
        if forms['main_form'].cleaned_data['show_contact']:
            PersonAddress.objects.update_or_create(
                person=self.admission.candidate,
                label=PersonAddressType.CONTACT.name,
                defaults=forms['contact'].get_prepare_data,
            )
        else:
            PersonAddress.objects.filter(
                person=self.admission.candidate,
                label=PersonAddressType.CONTACT.name,
            ).delete()

        return super().form_valid(forms)

    def update_current_admission_on_form_valid(self, form, admission):
        # Update submitted profile with newer data
        if admission.submitted_profile:
            address = (
                form['contact'].get_prepare_data
                if form['main_form'].cleaned_data['show_contact']
                else form['residential'].get_prepare_data
            )
            admission.submitted_profile['coordinates'] = {
                'country': address.get('country').iso_code,
                'postal_code': address.get('postal_code'),
                'city': address.get('city'),
                'street': address.get('street'),
                'street_number': address.get('street_number'),
                'postal_box': address.get('postal_box'),
            }

    def get_initial(self):
        addresses = PersonAddress.objects.filter(
            person=self.admission.candidate,
            label__in=[PersonAddressType.CONTACT.name, PersonAddressType.RESIDENTIAL.name],
        )
        return {
            'contact': next(
                (address for address in addresses if address.label == PersonAddressType.CONTACT.name),
                None,
            ),
            'residential': next(
                (address for address in addresses if address.label == PersonAddressType.RESIDENTIAL.name),
                None,
            ),
            'main_form': self.admission.candidate,
        }

    def get_forms(self):
        if not self.forms:
            kwargs = self.get_form_kwargs()
            kwargs.pop('prefix')
            initial = kwargs.pop('initial')
            self.forms = {
                'main_form': AdmissionCoordonneesForm(
                    show_contact=bool(initial.get('contact')),
                    prefix='',
                    instance=initial['main_form'],
                    **kwargs,
                ),
                'contact': AdmissionAddressForm(
                    check_coordinates_fields=bool(kwargs.get('data') and kwargs['data'].get('show_contact')),
                    prefix='contact',
                    instance=initial['contact'],
                    **kwargs,
                ),
                'residential': AdmissionAddressForm(
                    prefix='residential',
                    instance=initial['residential'],
                    **kwargs,
                ),
            }
        return self.forms

    def get_success_url(self):
        return self.next_url or reverse(
            f'admission:{self.current_context}:coordonnees',
            kwargs=self.kwargs,
        )
