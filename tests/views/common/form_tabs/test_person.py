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
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.models import ContinuingEducationAdmission, DoctorateAdmission, GeneralEducationAdmission
from admission.ddd import BE_ISO_CODE, FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre, ChoixSexe
from admission.forms.admission.person import AdmissionPersonForm, IdentificationType
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory
from base.models.enums.civil_state import CivilState
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_address import PersonAddressFactory
from reference.tests.factories.country import CountryFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class PersonFormTestCase(TestCase):
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
            'country_of_citizenship': cls.belgium_country.pk,
            'birth_place': 'Louvain-La-Neuve',
            'sex': ChoixSexe.M.name,
            'gender': ChoixGenre.H.name,
            'civil_state': CivilState.MARRIED.name,
            'has_national_number': True,
            'national_number': '01234567899',
        }

        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)

        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
        )
        cls.general_url = resolve_url('admission:general-education:update:person', uuid=cls.general_admission.uuid)

        cls.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate=cls.general_admission.candidate,
        )

        cls.continuing_url = resolve_url(
            'admission:continuing-education:update:person', uuid=cls.continuing_admission.uuid
        )

        cls.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate=cls.general_admission.candidate,
        )

        cls.doctorate_url = resolve_url('admission:doctorate:update:person', uuid=cls.doctorate_admission.uuid)

    def setUp(self) -> None:
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", "mimetype": "application/pdf"},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document.api.utils.confirm_remote_upload", side_effect=lambda token, upload_to: token)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_already_registered_field_initialization(self):
        form = AdmissionPersonForm(
            instance=PersonFactory(
                last_registration_year=AcademicYearFactory(year=2020),
            ),
        )
        self.assertEqual(form.initial.get('already_registered'), True)

        form = AdmissionPersonForm(
            instance=PersonFactory(
                last_registration_year=None,
            ),
        )
        self.assertEqual(form.initial.get('already_registered'), False)

    def test_unknown_birth_date_field_initialization(self):
        form = AdmissionPersonForm(
            instance=PersonFactory(
                birth_year=1990,
            ),
        )
        self.assertEqual(form.initial.get('unknown_birth_date'), True)

        form = AdmissionPersonForm(
            instance=PersonFactory(
                birth_year=None,
            ),
        )
        self.assertEqual(form.initial.get('unknown_birth_date'), None)

    def test_country_fields_initialization(self):
        # Without birth or citizenship country
        form = AdmissionPersonForm(
            instance=PersonFactory(
                birth_country=None,
                country_of_citizenship=None,
            ),
        )
        self.assertEqual(len(form.fields['birth_country'].queryset), 0)
        self.assertEqual(len(form.fields['country_of_citizenship'].queryset), 0)

        # With birth country but no citizenship country
        form = AdmissionPersonForm(
            instance=PersonFactory(
                birth_country=self.france_country,
                country_of_citizenship=None,
            ),
        )
        self.assertIn(self.france_country, form.fields['birth_country'].queryset)

        # With citizenship country but no birth country
        form = AdmissionPersonForm(
            instance=PersonFactory(
                birth_country=None,
                country_of_citizenship=self.belgium_country,
            ),
        )
        self.assertIn(self.belgium_country, form.fields['country_of_citizenship'].queryset)

        # With birth country and citizenship country
        form = AdmissionPersonForm(
            instance=PersonFactory(
                birth_country=self.france_country,
                country_of_citizenship=self.belgium_country,
            ),
        )
        self.assertIn(self.france_country, form.fields['birth_country'].queryset)
        self.assertIn(self.belgium_country, form.fields['country_of_citizenship'].queryset)

    def test_identification_type_field_initialization(self):
        # With id card number
        form = AdmissionPersonForm(
            instance=PersonFactory(
                id_card_number='123456789',
                passport_number='',
            ),
        )
        self.assertEqual(form.initial.get('identification_type'), IdentificationType.ID_CARD_NUMBER.name)

        # With passport number
        form = AdmissionPersonForm(
            instance=PersonFactory(
                id_card_number='',
                passport_number='123456789',
            ),
        )
        self.assertEqual(form.initial.get('identification_type'), IdentificationType.PASSPORT_NUMBER.name)

    def test_national_number_field_initialization(self):
        # With national number
        form = AdmissionPersonForm(
            instance=PersonFactory(
                national_number='123456789',
                passport_number='',
            ),
        )
        self.assertEqual(form.initial.get('has_national_number'), True)

        # With passport number
        form = AdmissionPersonForm(
            instance=PersonFactory(
                national_number='',
                passport_number='123456789',
            ),
        )
        self.assertEqual(form.initial.get('has_national_number'), False)

        # With id card number
        form = AdmissionPersonForm(
            instance=PersonFactory(
                national_number='',
                passport_number='',
                id_card_number='123456789',
            ),
        )
        self.assertEqual(form.initial.get('has_national_number'), False)

        # Without any number
        form = AdmissionPersonForm(
            instance=PersonFactory(
                national_number='',
                passport_number='',
                id_card_number='',
            ),
        )
        self.assertEqual(form.initial.get('has_national_number'), None)

    def form_submission_without_any_data(self):
        form = AdmissionPersonForm(
            data={},
        )
        self.assertFalse(form.is_valid())
        errors_fields = [
            'first_name',
            'last_name',
            'birth_date',
            'birth_country',
            'birth_place',
            'sex',
            'gender',
            'civil_state',
            'has_national_number',
            'identification_type',
        ]
        self.assertCountEqual(form.errors.keys(), errors_fields)

    def test_base_data_form_submission(self):
        form = AdmissionPersonForm(
            data=self.form_data,
        )
        self.assertTrue(form.is_valid())

    def test_birth_dates_fields_submission(self):
        # The birth date is unknown and the birth year and the birth date are specified
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'birth_year': 1990,
                'birth_date': datetime.date(1990, 1, 1),
                'unknown_birth_date': True,
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('birth_year'), 1990)
        self.assertEqual(form.cleaned_data.get('birth_date'), None)

        # The birthdate is known and the birth year and the birth date are specified
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'birth_year': 1990,
                'birth_date': datetime.date(1990, 1, 1),
                'unknown_birth_date': False,
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('birth_year'), None)
        self.assertEqual(form.cleaned_data.get('birth_date'), datetime.date(1990, 1, 1))

        # The birth date is unknown but the birth year is not specified
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'birth_year': None,
                'unknown_birth_date': True,
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('birth_year', []))

        # The birth date is known but not specified
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'birth_date': None,
                'unknown_birth_date': False,
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('birth_date', []))

        # Nothing is specified -> the birth date is required
        form = AdmissionPersonForm(
            data={},
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('birth_date', []))

    def test_last_registration_fields_submission(self):
        # The candidate hasn't already been registered but the related fields are specified -> to clean
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'already_registered': False,
                'last_registration_year': self.academic_year.pk,
                'last_registration_id': '01234567',
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('last_registration_year'), None)
        self.assertEqual(form.cleaned_data.get('last_registration_id'), '')

        # The candidate has already been registered but one related field is missing
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'already_registered': True,
                'last_registration_year': None,
                'last_registration_id': '1234567',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('last_registration_year', []))

    def test_name_fields_on_submission(self):
        # The first name and / or the last name must be specified
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'first_name': '',
                'last_name': '',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(_('This field is required if the surname is missing.'), form.errors.get('first_name', []))
        self.assertIn(_('This field is required if the first name is missing.'), form.errors.get('last_name', []))

    def test_national_number_fields(self):
        # The candidate is belgian and resides in Belgium -> the belgian national number is required
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'has_national_number': False,
                'national_number': '',
                'id_card': ['file-2-token'],
                'country_of_citizenship': self.belgium_country.pk,
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('national_number', []))
        self.assertEqual(form.cleaned_data.get('id_card'), ['file-2-token'])

        # The candidate indicated that he has a belgian national number -> the belgian national number is required
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'has_national_number': True,
                'national_number': '',
                'id_card': ['file-2-token'],
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('national_number', []))
        self.assertEqual(form.cleaned_data.get('id_card'), ['file-2-token'])

        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'has_national_number': True,
                'national_number': '01234567899',
                'passport_number': '0123456',
                'id_card_number': '0123456',
                'passport': ['file-1-token'],
                'id_card': ['file-2-token'],
            },
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('national_number'), '01234567899')
        self.assertEqual(form.cleaned_data.get('passport_number'), '')
        self.assertEqual(form.cleaned_data.get('id_card_number'), '')
        self.assertEqual(form.cleaned_data.get('passport'), [])
        self.assertEqual(form.cleaned_data.get('id_card'), ['file-2-token'])

        # The candidate indicated that he has another national number -> this number is required
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'country_of_citizenship': self.france_country.pk,
                'has_national_number': False,
                'identification_type': IdentificationType.ID_CARD_NUMBER.name,
                'id_card_number': '',
                'id_card': ['file-2-token'],
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('id_card_number', []))
        self.assertEqual(form.cleaned_data.get('id_card'), ['file-2-token'])

        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'country_of_citizenship': self.france_country.pk,
                'has_national_number': False,
                'identification_type': IdentificationType.ID_CARD_NUMBER.name,
                'id_card_number': '0123456',
                'id_card': ['file-2-token'],
                'national_number': '01234567899',
                'passport_number': '0123456',
                'passport': ['file-1-token'],
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('id_card_number'), '0123456')
        self.assertEqual(form.cleaned_data.get('passport_number'), '')
        self.assertEqual(form.cleaned_data.get('id_card'), ['file-2-token'])
        self.assertEqual(form.cleaned_data.get('national_number'), '')
        self.assertEqual(form.cleaned_data.get('passport'), [])

        # The candidate indicated that he has a passport number -> this number is required
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'country_of_citizenship': self.france_country.pk,
                'has_national_number': False,
                'identification_type': IdentificationType.PASSPORT_NUMBER.name,
                'passport_number': '',
                'passport': ['file-1-token'],
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('passport_number', []))
        self.assertEqual(form.cleaned_data.get('passport'), ['file-1-token'])

        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'country_of_citizenship': self.france_country.pk,
                'has_national_number': False,
                'identification_type': IdentificationType.PASSPORT_NUMBER.name,
                'passport_number': '0123456',
                'passport': ['file-1-token'],
                'id_card_number': '0123456',
                'national_number': '01234567899',
                'id_card': ['file-2-token'],
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('passport_number'), '0123456')
        self.assertEqual(form.cleaned_data.get('id_card_number'), '')
        self.assertEqual(form.cleaned_data.get('id_card'), [])
        self.assertEqual(form.cleaned_data.get('national_number'), '')
        self.assertEqual(form.cleaned_data.get('passport'), ['file-1-token'])

        # Some data are specified but the type of national number is not -> to clean
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'country_of_citizenship': self.france_country.pk,
                'has_national_number': None,
                'identification_type': '',
                'passport_number': '0123456',
                'passport': ['file-1-token'],
                'id_card_number': '0123456',
                'national_number': '01234567899',
                'id_card': ['file-2-token'],
            },
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.cleaned_data.get('passport_number'), '')
        self.assertEqual(form.cleaned_data.get('id_card_number'), '')
        self.assertEqual(form.cleaned_data.get('id_card'), [])
        self.assertEqual(form.cleaned_data.get('national_number'), '')
        self.assertEqual(form.cleaned_data.get('passport'), [])

    def test_transform_fields_to_title_case(self):
        form = AdmissionPersonForm(
            data={
                **self.form_data,
                'first_name': 'JOHN',
                'last_name': 'DOE',
                'middle_name': 'JIM',
                'birth_place': 'LOUVAIN-LA-NEUVE',
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('first_name'), 'John')
        self.assertEqual(form.cleaned_data.get('last_name'), 'Doe')
        self.assertEqual(form.cleaned_data.get('middle_name'), 'Jim')
        self.assertEqual(form.cleaned_data.get('birth_place'), 'Louvain-La-Neuve')

    def test_general_person_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        # No residential address
        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)

    def test_general_person_form_on_get(self):
        self.client.force_login(user=self.sic_manager_user)

        # No residential address
        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['BE_ISO_CODE'], self.belgium_country.pk)

        # Legal domicile > Belgium
        residential_address = PersonAddressFactory(
            person=self.general_admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
            country=self.belgium_country,
        )

        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)

        # Legal domicile > Foreign country
        residential_address.country = self.france_country
        residential_address.save()

        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)

    def test_general_person_form_post_with_valid_data(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.general_url, self.form_data)

        self.assertRedirects(
            response,
            reverse('admission:general-education:person', args=[self.general_admission.uuid]),
        )

        candidate = Person.objects.get(pk=self.general_admission.candidate.pk)
        self.assertEqual(candidate.first_name, self.form_data['first_name'])
        self.assertEqual(candidate.last_name, self.form_data['last_name'])

    def test_general_person_form_post_updates_submitted_profile_if_necessary(self):
        self.client.force_login(user=self.sic_manager_user)

        general_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.general_admission.training.management_entity,
            training__academic_year=self.general_admission.training.academic_year,
            candidate__phone_mobile='987654321',
            candidate__private_email='joe.foe@example.com',
            submitted_profile={},
        )

        url = resolve_url('admission:general-education:update:person', uuid=general_admission.uuid)

        default_submitted_profile = {
            'identification': {
                'first_name': 'Joe',
                'last_name': 'Poe',
                'gender': ChoixGenre.X.name,
                'country_of_citizenship': 'FR',
            },
            'coordinates': {
                'country': 'BE',
                'postal_code': '1348',
                'city': 'Louvain-La-Neuve',
                'place': 'P1',
                'street': 'University street',
                'street_number': '1',
                'postal_box': 'PB1',
            },
        }

        # No submitted profile so it should not be updated
        response = self.client.post(url, data=self.form_data)

        self.assertEqual(response.status_code, 302)

        general_admission.refresh_from_db()
        self.assertEqual(general_admission.submitted_profile, {})

        # The submitted profile exists so it should be updated with the newer data
        general_admission.submitted_profile = default_submitted_profile
        general_admission.save()

        response = self.client.post(url, data=self.form_data)

        self.assertEqual(response.status_code, 302)

        general_admission.refresh_from_db()
        self.assertEqual(
            general_admission.submitted_profile,
            {
                'coordinates': default_submitted_profile.get('coordinates'),
                'identification': {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'gender': ChoixGenre.H.name,
                    'country_of_citizenship': 'BE',
                },
            },
        )

    def test_general_person_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        response = self.client.post(self.general_url, {})
        self.assertEqual(response.status_code, 200)

    def test_continuing_person_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        # No residential address
        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)

    def test_continuing_person_form_on_get(self):
        self.client.force_login(user=self.sic_manager_user)

        # No residential address
        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['BE_ISO_CODE'], self.belgium_country.pk)

        # Legal domicile > Belgium
        residential_address = PersonAddressFactory(
            person=self.continuing_admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
            country=self.belgium_country,
        )

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)

        # Legal domicile > Foreign country
        residential_address.country = self.france_country
        residential_address.save()

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)

    def test_continuing_person_form_post_with_valid_data(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.continuing_url, self.form_data)

        self.assertRedirects(
            response, reverse('admission:continuing-education:person', args=[self.continuing_admission.uuid])
        )

        candidate = Person.objects.get(pk=self.doctorate_admission.candidate.pk)
        self.assertEqual(candidate.first_name, self.form_data['first_name'])
        self.assertEqual(candidate.last_name, self.form_data['last_name'])

    def test_continuing_person_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        response = self.client.post(self.continuing_url, {})
        self.assertEqual(response.status_code, 200)

    def test_doctorate_person_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        # No residential address
        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 200)

    def test_doctorate_person_form_on_get(self):
        self.client.force_login(user=self.sic_manager_user)

        # No residential address
        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['BE_ISO_CODE'], self.belgium_country.pk)

        # Legal domicile > Belgium
        residential_address = PersonAddressFactory(
            person=self.doctorate_admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
            country=self.belgium_country,
        )

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 200)

        # Legal domicile > Foreign country
        residential_address.country = self.france_country
        residential_address.save()

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 200)

    def test_doctorate_person_form_post_with_valid_data(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(self.doctorate_url, self.form_data)

        self.assertRedirects(response, reverse('admission:doctorate:person', args=[self.doctorate_admission.uuid]))

        candidate = Person.objects.get(pk=self.doctorate_admission.candidate.pk)
        self.assertEqual(candidate.first_name, self.form_data['first_name'])
        self.assertEqual(candidate.last_name, self.form_data['last_name'])

    def test_doctorate_person_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        response = self.client.post(self.doctorate_url, {})
        self.assertEqual(response.status_code, 200)
