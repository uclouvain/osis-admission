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
import datetime
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.models import ContinuingEducationAdmission, GeneralEducationAdmission, DoctorateAdmission
from admission.ddd import BE_ISO_CODE, FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE, ENTITY_CDSS
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixSexe, ChoixGenre
from admission.forms.admission.coordonnees import AdmissionCoordonneesForm, AdmissionAddressForm
from admission.forms.admission.person import AdmissionPersonForm, IdentificationType
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, SicManagerRoleFactory, CddManagerFactory
from base.models.enums.civil_state import CivilState
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_address import PersonAddress
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_address import PersonAddressFactory
from reference.models.country import Country
from reference.tests.factories.country import CountryFactory


class BaseCoordonneesFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.belgium_country = CountryFactory(iso_code=BE_ISO_CODE)
        cls.france_country = CountryFactory(iso_code=FR_ISO_CODE)
        cls.academic_year = AcademicYearFactory(year=2021)
        cls.form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'birth_date': datetime.date(1990, 1, 1),
            'birth_country': cls.belgium_country.pk,
            'birth_place': 'Louvain-La-Neuve',
            'sex': ChoixSexe.M.name,
            'gender': ChoixGenre.H.name,
            'civil_state': CivilState.MARRIED.name,
            'has_national_number': True,
            'national_number': '01234567899',
        }


class AdmissionCoordonneesFormTestCase(TestCase):
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
        self.assertTrue(form.is_valid())


