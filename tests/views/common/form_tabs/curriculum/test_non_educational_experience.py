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
import itertools
import uuid
from unittest import mock

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.contrib.models.base import (
    AdmissionProfessionalValuatedExperiences,
)
from admission.contrib.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.tests.factories.curriculum import (
    ProfessionalExperienceFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from osis_profile.models import ProfessionalExperience
from osis_profile.models.enums.curriculum import ActivityType, ActivitySector
from reference.tests.factories.country import CountryFactory


# TODO: Remove duplicate tests with osis_profile
@freezegun.freeze_time('2023-01-01')
class CurriculumNonEducationalExperienceFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020]]
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=cls.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__country_of_citizenship=CountryFactory(european_union=False),
            candidate__graduated_from_high_school_year=None,
            candidate__last_registration_year=None,
            candidate__id_photo=[],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user

        cls.file_uuid = uuid.uuid4()

    def setUp(self):
        # Create data
        self.experience: ProfessionalExperience = ProfessionalExperienceFactory(
            person=self.general_admission.candidate,
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2021, 12, 31),
            type=ActivityType.WORK.name,
            role='Function',
            sector=ActivitySector.PRIVATE.name,
            institute_name='Institute',
            certificate=[self.file_uuid],
            activity='Activity',
        )

        # Mock osis document api
        patcher = mock.patch("osis_document.api.utils.get_remote_token", side_effect=lambda value, **kwargs: value)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE, "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: value

        # Targeted url
        self.form_url = resolve_url(
            'admission:general-education:update:curriculum:non_educational',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )
        self.create_url = resolve_url(
            'admission:general-education:update:curriculum:non_educational_create',
            uuid=self.general_admission.uuid,
        )

    def test_update_curriculum_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        month_choices = [
            ['', ' - '],
            [1, 'Janvier'],
            [2, 'Février'],
            [3, 'Mars'],
            [4, 'Avril'],
            [5, 'Mai'],
            [6, 'Juin'],
            [7, 'Juillet'],
            [8, 'Août'],
            [9, 'Septembre'],
            [10, 'Octobre'],
            [11, 'Novembre'],
            [12, 'Décembre'],
        ]

        year_choices = [['', ' - ']] + [[year, year] for year in range(2023, 1900, -1)]

        # Start date
        self.assertEqual(form['start_date_month'].value(), 1)
        self.assertEqual(
            [[choice[0], choice[1]] for choice in form.fields['start_date_month'].choices],
            month_choices,
        )
        self.assertEqual(form['start_date_year'].value(), 2020)
        self.assertEqual(
            [[choice[0], choice[1]] for choice in form.fields['start_date_year'].choices],
            year_choices,
        )

        # End date
        self.assertEqual(form['end_date_month'].value(), 12)
        self.assertEqual(
            [[choice[0], choice[1]] for choice in form.fields['end_date_month'].choices],
            month_choices,
        )
        self.assertEqual(form['end_date_year'].value(), 2021)
        self.assertEqual(
            [[choice[0], choice[1]] for choice in form.fields['end_date_year'].choices],
            year_choices,
        )

        # Type
        self.assertEqual(form['type'].value(), ActivityType.WORK.name)

        # Function
        self.assertEqual(form['role'].value(), 'Function')

        # Sector
        self.assertEqual(form['sector'].value(), ActivitySector.PRIVATE.name)

        # Institute
        self.assertEqual(form['institute_name'].value(), 'Institute')

        # Certificate
        self.assertEqual(form['certificate'].value(), [self.file_uuid])

        # Activity
        self.assertEqual(form['activity'].value(), 'Activity')

    def test_submit_form_with_missing_fields(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('start_date_month', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('start_date_year', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('end_date_month', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('end_date_year', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('type', []))

    def test_submit_form_with_missing_fields_for_work(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            {
                'start_date_month': 1,
                'start_date_year': 2020,
                'end_date_month': 12,
                'end_date_year': 2021,
                'type': ActivityType.WORK.name,
                'activity': 'Activity',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('role', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('sector', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('institute_name', []))

        self.assertEqual(form.cleaned_data['activity'], '')

    def test_submit_form_with_missing_fields_for_other_activity(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            {
                'start_date_month': 1,
                'start_date_year': 2020,
                'end_date_month': 12,
                'end_date_year': 2021,
                'type': ActivityType.OTHER.name,
                'role': 'Role',
                'sector': ActivitySector.PRIVATE.name,
                'institute_name': 'Institute',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('activity', []))

        self.assertEqual(form.cleaned_data['role'], '')
        self.assertEqual(form.cleaned_data['sector'], '')
        self.assertEqual(form.cleaned_data['institute_name'], '')

    def test_submit_valid_form_for_work(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            {
                'start_date_month': 2,
                'start_date_year': 2019,
                'end_date_month': 3,
                'end_date_year': 2022,
                'type': ActivityType.WORK.name,
                'role': 'Role',
                'sector': ActivitySector.PRIVATE.name,
                'institute_name': 'Institute',
                'activity': 'Activity',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.experience.refresh_from_db()

        self.assertEqual(self.experience.start_date, datetime.date(2019, 2, 1))
        self.assertEqual(self.experience.end_date, datetime.date(2022, 3, 31))
        self.assertEqual(self.experience.type, ActivityType.WORK.name)
        self.assertEqual(self.experience.role, 'Role')
        self.assertEqual(self.experience.sector, ActivitySector.PRIVATE.name)
        self.assertEqual(self.experience.institute_name, 'Institute')
        self.assertEqual(self.experience.activity, '')

        # Check the admission
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            self.general_admission.requested_documents,
        )

    def test_submit_valid_form_for_other_activity_and_redirect(self):
        self.client.force_login(self.sic_manager_user)

        admission_url = resolve_url('admission')
        expected_url = f'{admission_url}#custom_hash'

        response = self.client.post(
            f'{self.form_url}?next={admission_url}&next_hash_url=custom_hash',
            {
                'start_date_month': 2,
                'start_date_year': 2019,
                'end_date_month': 3,
                'end_date_year': 2022,
                'type': ActivityType.OTHER.name,
                'role': 'Role',
                'sector': ActivitySector.PRIVATE.name,
                'institute_name': 'Institute',
                'activity': 'Activity',
            },
        )

        self.assertRedirects(response=response, fetch_redirect_response=False, expected_url=expected_url)

        self.experience.refresh_from_db()

        self.assertEqual(self.experience.start_date, datetime.date(2019, 2, 1))
        self.assertEqual(self.experience.end_date, datetime.date(2022, 3, 31))
        self.assertEqual(self.experience.type, ActivityType.OTHER.name)
        self.assertEqual(self.experience.role, '')
        self.assertEqual(self.experience.sector, '')
        self.assertEqual(self.experience.institute_name, '')
        self.assertEqual(self.experience.activity, 'Activity')

    def test_submit_valid_form_for_create_a_new_work_activity(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.create_url,
            {
                'start_date_month': 2,
                'start_date_year': 2019,
                'end_date_month': 3,
                'end_date_year': 2022,
                'type': ActivityType.WORK.name,
                'role': 'My new role',
                'sector': ActivitySector.PRIVATE.name,
                'institute_name': 'Institute',
                'activity': 'Activity',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.experience.refresh_from_db()

        created_experience = ProfessionalExperience.objects.filter(
            role='My new role',
            person=self.general_admission.candidate,
        ).first()

        self.assertIsNotNone(created_experience)

        self.assertEqual(created_experience.start_date, datetime.date(2019, 2, 1))
        self.assertEqual(created_experience.end_date, datetime.date(2022, 3, 31))
        self.assertEqual(created_experience.type, ActivityType.WORK.name)
        self.assertEqual(created_experience.role, 'My new role')
        self.assertEqual(created_experience.sector, ActivitySector.PRIVATE.name)
        self.assertEqual(created_experience.institute_name, 'Institute')
        self.assertEqual(created_experience.activity, '')

        # Check that the experience has been valuated
        self.assertTrue(
            AdmissionProfessionalValuatedExperiences.objects.filter(
                baseadmission_id=self.general_admission.uuid,
                professionalexperience_id=created_experience.uuid,
            ).exists()
        )

        # Check that the checklist has been updated
        self.general_admission.refresh_from_db()

        last_experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][-1]

        self.assertEqual(
            last_experience_checklist['extra']['identifiant'],
            str(created_experience.uuid),
        )

        self.assertEqual(
            last_experience_checklist,
            {
                'libelle': 'To be processed',
                'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                'extra': {
                    'identifiant': str(created_experience.uuid),
                    'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
                },
                'enfants': [],
            },
        )


@freezegun.freeze_time('2022-01-01')
class CurriculumNonEducationalExperienceDeleteViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=cls.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__country_of_citizenship=CountryFactory(european_union=False),
            candidate__graduated_from_high_school_year=None,
            candidate__last_registration_year=None,
            candidate__id_photo=[],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user
        cls.file_uuid = uuid.uuid4()

    def setUp(self):
        # Create data
        self.experience: ProfessionalExperience = ProfessionalExperienceFactory(
            person=self.general_admission.candidate,
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2021, 12, 31),
            type=ActivityType.WORK.name,
            role='Function',
            sector=ActivitySector.PRIVATE.name,
            institute_name='Institute',
            certificate=[self.file_uuid],
            activity='Activity',
        )

        # Targeted url
        self.delete_url = resolve_url(
            'admission:general-education:update:curriculum:non_educational_delete',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )

    def test_delete_experience_from_curriculum_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_experience_from_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.delete(self.delete_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_delete_experience_from_curriculum_and_redirect(self):
        self.client.force_login(self.sic_manager_user)

        admission_url = resolve_url('admission')
        expected_url = f'{admission_url}#custom_hash'

        response = self.client.delete(f'{self.delete_url}?next={admission_url}&next_hash_url=custom_hash')
        self.assertRedirects(response=response, fetch_redirect_response=False, expected_url=expected_url)

    def test_delete_unknown_experience_returns_404(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.delete(
            resolve_url(
                'admission:general-education:update:curriculum:non_educational_delete',
                uuid=self.general_admission.uuid,
                experience_uuid=uuid.uuid4(),
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_known_experience(self):
        self.client.force_login(self.sic_manager_user)

        # Simulate a valuated experience
        AdmissionProfessionalValuatedExperiences.objects.create(
            baseadmission_id=self.general_admission.uuid,
            professionalexperience_id=self.experience.uuid,
        )

        self.general_admission.checklist['current']['parcours_anterieur']['enfants'] = [
            Checklist.initialiser_checklist_experience(experience_uuid=self.experience.uuid).to_dict()
        ]

        self.general_admission.save()

        response = self.client.delete(self.delete_url)

        self.assertFalse(ProfessionalExperience.objects.filter(uuid=self.experience.uuid).exists())

        self.assertFalse(
            AdmissionProfessionalValuatedExperiences.objects.filter(
                professionalexperience_id=self.experience.uuid
            ).exists()
        )

        self.general_admission.refresh_from_db()

        self.assertEqual(
            self.general_admission.checklist['current']['parcours_anterieur']['enfants'],
            [],
        )
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            self.general_admission.requested_documents,
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)


@freezegun.freeze_time('2022-01-01')
class CurriculumNonEducationalExperienceDuplicateViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=cls.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__country_of_citizenship=CountryFactory(european_union=False),
            candidate__graduated_from_high_school_year=None,
            candidate__last_registration_year=None,
            candidate__id_photo=[],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user
        cls.file_uuid = uuid.uuid4()
        cls.file_uuid_str = str(cls.file_uuid)
        cls.duplicate_uuid = uuid.uuid4()
        cls.duplicate_uuid_str = str(cls.duplicate_uuid)

    def setUp(self):
        # Create data
        self.experience: ProfessionalExperience = ProfessionalExperienceFactory(
            person=self.general_admission.candidate,
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2021, 12, 31),
            type=ActivityType.WORK.name,
            role='Function',
            sector=ActivitySector.PRIVATE.name,
            institute_name='Institute',
            certificate=[self.file_uuid],
            activity='Activity',
            external_id='id_experience',
        )

        # Targeted url
        self.duplicate_url = resolve_url(
            'admission:general-education:update:curriculum:non_educational_duplicate',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )

        # Mock osis document api
        self.get_several_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        self.get_several_remote_metadata_patched = self.get_several_remote_metadata_patcher.start()
        self.get_several_remote_metadata_patched.return_value = {'foobar': {'name': 'certificate.pdf', 'size': 1}}
        self.addCleanup(self.get_several_remote_metadata_patcher.stop)

        self.get_remote_tokens_patcher = mock.patch('osis_document.api.utils.get_remote_tokens')
        self.get_remote_tokens_patched = self.get_remote_tokens_patcher.start()
        self.get_remote_tokens_patched.return_value = {self.file_uuid_str: 'foobar'}
        self.addCleanup(self.get_remote_tokens_patcher.stop)

        self.documents_remote_duplicate_patcher = mock.patch('osis_document.api.utils.documents_remote_duplicate')
        self.documents_remote_duplicate_patched = self.documents_remote_duplicate_patcher.start()
        self.documents_remote_duplicate_patched.return_value = {self.file_uuid_str: self.duplicate_uuid_str}
        self.addCleanup(self.documents_remote_duplicate_patcher.stop)

    def test_duplicate_experience_from_curriculum_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.post(self.duplicate_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_experience_from_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.post(self.duplicate_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_duplicate_experience_from_curriculum_and_redirect(self):
        self.client.force_login(self.sic_manager_user)

        admission_url = resolve_url('admission')
        expected_url = f'{admission_url}#custom_hash'

        response = self.client.post(f'{self.duplicate_url}?next={admission_url}&next_hash_url=custom_hash')
        self.assertRedirects(response=response, fetch_redirect_response=False, expected_url=expected_url)

    def test_duplicate_unknown_experience_returns_404(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            resolve_url(
                'admission:general-education:update:curriculum:non_educational_duplicate',
                uuid=self.general_admission.uuid,
                experience_uuid=uuid.uuid4(),
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @freezegun.freeze_time('2022-02-02')
    def test_duplicate_known_but_not_valuated_experience(self):
        self.client.force_login(self.sic_manager_user)

        professional_experiences = ProfessionalExperience.objects.filter(person=self.general_admission.candidate)

        self.assertEqual(professional_experiences.count(), 1)

        base_original_experience = professional_experiences.first()

        response = self.client.post(self.duplicate_url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check the data of the duplicated experience
        professional_experiences = ProfessionalExperience.objects.filter(person=self.general_admission.candidate)

        self.assertEqual(professional_experiences.count(), 2)

        if professional_experiences[0].uuid == base_original_experience.uuid:
            original_experience, duplicated_experience = professional_experiences
        else:
            duplicated_experience, original_experience = professional_experiences

        fields_to_duplicate = [
            'person',
            'institute_name',
            'start_date',
            'end_date',
            'type',
            'role',
            'sector',
            'activity',
        ]

        fields_to_update = [
            'external_id',
            'certificate',
        ]

        # Check that the original experience has not been updated
        for field in itertools.chain(fields_to_duplicate, fields_to_update):
            self.assertEqual(getattr(base_original_experience, field), getattr(original_experience, field))

        # Check that the duplicated experience is a valid copy of the original
        for field in fields_to_duplicate:
            self.assertEqual(getattr(original_experience, field), getattr(duplicated_experience, field))

        for field in fields_to_update:
            self.assertNotEqual(getattr(original_experience, field), getattr(duplicated_experience, field))

        self.assertEqual(duplicated_experience.external_id, None)
        self.assertEqual(duplicated_experience.certificate, [self.duplicate_uuid])

        self.documents_remote_duplicate_patched.assert_called_once_with(
            uuids=[self.file_uuid],
            with_modified_upload=True,
            upload_path_by_uuid={
                self.file_uuid_str: f'{self.general_admission.candidate.uuid}/curriculum/certificate.pdf',
            },
        )

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime(2022, 2, 2, 0, 0))

    def test_duplicate_known_valuated_experience(self):
        self.client.force_login(self.sic_manager_user)

        # Simulate valuated experiences
        other_valuated_admission_without_checklist = GeneralEducationAdmissionFactory(
            training=self.general_admission.training,
            candidate=self.general_admission.candidate,
            status=self.general_admission.status,
            checklist={},
        )
        other_valuated_admission_with_checklist = GeneralEducationAdmissionFactory(
            training=self.general_admission.training,
            candidate=self.general_admission.candidate,
            status=self.general_admission.status,
        )
        other_not_valuated_admission = GeneralEducationAdmissionFactory(
            training=self.general_admission.training,
            candidate=self.general_admission.candidate,
            status=self.general_admission.status,
        )

        professional_experiences = ProfessionalExperience.objects.filter(person=self.general_admission.candidate)

        self.assertEqual(professional_experiences.count(), 1)

        base_original_experience = professional_experiences.first()

        valuations = [
            AdmissionProfessionalValuatedExperiences.objects.create(
                baseadmission_id=admission.uuid,
                professionalexperience_id=self.experience.uuid,
            )
            for admission in [
                self.general_admission,
                other_valuated_admission_with_checklist,
                other_valuated_admission_without_checklist,
            ]
        ]

        response = self.client.post(self.duplicate_url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check the data of the valuations
        professional_experiences = ProfessionalExperience.objects.filter(person=self.general_admission.candidate)

        self.assertEqual(professional_experiences.count(), 2)

        if professional_experiences[0].uuid == base_original_experience.uuid:
            original_experience, duplicated_experience = professional_experiences
        else:
            duplicated_experience, original_experience = professional_experiences

        default_checklist = Checklist.initialiser_checklist_experience(
            experience_uuid=str(duplicated_experience.uuid),
        ).to_dict()

        duplicated_valuations = AdmissionProfessionalValuatedExperiences.objects.filter(
            professionalexperience_id=duplicated_experience.uuid,
        ).select_related('baseadmission')

        self.assertEqual(duplicated_valuations.count(), 3)

        self.assertCountEqual(
            [valuation.baseadmission.uuid for valuation in duplicated_valuations],
            [
                self.general_admission.uuid,
                other_valuated_admission_with_checklist.uuid,
                other_valuated_admission_without_checklist.uuid,
            ],
        )

        # Check that the checklists have been well initialized
        self.general_admission.refresh_from_db()
        other_valuated_admission_without_checklist.refresh_from_db()
        other_valuated_admission_with_checklist.refresh_from_db()
        other_not_valuated_admission.refresh_from_db()

        self.assertIn(
            default_checklist,
            self.general_admission.checklist.get('current', {}).get('parcours_anterieur', {}).get('enfants', []),
        )

        self.assertIn(
            default_checklist,
            other_valuated_admission_with_checklist.checklist.get('current', {})
            .get('parcours_anterieur', {})
            .get('enfants', []),
        )

        self.assertNotIn(
            default_checklist,
            other_not_valuated_admission.checklist.get('current', {}).get('parcours_anterieur', {}).get('enfants', []),
        )

        self.assertNotIn(
            default_checklist,
            other_valuated_admission_without_checklist.checklist.get('current', {})
            .get('parcours_anterieur', {})
            .get('enfants', []),
        )

    @freezegun.freeze_time('2022-01-01')
    class CurriculumNonEducationalExperienceValuateViewTestCase(TestCase):
        @classmethod
        def setUpTestData(cls):
            # Create data
            cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
            entity = EntityWithVersionFactory()

            cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
                training__management_entity=entity,
                status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            )

            # Create users
            cls.sic_manager_user = SicManagementRoleFactory(entity=entity).person.user
            cls.program_manager_user = ProgramManagerRoleFactory(
                education_group=cls.general_admission.training.education_group,
            ).person.user

        def setUp(self):
            # Create data
            self.experience: ProfessionalExperience = ProfessionalExperienceFactory(
                person=self.general_admission.candidate,
            )

            # Targeted url
            self.valuate_url = resolve_url(
                'admission:general-education:update:curriculum:non_educational_valuate',
                uuid=self.general_admission.uuid,
                experience_uuid=self.experience.uuid,
            )

        def test_valuate_experience_from_curriculum_is_not_allowed_for_fac_users(self):
            self.client.force_login(self.program_manager_user)
            response = self.client.post(self.valuate_url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        def test_valuate_experience_from_curriculum_is_allowed_for_sic_users(self):
            self.client.force_login(self.sic_manager_user)

            expected_url = resolve_url('admission:general-education:checklist', uuid=self.general_admission.uuid)

            response = self.client.post(self.valuate_url)

            self.assertRedirects(response=response, fetch_redirect_response=False, expected_url=expected_url)

        def test_valuate_experience_from_curriculum_and_redirect(self):
            self.client.force_login(self.sic_manager_user)

            admission_url = resolve_url('admission')
            expected_url = f'{admission_url}#custom_hash'

            response = self.client.post(f'{self.valuate_url}?next={admission_url}&next_hash_url=custom_hash')

            self.assertRedirects(response=response, fetch_redirect_response=False, expected_url=expected_url)

        def test_valuate_unknown_experience_returns_404(self):
            self.client.force_login(self.sic_manager_user)

            response = self.client.post(
                resolve_url(
                    'admission:general-education:update:curriculum:non_educational_valuate',
                    uuid=self.general_admission.uuid,
                    experience_uuid=uuid.uuid4(),
                ),
            )

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        def test_valuate_known_experience(self):
            self.client.force_login(self.sic_manager_user)

            default_experience_checklist = Checklist.initialiser_checklist_experience(
                str(self.experience.uuid)
            ).to_dict()

            response = self.client.post(self.valuate_url)

            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

            # Check that the experience has been valuated
            valuation = AdmissionProfessionalValuatedExperiences.objects.filter(
                professionalexperience_id=self.experience.uuid,
                baseadmission=self.general_admission,
            ).first()
            self.assertIsNotNone(valuation)

            # Check that the experience has been added to the checklist
            self.general_admission.refresh_from_db()

            saved_experience_checklist = [
                experience_checklist
                for experience_checklist in self.general_admission.checklist['current']['parcours_anterieur']['enfants']
                if experience_checklist.get('extra', {}).get('identifiant') == str(self.experience.uuid)
            ]

            self.assertEqual(len(saved_experience_checklist), 1)
            self.assertEqual(saved_experience_checklist[0], default_experience_checklist)

            # Check that the modified informations have been updated
            self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
            self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

            # Keep the experience checklist if one is already there
            saved_experience_checklist[0]['extra']['custom'] = 'custom value'
            self.general_admission.save(update_fields=['checklist'])

            valuation.delete()

            response = self.client.post(self.valuate_url)

            # Check that the experience has been valuated
            valuation = AdmissionProfessionalValuatedExperiences.objects.filter(
                professionalexperience_id=self.experience.uuid,
                baseadmission=self.general_admission,
            ).first()
            self.assertIsNotNone(valuation)

            # Check that the experience checklist has been kept
            self.general_admission.refresh_from_db()

            new_saved_experience_checklist = [
                experience_checklist
                for experience_checklist in self.general_admission.checklist['current']['parcours_anterieur']['enfants']
                if experience_checklist.get('extra', {}).get('identifiant') == str(self.experience.uuid)
            ]

            self.assertEqual(len(new_saved_experience_checklist), 1)
            self.assertNotEqual(new_saved_experience_checklist[0], default_experience_checklist)
            self.assertEqual(new_saved_experience_checklist[0], saved_experience_checklist[0])
