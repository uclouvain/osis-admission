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

import datetime
import uuid
from unittest.mock import patch

import freezegun
from django.conf import settings
from django.http import QueryDict
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.forms.admission.person import AdmissionPersonForm
from admission.models import ContinuingEducationAdmission, DoctorateAdmission, GeneralEducationAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
    AdmissionEducationalValuatedExperiencesFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import (
    SicManagementRoleFactory,
    ProgramManagerRoleFactory,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.models.enums.civil_state import CivilState
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_address import PersonAddressFactory
from osis_profile import BE_ISO_CODE, FR_ISO_CODE
from osis_profile.models.enums.curriculum import TranscriptType
from osis_profile.models.enums.person import ChoixGenre, ChoixSexe
from reference.tests.factories.country import CountryFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
@freezegun.freeze_time('2021-12-01')
class AdmissionPersonFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.belgium_country = CountryFactory(iso_code=BE_ISO_CODE)
        cls.france_country = CountryFactory(iso_code=FR_ISO_CODE)
        cls.academic_year = AcademicYearFactory(year=2021)
        cls.form_data = QueryDict(
            urlencode(
                {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'birth_date': datetime.date(1990, 1, 1),
                    'birth_country': cls.belgium_country.pk,
                    'country_of_citizenship': cls.belgium_country.pk,
                    'birth_place': 'Louvain-la-Neuve',
                    'sex': ChoixSexe.M.name,
                    'gender': ChoixGenre.H.name,
                    'civil_state': CivilState.MARRIED.name,
                    'has_national_number': True,
                    'national_number': '01234567899',
                    'id_card_expiry_date': datetime.date(2020, 2, 2),
                    'passport_expiry_date': datetime.date(2020, 2, 2),
                    'id_photo_0': str(uuid.uuid4()),
                    'id_card_0': str(uuid.uuid4()),
                }
            ),
            mutable=True,
        )

        cls.form_data_as_dict = cls.form_data.dict()

        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)

        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__global_id="80001234",
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        cls.general_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user

        cls.general_url = resolve_url('admission:general-education:update:person', uuid=cls.general_admission.uuid)

        cls.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )

        cls.continuing_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.continuing_admission.training.education_group,
        ).person.user

        cls.continuing_url = resolve_url(
            'admission:continuing-education:update:person',
            uuid=cls.continuing_admission.uuid,
        )

        cls.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        cls.doctorate_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.doctorate_admission.training.education_group,
        ).person.user

        cls.doctorate_url = resolve_url('admission:doctorate:update:person', uuid=cls.doctorate_admission.uuid)

    def setUp(self) -> None:
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            side_effect=lambda token, *args, **kwargs: {
                "name": "myfile",
                "mimetype": (
                    "image/png" if token in {'file-0-token', self.form_data['id_photo_0']} else "application/pdf"
                ),
                "size": 1,
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "infrastructure.messages_bus.message_bus_instance.publish",
            side_effect=lambda *args, **kwargs: None,
        )
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

    def test_last_registration_fields_submission(self):
        # The candidate hasn't already been registered but the related fields are specified -> to clean
        form = AdmissionPersonForm(
            data={
                **self.form_data_as_dict,
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
                **self.form_data_as_dict,
                'already_registered': True,
                'last_registration_year': None,
                'last_registration_id': '1234567',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('last_registration_year', []))

    def test_general_person_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)

    def test_general_person_form_on_get_program_manager(self):
        self.client.force_login(user=self.general_program_manager_user)

        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 403)

    def test_general_person_form_on_post_program_manager_is_forbidden(self):
        self.client.force_login(user=self.general_program_manager_user)

        response = self.client.post(self.general_url, self.form_data)

        self.assertEqual(response.status_code, 403)

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
            fetch_redirect_response=False,
        )

        candidate = Person.objects.get(pk=self.general_admission.candidate.pk)
        self.assertEqual(candidate.first_name, self.form_data['first_name'])
        self.assertEqual(candidate.last_name, self.form_data['last_name'])

        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

    def test_general_person_form_post_without_country_of_citizenship(self):
        self.client.force_login(user=self.sic_manager_user)

        data = self.form_data.copy()
        data['country_of_citizenship'] = ''
        response = self.client.post(self.general_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('country_of_citizenship', response.context['form'].errors)

    def test_general_person_form_post_updates_submitted_profile_if_necessary(self):
        self.client.force_login(user=self.sic_manager_user)

        general_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.general_admission.training.management_entity,
            training__academic_year=self.general_admission.training.academic_year,
            candidate__phone_mobile='987654321',
            candidate__private_email='joe.foe@example.com',
            candidate__global_id="81234565",
            submitted_profile={},
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
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
                'city': 'Louvain-la-Neuve',
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
                    'birth_date': '1990-01-01',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'gender': ChoixGenre.H.name,
                    'country_of_citizenship': 'BE',
                },
            },
        )

    def test_computation_of_missing_documents(self):
        self.client.force_login(user=self.sic_manager_user)

        # Add curriculum experiences
        educational_experience = EducationalExperienceFactory(
            person=self.general_admission.candidate,
            transcript_type=TranscriptType.ONE_FOR_ALL_YEARS.name,
            transcript=[],
        )
        EducationalExperienceYearFactory(
            educational_experience=educational_experience,
            academic_year=self.general_admission.training.academic_year,
        )
        transcript_identifier = f'CURRICULUM.{educational_experience.uuid}.RELEVE_NOTES'

        # No valuated experience -> no document
        response = self.client.post(self.general_url, self.form_data)

        self.assertEqual(response.status_code, 302)

        self.general_admission.refresh_from_db()
        self.assertNotIn(transcript_identifier, self.general_admission.requested_documents)

        # Valuated experiences but by another admission -> no document
        educational_valuation = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.continuing_admission,
            educationalexperience=educational_experience,
        )

        response = self.client.post(self.general_url, self.form_data)

        self.assertEqual(response.status_code, 302)

        self.general_admission.refresh_from_db()

        self.assertNotIn(transcript_identifier, self.general_admission.requested_documents)

        # Valuated experiences by this admission -> retrieve documents
        educational_valuation.baseadmission = self.general_admission
        educational_valuation.save()

        response = self.client.post(self.general_url, self.form_data)

        self.assertEqual(response.status_code, 302)

        self.general_admission.refresh_from_db()

        self.assertNotIn(transcript_identifier, self.general_admission.requested_documents)

    def test_general_person_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        response = self.client.post(self.general_url, {})
        self.assertEqual(response.status_code, 200)

    def test_continuing_person_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)

        continuing_admission = ContinuingEducationAdmissionFactory(
            candidate=self.continuing_admission.candidate,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)

        doctorate_admission = DoctorateAdmissionFactory(
            candidate=self.continuing_admission.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 403)

        doctorate_admission.delete()

        general_admission = GeneralEducationAdmissionFactory(
            candidate=self.continuing_admission.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 403)

    def test_continuing_person_form_on_get_program_manager(self):
        self.client.force_login(user=self.continuing_program_manager_user)

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)

        continuing_admission = ContinuingEducationAdmissionFactory(
            candidate=self.continuing_admission.candidate,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)

        doctorate_admission = DoctorateAdmissionFactory(
            candidate=self.continuing_admission.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 403)

        doctorate_admission.delete()

        general_admission = GeneralEducationAdmissionFactory(
            candidate=self.continuing_admission.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 403)

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
            response,
            reverse('admission:continuing-education:person', args=[self.continuing_admission.uuid]),
            fetch_redirect_response=False,
        )

        candidate = Person.objects.get(pk=self.continuing_admission.candidate.pk)
        self.assertEqual(candidate.first_name, self.form_data['first_name'])
        self.assertEqual(candidate.last_name, self.form_data['last_name'])

    def test_continuing_person_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        response = self.client.post(self.continuing_url, {})
        self.assertEqual(response.status_code, 200)

    def test_doctorate_person_form_on_get_program_manager(self):
        self.client.force_login(user=self.doctorate_program_manager_user)

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 403)

    def test_doctorate_person_form_on_get_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 200)

        ContinuingEducationAdmissionFactory(
            candidate=self.doctorate_admission.candidate,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 200)

        DoctorateAdmissionFactory(
            candidate=self.doctorate_admission.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 200)

        GeneralEducationAdmissionFactory(
            candidate=self.doctorate_admission.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, 403)

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

        self.assertRedirects(
            response,
            reverse('admission:doctorate:person', args=[self.doctorate_admission.uuid]),
            fetch_redirect_response=False,
        )

        candidate = Person.objects.get(pk=self.doctorate_admission.candidate.pk)
        self.assertEqual(candidate.first_name, self.form_data['first_name'])
        self.assertEqual(candidate.last_name, self.form_data['last_name'])

    def test_doctorate_person_form_post_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)
        response = self.client.post(self.doctorate_url, {})
        self.assertEqual(response.status_code, 200)

    def test_doctorate_program_manager_is_forbidden(self):
        self.client.force_login(user=self.doctorate_program_manager_user)

        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.doctorate_url)
        self.assertEqual(response.status_code, 403)
