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

from django.shortcuts import resolve_url
from django.test import TestCase

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.models import ContinuingEducationAdmission, DoctorateAdmission, GeneralEducationAdmission
from admission.ddd import BE_ISO_CODE, FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.forms.admission.coordonnees import AdmissionAddressForm, AdmissionCoordonneesForm
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CentralManagerRoleFactory, SicManagementRoleFactory
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_address import PersonAddress
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.person_address import PersonAddressFactory
from reference.models.country import Country
from reference.tests.factories.country import CountryFactory


class CoordonneesFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.belgium_country = CountryFactory(iso_code=BE_ISO_CODE)
        cls.france_country = CountryFactory(iso_code=FR_ISO_CODE)
        cls.academic_year = AcademicYearFactory(year=2021)

        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)

        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.cdd_manager = CentralManagerRoleFactory(entity=first_doctoral_commission).person.user

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__phone_mobile='987654321',
            candidate__private_email='joe.foe@example.com',
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        cls.general_url = resolve_url('admission:general-education:update:coordonnees', uuid=cls.general_admission.uuid)
        cls.general_redirect_url = resolve_url(
            'admission:general-education:coordonnees',
            uuid=cls.general_admission.uuid,
        )

        cls.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__phone_mobile='987654321',
            candidate__private_email='joe.foe@example.com',
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )

        cls.continuing_url = resolve_url(
            'admission:continuing-education:update:coordonnees',
            uuid=cls.continuing_admission.uuid,
        )

        cls.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__phone_mobile='987654321',
            candidate__private_email='joe.foe@example.com',
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        cls.doctorate_url = resolve_url('admission:doctorate:update:coordonnees', uuid=cls.doctorate_admission.uuid)

    def test_form_initialization(self):
        form = AdmissionCoordonneesForm(
            show_contact=True,
        )
        self.assertTrue(form.fields['show_contact'].initial)

        form = AdmissionCoordonneesForm(
            show_contact=False,
        )
        self.assertFalse(form.fields['show_contact'].initial)

    def test_form_submission_without_any_data(self):
        form = AdmissionCoordonneesForm(
            show_contact=True,
            data={},
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('phone_mobile', []))

    def test_country_field_initialization(self):
        # Without country
        form = AdmissionAddressForm(
            instance=PersonAddressFactory(
                country=None,
            ),
        )
        self.assertEqual(len(form.fields['country'].queryset), 0)

        # With country
        form = AdmissionAddressForm(
            instance=PersonAddressFactory(
                country=self.belgium_country,
            ),
        )
        self.assertIn(self.belgium_country, form.fields['country'].queryset)

    def test_be_city_fields_initialization(self):
        # Without country
        form = AdmissionAddressForm(
            instance=PersonAddressFactory(
                country=None,
                postal_code='1348',
                city='Louvain-la-Neuve',
            ),
        )
        self.assertEqual(form.initial.get('be_postal_code'), None)
        self.assertEqual(form.initial.get('be_city'), None)

        # With foreign country
        form = AdmissionAddressForm(
            instance=PersonAddressFactory(
                country=self.france_country,
                postal_code='1348',
                city='Louvain-la-Neuve',
            ),
        )
        self.assertEqual(form.initial.get('be_postal_code'), None)
        self.assertEqual(form.initial.get('be_city'), None)

        # With Belgium
        form = AdmissionAddressForm(
            instance=PersonAddressFactory(
                country=self.belgium_country,
                postal_code='1348',
                city='Louvain-la-Neuve',
            ),
        )
        self.assertEqual(form.initial.get('be_postal_code'), '1348')
        self.assertEqual(form.initial.get('be_city'), 'Louvain-la-Neuve')
        self.assertEqual(form.fields['be_city'].widget.choices, [('Louvain-la-Neuve', 'Louvain-la-Neuve')])

    def form_submission_without_any_data(self):
        # By default, the form can be empty
        form = AdmissionAddressForm(
            data={},
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data,
            {
                'be_city': '',
                'be_postal_code': '',
                'city': '',
                'country': None,
                'postal_box': '',
                'postal_code': '',
                'street': '',
                'street_number': '',
            },
        )
        self.assertEqual(
            form.get_prepare_data,
            {
                'city': '',
                'country': None,
                'postal_box': '',
                'postal_code': '',
                'street': '',
                'street_number': '',
            },
        )

        # Otherwise, some fields are required if the address cannot be empty
        form = AdmissionAddressForm(
            data={},
        )
        form.address_can_be_empty = False
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('street', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('street_number', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('postal_code', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('city', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('country', []))

    def test_form_submission_with_foreign_country(self):
        # Some fields are missing
        form = AdmissionAddressForm(
            data={
                'country': self.france_country.pk,
                'street': 'Art street',
                'street_number': '123',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('city', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('postal_code', []))
        self.assertEqual(form.get_prepare_data, None)

        # All required fields are filled
        form = AdmissionAddressForm(
            data={
                'country': self.france_country.pk,
                'street': 'ART STREET',
                'street_number': '123',
                'city': 'PARIS',
                'postal_code': '92000',
                'be_city': 'Louvain-la-Neuve',
                'be_postal_code': '1348',
            },
        )
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data
        self.assertEqual(
            cleaned_data,
            {
                'country': self.france_country,
                'city': 'Paris',
                'postal_code': '92000',
                'street': 'Art Street',
                'postal_box': '',
                'be_city': 'Louvain-la-Neuve',
                'be_postal_code': '1348',
                'street_number': '123',
            },
        )
        self.assertEqual(
            form.get_prepare_data,
            {
                'country': self.france_country,
                'city': 'Paris',
                'postal_code': '92000',
                'street': 'Art Street',
                'postal_box': '',
                'street_number': '123',
            },
        )

    def test_form_submission_with_belgium_country(self):
        # Some fields are missing
        form = AdmissionAddressForm(
            data={
                'country': self.belgium_country.pk,
                'street': 'Art street',
                'street_number': '123',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('be_city', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('be_postal_code', []))
        self.assertEqual(form.get_prepare_data, None)

        # All required fields are filled
        form = AdmissionAddressForm(
            data={
                'country': self.belgium_country.pk,
                'street': 'ART STREET',
                'street_number': '123',
                'city': 'PARIS',
                'postal_code': '92000',
                'be_city': 'Louvain-la-Neuve',
                'be_postal_code': '1348',
            },
        )
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data
        self.assertEqual(
            cleaned_data,
            {
                'country': self.belgium_country,
                'city': 'Paris',
                'postal_code': '92000',
                'street': 'Art Street',
                'postal_box': '',
                'be_city': 'Louvain-la-Neuve',
                'be_postal_code': '1348',
                'street_number': '123',
            },
        )
        self.assertEqual(
            form.get_prepare_data,
            {
                'country': self.belgium_country,
                'city': 'Louvain-la-Neuve',
                'postal_code': '1348',
                'street': 'Art Street',
                'postal_box': '',
                'street_number': '123',
            },
        )

    def test_general_coordinates_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)

    def test_general_coordinates_form_on_get(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['BE_ISO_CODE'], self.belgium_country.pk)
        self.assertIsInstance(response.context['main_form'], AdmissionCoordonneesForm)
        self.assertIsInstance(response.context['residential'], AdmissionAddressForm)
        self.assertIsInstance(response.context['contact'], AdmissionAddressForm)
        self.assertTrue(response.context['force_form'])

    def test_general_coordinates_form_post_main_form(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.general_url,
            {
                'phone_mobile': '+3223742211',
                'private_email': 'john.doe@example.com',
                'residential-country': self.france_country.pk,
                'residential-postal_code': '92000',
                'residential-city': 'Paris',
                'residential-street': 'Peace street',
                'residential-street_number': '10',
            },
        )

        self.assertRedirects(response, self.general_redirect_url)

        candidate = Person.objects.get(pk=self.general_admission.candidate.pk)
        self.assertEqual(candidate.phone_mobile, '+3223742211')
        self.assertEqual(candidate.private_email, 'joe.foe@example.com')  # Not updated (disabled field)

    def test_general_coordinates_form_post_residential_address(self):
        self.client.force_login(user=self.sic_manager_user)

        PersonAddress.objects.filter(person=self.general_admission.candidate).delete()

        # The candidate has no address and specifies a new one
        response = self.client.post(
            self.general_url,
            {
                'phone_mobile': '+3223742211',
                'residential-country': self.belgium_country.pk,
                'residential-be_postal_code': '1348',
                'residential-be_city': 'Louvain-la-Neuve',
                'residential-street': 'Art street',
                'residential-street_number': '1',
            },
        )

        self.assertRedirects(response, self.general_redirect_url)

        residential_addresses = PersonAddress.objects.filter(
            person=self.general_admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
        )

        self.assertEqual(len(residential_addresses), 1)
        self.assertEqual(residential_addresses[0].country, self.belgium_country)
        self.assertEqual(residential_addresses[0].postal_code, '1348')
        self.assertEqual(residential_addresses[0].city, 'Louvain-la-Neuve')
        self.assertEqual(residential_addresses[0].street, 'Art street')
        self.assertEqual(residential_addresses[0].street_number, '1')

        # The candidate has an existing address and specifies a new one
        response = self.client.post(
            self.general_url,
            {
                'phone_mobile': '+3223742211',
                'residential-country': self.france_country.pk,
                'residential-postal_code': '92000',
                'residential-city': 'Paris',
                'residential-street': 'Peace street',
                'residential-street_number': '10',
            },
        )

        self.assertRedirects(response, self.general_redirect_url)

        residential_addresses = PersonAddress.objects.filter(
            person=self.general_admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
        )

        self.assertEqual(len(residential_addresses), 1)
        self.assertEqual(residential_addresses[0].country, self.france_country)
        self.assertEqual(residential_addresses[0].postal_code, '92000')
        self.assertEqual(residential_addresses[0].city, 'Paris')
        self.assertEqual(residential_addresses[0].street, 'Peace street')
        self.assertEqual(residential_addresses[0].street_number, '10')

    def test_general_coordinates_form_post_contact_address(self):
        self.client.force_login(user=self.sic_manager_user)

        PersonAddress.objects.filter(person=self.general_admission.candidate).delete()

        # The candidate has no address and specifies a new one
        response = self.client.post(
            self.general_url,
            {
                'show_contact': True,
                'phone_mobile': '+3223742211',
                'contact-country': self.belgium_country.pk,
                'contact-be_postal_code': '1348',
                'contact-be_city': 'Louvain-la-Neuve',
                'contact-street': 'Art street',
                'contact-street_number': '1',
                'residential-country': self.france_country.pk,
                'residential-postal_code': '92000',
                'residential-city': 'Paris',
                'residential-street': 'Peace street',
                'residential-street_number': '10',
            },
        )

        self.assertRedirects(response, self.general_redirect_url)

        contact_addresses = PersonAddress.objects.filter(
            person=self.general_admission.candidate,
            label=PersonAddressType.CONTACT.name,
        )

        self.assertEqual(len(contact_addresses), 1)
        self.assertEqual(contact_addresses[0].country, self.belgium_country)
        self.assertEqual(contact_addresses[0].postal_code, '1348')
        self.assertEqual(contact_addresses[0].city, 'Louvain-la-Neuve')
        self.assertEqual(contact_addresses[0].street, 'Art street')

        # The candidate has an existing address and specifies a new one
        response = self.client.post(
            self.general_url,
            {
                'show_contact': True,
                'phone_mobile': '+3223742211',
                'contact-country': self.france_country.pk,
                'contact-postal_code': '92000',
                'contact-city': 'Paris',
                'contact-street': 'Peace street',
                'contact-street_number': '10',
                'residential-country': self.france_country.pk,
                'residential-postal_code': '92000',
                'residential-city': 'Paris',
                'residential-street': 'Peace street',
                'residential-street_number': '10',
            },
        )

        self.assertRedirects(response, self.general_redirect_url)

        contact_addresses = PersonAddress.objects.filter(
            person=self.general_admission.candidate,
            label=PersonAddressType.CONTACT.name,
        )

        self.assertEqual(len(contact_addresses), 1)
        self.assertEqual(contact_addresses[0].country, self.france_country)
        self.assertEqual(contact_addresses[0].postal_code, '92000')
        self.assertEqual(contact_addresses[0].city, 'Paris')
        self.assertEqual(contact_addresses[0].street, 'Peace street')
        self.assertEqual(contact_addresses[0].street_number, '10')

        # The candidate has an existing contact address and no specifies a new one -> delete the existing one
        response = self.client.post(
            self.general_url,
            data={
                'phone_mobile': '+3223742211',
                'residential-country': self.france_country.pk,
                'residential-postal_code': '92000',
                'residential-city': 'Paris',
                'residential-street': 'Peace street',
                'residential-street_number': '10',
            },
        )

        self.assertRedirects(response, self.general_redirect_url)
        self.assertFalse(
            PersonAddress.objects.filter(
                person=self.general_admission.candidate,
                label=PersonAddressType.CONTACT.name,
            ).exists()
        )

    def test_general_coordinates_form_post_updates_submitted_profile_if_necessary(self):
        self.client.force_login(user=self.sic_manager_user)

        general_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.general_admission.training.management_entity,
            training__academic_year=self.general_admission.training.academic_year,
            candidate__phone_mobile='987654321',
            candidate__private_email='joe.foe@example.com',
            submitted_profile={},
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        url = resolve_url('admission:general-education:update:coordonnees', uuid=general_admission.uuid)

        default_submitted_profile = {
            'identification': {
                'first_name': general_admission.candidate.first_name,
                'last_name': general_admission.candidate.last_name,
                'gender': general_admission.candidate.gender,
                'country_of_citizenship': 'BE',
            },
            'coordinates': {
                'country': 'BE',
                'postal_code': '1348',
                'city': 'Louvain-la-Neuve',
                'street': 'University street',
                'street_number': '1',
                'postal_box': 'PB1',
            },
        }

        # No submitted profile so it should not be updated
        response = self.client.post(
            url,
            data={
                'phone_mobile': '+3223742211',
                'residential-country': self.france_country.pk,
                'residential-postal_code': '92000',
                'residential-city': 'Paris',
                'residential-street': 'Peace street',
                'residential-street_number': '10',
                'residential-postal_box': 'PB2',
            },
        )

        self.assertEqual(response.status_code, 302)

        general_admission.refresh_from_db()
        self.assertEqual(general_admission.submitted_profile, {})

        # The submitted profile exists so it should be updated with the residential address
        general_admission.submitted_profile = default_submitted_profile
        general_admission.save()

        response = self.client.post(
            url,
            data={
                'phone_mobile': '+3223742211',
                'residential-country': self.france_country.pk,
                'residential-postal_code': '92000',
                'residential-city': 'Paris',
                'residential-street': 'Peace street',
                'residential-street_number': '10',
                'residential-postal_box': 'PB2',
            },
        )

        self.assertEqual(response.status_code, 302)

        general_admission.refresh_from_db()
        self.assertEqual(
            general_admission.submitted_profile,
            {
                'identification': default_submitted_profile.get('identification'),
                'coordinates': {
                    'country': 'FR',
                    'postal_code': '92000',
                    'city': 'Paris',
                    'street': 'Peace street',
                    'street_number': '10',
                    'postal_box': 'PB2',
                },
            },
        )

        # The submitted profile exists so it should be updated with the contact address
        general_admission.submitted_profile = default_submitted_profile
        general_admission.save()

        response = self.client.post(
            url,
            {
                'phone_mobile': '+3223742211',
                'show_contact': True,
                'residential-country': self.france_country.pk,
                'residential-postal_code': '92000',
                'residential-city': 'Paris',
                'residential-street': 'Peace street',
                'residential-street_number': '10',
                'residential-postal_box': 'PB2',
                'contact-country': self.belgium_country.pk,
                'contact-be_postal_code': '1000',
                'contact-be_city': 'Bruxelles',
                'contact-street': 'Main street',
                'contact-street_number': '15',
                'contact-postal_box': 'PB3',
            },
        )

        self.assertEqual(response.status_code, 302)

        general_admission.refresh_from_db()
        self.assertEqual(
            general_admission.submitted_profile,
            {
                'identification': default_submitted_profile.get('identification'),
                'coordinates': {
                    'country': 'BE',
                    'postal_code': '1000',
                    'city': 'Bruxelles',
                    'street': 'Main street',
                    'street_number': '15',
                    'postal_box': 'PB3',
                },
            },
        )

    def test_general_coordinates_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        max_pk = Country.objects.latest('pk').pk
        response = self.client.post(
            self.general_url,
            {
                "residential-country": max_pk + 1,  # Invalid country
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_continuing_coordinates_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, 200)

    def test_continuing_coordinates_form_on_get(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['BE_ISO_CODE'], self.belgium_country.pk)
        self.assertIsInstance(response.context['main_form'], AdmissionCoordonneesForm)
        self.assertIsInstance(response.context['residential'], AdmissionAddressForm)
        self.assertIsInstance(response.context['contact'], AdmissionAddressForm)
        self.assertTrue(response.context['force_form'])

    def test_continuing_coordinates_form_post_main_form(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.continuing_url,
            {
                'phone_mobile': '+3223742211',
                'private_email': 'john.doe@example.com',
                'residential-country': self.france_country.pk,
                'residential-postal_code': '92000',
                'residential-city': 'Paris',
                'residential-street': 'Peace street',
                'residential-street_number': '10',
            },
        )
        redirect_url = resolve_url('admission:continuing-education:coordonnees', uuid=self.continuing_admission.uuid)
        self.assertRedirects(response, redirect_url)

        candidate = Person.objects.get(pk=self.continuing_admission.candidate.pk)
        self.assertEqual(candidate.phone_mobile, '+3223742211')

    def test_continuing_coordinates_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        max_pk = Country.objects.latest('pk').pk
        response = self.client.post(
            self.continuing_url,
            {
                "residential-country": max_pk + 1,  # Invalid country
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_doctoral_coordinates_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, 200)

    def test_doctoral_coordinates_form_on_get_cdd_manager(self):
        self.client.force_login(user=self.cdd_manager.person.user)

        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, 200)

    def test_doctoral_coordinates_form_on_get(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['BE_ISO_CODE'], self.belgium_country.pk)
        self.assertIsInstance(response.context['main_form'], AdmissionCoordonneesForm)
        self.assertIsInstance(response.context['residential'], AdmissionAddressForm)
        self.assertIsInstance(response.context['contact'], AdmissionAddressForm)
        self.assertTrue(response.context['force_form'])

    def test_doctoral_coordinates_form_post_main_form(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.doctorate_url,
            {
                'phone_mobile': '+3223742211',
                'private_email': 'john.doe@example.com',
                'residential-country': self.france_country.pk,
                'residential-postal_code': '92000',
                'residential-city': 'Paris',
                'residential-street': 'Peace street',
                'residential-street_number': '10',
            },
        )

        redirect_url = resolve_url('admission:doctorate:coordonnees', uuid=self.doctorate_admission.uuid)
        self.assertRedirects(response, redirect_url)

        candidate = Person.objects.get(pk=self.doctorate_admission.candidate.pk)
        self.assertEqual(candidate.phone_mobile, '+3223742211')

    def test_doctoral_coordinates_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        max_pk = Country.objects.latest('pk').pk
        response = self.client.post(
            self.doctorate_url,
            {
                "residential-country": max_pk + 1,  # Invalid country
            },
        )
        self.assertEqual(response.status_code, 200)