class AdmissionAddressFormTestCase(BaseCoordonneesFormTestCase):
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
                city='Louvain-La-Neuve',
            ),
        )
        self.assertEqual(form.initial.get('be_postal_code'), None)
        self.assertEqual(form.initial.get('be_city'), None)

        # With foreign country
        form = AdmissionAddressForm(
            instance=PersonAddressFactory(
                country=self.france_country,
                postal_code='1348',
                city='Louvain-La-Neuve',
            ),
        )
        self.assertEqual(form.initial.get('be_postal_code'), None)
        self.assertEqual(form.initial.get('be_city'), None)

        # With Belgium
        form = AdmissionAddressForm(
            instance=PersonAddressFactory(
                country=self.belgium_country,
                postal_code='1348',
                city='Louvain-La-Neuve',
            ),
        )
        self.assertEqual(form.initial.get('be_postal_code'), '1348')
        self.assertEqual(form.initial.get('be_city'), 'Louvain-La-Neuve')
        self.assertEqual(form.fields['be_city'].widget.choices, [('Louvain-La-Neuve', 'Louvain-La-Neuve')])

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
                'place': '',
                'postal_box': '',
                'postal_code': '',
                'street': '',
                'street_number': '',
            },
        )
        self.assertEqual(
            form.get_prepare_data(),
            {
                'city': '',
                'country': None,
                'place': '',
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
        self.assertEqual(form.get_prepare_data(), None)

        # All required fields are filled
        form = AdmissionAddressForm(
            data={
                'country': self.france_country.pk,
                'street': 'ART STREET',
                'street_number': '123',
                'city': 'PARIS',
                'postal_code': '92000',
                'place': 'MUSIC PLACE',
                'be_city': 'Louvain-La-Neuve',
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
                'place': 'Music Place',
                'street': 'Art Street',
                'postal_box': '',
                'be_city': 'Louvain-La-Neuve',
                'be_postal_code': '1348',
                'street_number': '123',
            },
        )
        self.assertEqual(
            form.get_prepare_data(),
            {
                'country': self.france_country,
                'city': 'Paris',
                'postal_code': '92000',
                'place': 'Music Place',
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
        self.assertEqual(form.get_prepare_data(), None)

        # All required fields are filled
        form = AdmissionAddressForm(
            data={
                'country': self.belgium_country.pk,
                'street': 'ART STREET',
                'street_number': '123',
                'city': 'PARIS',
                'postal_code': '92000',
                'place': 'MUSIC PLACE',
                'be_city': 'Louvain-La-Neuve',
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
                'place': 'Music Place',
                'street': 'Art Street',
                'postal_box': '',
                'be_city': 'Louvain-La-Neuve',
                'be_postal_code': '1348',
                'street_number': '123',
            },
        )
        self.assertEqual(
            form.get_prepare_data(),
            {
                'country': self.belgium_country,
                'city': 'Louvain-La-Neuve',
                'postal_code': '1348',
                'place': 'Music Place',
                'street': 'Art Street',
                'postal_box': '',
                'street_number': '123',
            },
        )


class GeneralAdmissionPersonFormViewTestCase(BaseCoordonneesFormTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        cls.sic_manager_user = SicManagerRoleFactory().person.user

        cls.admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__phone_mobile='987654321',
            candidate__private_email='joe.foe@example.com',
        )

        cls.url = reverse('admission:general-education:update:coordonnees', args=[cls.admission.uuid])
        cls.redirect_url = reverse('admission:general-education:coordonnees', args=[cls.admission.uuid])

    def test_person_form_on_get_candidate_user(self):
        self.client.force_login(user=self.admission.candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_person_form_on_get_other_candidate_user(self):
        self.client.force_login(user=CandidateFactory().person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_person_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_person_form_on_get(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['BE_ISO_CODE'], self.belgium_country.pk)
        self.assertIsInstance(response.context['main_form'], AdmissionCoordonneesForm)
        self.assertIsInstance(response.context['residential'], AdmissionAddressForm)
        self.assertIsInstance(response.context['contact'], AdmissionAddressForm)
        self.assertTrue(response.context['force_form'])

    def test_person_form_post_main_form(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            {
                'phone_mobile': '0123456789',
                'private_email': 'john.doe@example.com',
            },
        )

        self.assertRedirects(response, self.redirect_url)

        candidate = Person.objects.get(pk=self.admission.candidate.pk)
        self.assertEqual(candidate.phone_mobile, '0123456789')
        self.assertEqual(candidate.private_email, 'joe.foe@example.com')  # Not updated (disabled field)

    def test_person_form_post_residential_address(self):
        self.client.force_login(user=self.sic_manager_user)

        PersonAddress.objects.filter(person=self.admission.candidate).delete()

        # The candidate has no address and specifies a new one
        response = self.client.post(
            self.url,
            {
                'residential-country': self.belgium_country.pk,
                'residential-be_postal_code': '1348',
                'residential-be_city': 'Louvain-La-Neuve',
                'residential-street': 'Art street',
                'residential-street_number': '1',
            },
        )

        self.assertRedirects(response, self.redirect_url)

        residential_addresses = PersonAddress.objects.filter(
            person=self.admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
        )

        self.assertEqual(len(residential_addresses), 1)
        self.assertEqual(residential_addresses[0].country, self.belgium_country)
        self.assertEqual(residential_addresses[0].postal_code, '1348')
        self.assertEqual(residential_addresses[0].city, 'Louvain-La-Neuve')
        self.assertEqual(residential_addresses[0].street, 'Art street')
        self.assertEqual(residential_addresses[0].street_number, '1')

        # The candidate has an existing address and specifies a new one
        response = self.client.post(
            self.url,
            {
                'residential-country': self.france_country.pk,
                'residential-postal_code': '92000',
                'residential-city': 'Paris',
                'residential-street': 'Peace street',
                'residential-street_number': '10',
            },
        )

        self.assertRedirects(response, self.redirect_url)

        residential_addresses = PersonAddress.objects.filter(
            person=self.admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
        )

        self.assertEqual(len(residential_addresses), 1)
        self.assertEqual(residential_addresses[0].country, self.france_country)
        self.assertEqual(residential_addresses[0].postal_code, '92000')
        self.assertEqual(residential_addresses[0].city, 'Paris')
        self.assertEqual(residential_addresses[0].street, 'Peace street')
        self.assertEqual(residential_addresses[0].street_number, '10')

        # The candidate has an existing address and no specifies a new one -> reset address
        response = self.client.post(
            self.url,
            {},
        )

        self.assertRedirects(response, self.redirect_url)

        residential_addresses = PersonAddress.objects.filter(
            person=self.admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
        )

        self.assertEqual(len(residential_addresses), 1)
        self.assertEqual(residential_addresses[0].country, None)
        self.assertEqual(residential_addresses[0].postal_code, '')
        self.assertEqual(residential_addresses[0].city, '')
        self.assertEqual(residential_addresses[0].street, '')
        self.assertEqual(residential_addresses[0].street_number, '')

    def test_person_form_post_contact_address(self):
        self.client.force_login(user=self.sic_manager_user)

        PersonAddress.objects.filter(person=self.admission.candidate).delete()

        # The candidate has no address and specifies a new one
        response = self.client.post(
            self.url,
            {
                'show_contact': True,
                'contact-country': self.belgium_country.pk,
                'contact-be_postal_code': '1348',
                'contact-be_city': 'Louvain-La-Neuve',
                'contact-street': 'Art street',
                'contact-street_number': '1',
            },
        )

        self.assertRedirects(response, self.redirect_url)

        contact_addresses = PersonAddress.objects.filter(
            person=self.admission.candidate,
            label=PersonAddressType.CONTACT.name,
        )

        self.assertEqual(len(contact_addresses), 1)
        self.assertEqual(contact_addresses[0].country, self.belgium_country)
        self.assertEqual(contact_addresses[0].postal_code, '1348')
        self.assertEqual(contact_addresses[0].city, 'Louvain-La-Neuve')
        self.assertEqual(contact_addresses[0].street, 'Art street')

        # The candidate has an existing address and specifies a new one
        response = self.client.post(
            self.url,
            {
                'show_contact': True,
                'contact-country': self.france_country.pk,
                'contact-postal_code': '92000',
                'contact-city': 'Paris',
                'contact-street': 'Peace street',
                'contact-street_number': '10',
            },
        )

        self.assertRedirects(response, self.redirect_url)

        contact_addresses = PersonAddress.objects.filter(
            person=self.admission.candidate,
            label=PersonAddressType.CONTACT.name,
        )

        self.assertEqual(len(contact_addresses), 1)
        self.assertEqual(contact_addresses[0].country, self.france_country)
        self.assertEqual(contact_addresses[0].postal_code, '92000')
        self.assertEqual(contact_addresses[0].city, 'Paris')
        self.assertEqual(contact_addresses[0].street, 'Peace street')
        self.assertEqual(contact_addresses[0].street_number, '10')

        # The candidate has an existing address and no specifies a new one -> delete the existing one
        response = self.client.post(
            self.url,
            data={
                'show_contact': False,
            },
        )

        self.assertRedirects(response, self.redirect_url)
        self.assertFalse(
            PersonAddress.objects.filter(
                person=self.admission.candidate,
                label=PersonAddressType.CONTACT.name,
            ).exists()
        )

    def test_person_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        max_pk = Country.objects.latest('pk').pk
        response = self.client.post(
            self.url,
            {
                "residential-country": max_pk + 1,  # Invalid country
            },
        )
        self.assertEqual(response.status_code, 200)


class ContinuingAdmissionPersonFormViewTestCase(BaseCoordonneesFormTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        cls.sic_manager_user = SicManagerRoleFactory().person.user

        cls.admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__phone_mobile='987654321',
            candidate__private_email='joe.foe@example.com',
        )

        cls.url = reverse('admission:continuing-education:update:coordonnees', args=[cls.admission.uuid])
        cls.redirect_url = reverse('admission:continuing-education:coordonnees', args=[cls.admission.uuid])

    def test_person_form_on_get_candidate_user(self):
        self.client.force_login(user=self.admission.candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_person_form_on_get_other_candidate_user(self):
        self.client.force_login(user=CandidateFactory().person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_person_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_person_form_on_get(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['BE_ISO_CODE'], self.belgium_country.pk)
        self.assertIsInstance(response.context['main_form'], AdmissionCoordonneesForm)
        self.assertIsInstance(response.context['residential'], AdmissionAddressForm)
        self.assertIsInstance(response.context['contact'], AdmissionAddressForm)
        self.assertTrue(response.context['force_form'])

    def test_person_form_post_main_form(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            {
                'phone_mobile': '0123456789',
                'private_email': 'john.doe@example.com',
            },
        )

        self.assertRedirects(response, self.redirect_url)

        candidate = Person.objects.get(pk=self.admission.candidate.pk)
        self.assertEqual(candidate.phone_mobile, '0123456789')

    def test_person_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        max_pk = Country.objects.latest('pk').pk
        response = self.client.post(
            self.url,
            {
                "residential-country": max_pk + 1,  # Invalid country
            },
        )
        self.assertEqual(response.status_code, 200)


class DoctorateAdmissionPersonFormViewTestCase(BaseCoordonneesFormTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        cls.sic_manager_user = SicManagerRoleFactory().person.user

        cls.cdd_manager = CddManagerFactory(
            entity=first_doctoral_commission,
        )

        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__phone_mobile='987654321',
            candidate__private_email='joe.foe@example.com',
        )

        cls.url = reverse('admission:doctorate:update:coordonnees', args=[cls.admission.uuid])
        cls.redirect_url = reverse('admission:doctorate:coordonnees', args=[cls.admission.uuid])

    def test_person_form_on_get_candidate_user(self):
        self.client.force_login(user=self.admission.candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_person_form_on_get_other_candidate_user(self):
        self.client.force_login(user=CandidateFactory().person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_person_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_person_form_on_get_cdd_manager(self):
        self.client.force_login(user=self.cdd_manager.person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_person_form_on_get(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['BE_ISO_CODE'], self.belgium_country.pk)
        self.assertIsInstance(response.context['main_form'], AdmissionCoordonneesForm)
        self.assertIsInstance(response.context['residential'], AdmissionAddressForm)
        self.assertIsInstance(response.context['contact'], AdmissionAddressForm)
        self.assertTrue(response.context['force_form'])

    def test_person_form_post_main_form(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            {
                'phone_mobile': '0123456789',
                'private_email': 'john.doe@example.com',
            },
        )

        self.assertRedirects(response, self.redirect_url)

        candidate = Person.objects.get(pk=self.admission.candidate.pk)
        self.assertEqual(candidate.phone_mobile, '0123456789')

    def test_person_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        max_pk = Country.objects.latest('pk').pk
        response = self.client.post(
            self.url,
            {
                "residential-country": max_pk + 1,  # Invalid country
            },
        )
        self.assertEqual(response.status_code, 200)
