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

from admission.models import DoctorateAdmission
from admission.models.base import (
    AdmissionProfessionalValuatedExperiences,
)
from admission.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import (
    ProfessionalExperienceFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from osis_profile.models import ProfessionalExperience
from osis_profile.models.enums.curriculum import ActivityType, ActivitySector
from reference.tests.factories.country import CountryFactory


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

        cls.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=cls.academic_years[0],
            candidate=cls.general_admission.candidate,
            submitted=True,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user
        cls.doctorate_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.doctorate_admission.training.education_group,
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
        self.doctorate_duplicate_url = resolve_url(
            'admission:doctorate:update:curriculum:non_educational_duplicate',
            uuid=self.doctorate_admission.uuid,
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

    def test_duplicate_experience_from_doctorate_curriculum_is_allowed_for_fac_users(self):
        self.client.force_login(self.doctorate_program_manager_user)

        other_admission = DoctorateAdmissionFactory(
            training=self.doctorate_admission.training,
            candidate=self.doctorate_admission.candidate,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        response = self.client.post(
            resolve_url(
                'admission:doctorate:update:curriculum:non_educational_duplicate',
                uuid=other_admission.uuid,
                experience_uuid=self.experience.uuid,
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_duplicate_experience_from_doctorate_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)

        admission_url = resolve_url('admission')
        expected_url = f'{admission_url}#custom_hash'

        response = self.client.post(f'{self.duplicate_url}?next={admission_url}&next_hash_url=custom_hash')
        self.assertRedirects(
            response=response,
            fetch_redirect_response=False,
            expected_url=expected_url,
        )
