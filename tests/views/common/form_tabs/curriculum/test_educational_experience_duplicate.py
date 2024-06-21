# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
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

from admission.contrib.models.base import AdmissionEducationalValuatedExperiences
from admission.contrib.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.models.enums.community import CommunityEnum
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.enums.teaching_type import TeachingTypeEnum
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from osis_profile.models import EducationalExperience, EducationalExperienceYear
from osis_profile.models.enums.curriculum import TranscriptType, Result, EvaluationSystem, Reduction, Grade
from reference.models.enums.cycle import Cycle
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.diploma_title import DiplomaTitleFactory
from reference.tests.factories.language import LanguageFactory


@freezegun.freeze_time('2022-01-01')
class CurriculumEducationalExperienceDuplicateViewTestCase(TestCase):
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
        cls.be_country = CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')
        cls.fr_country = CountryFactory(iso_code='FR', name='France', name_en='France')

        cls.first_cycle_diploma = DiplomaTitleFactory(
            cycle=Cycle.FIRST_CYCLE.name,
        )
        cls.second_cycle_diploma = DiplomaTitleFactory(
            cycle=Cycle.SECOND_CYCLE.name,
        )
        cls.first_institute = OrganizationFactory(
            community=CommunityEnum.FRENCH_SPEAKING.name,
            establishment_type=EstablishmentTypeEnum.UNIVERSITY.name,
        )
        cls.second_institute = OrganizationFactory(
            community=CommunityEnum.FRENCH_SPEAKING.name,
            establishment_type=EstablishmentTypeEnum.NON_UNIVERSITY_HIGHER.name,
        )
        cls.french = LanguageFactory(code='FR')

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user

        cls.files_uuids = [uuid.uuid4() for _ in range(9)]
        cls.files_uuids_str = [str(current_uuid) for current_uuid in cls.files_uuids]
        cls.duplicate_files_uuids = [uuid.uuid4() for _ in cls.files_uuids]
        cls.duplicate_files_uuids_str = [str(current_uuid) for current_uuid in cls.duplicate_files_uuids]

    def setUp(self):
        # Create data
        self.experience: EducationalExperience = EducationalExperienceFactory(
            external_id='custom_id_1',
            person=self.general_admission.candidate,
            institute_name='University of Louvain',
            country=self.be_country,
            institute=self.first_institute,
            institute_address='Rue de Louvain, 1000 Bruxelles',
            program=self.first_cycle_diploma,
            fwb_equivalent_program=self.second_cycle_diploma,
            education_name='Computer science',
            study_system=TeachingTypeEnum.SOCIAL_PROMOTION.name,
            evaluation_type=EvaluationSystem.ECTS_CREDITS.name,
            linguistic_regime=self.french,
            transcript_type=TranscriptType.ONE_A_YEAR.name,
            obtained_diploma=True,
            obtained_grade=Grade.GREAT_DISTINCTION.name,
            graduate_degree=[self.files_uuids[0]],
            graduate_degree_translation=[self.files_uuids[1]],
            transcript=[self.files_uuids[2]],
            transcript_translation=[self.files_uuids[3]],
            rank_in_diploma='10',
            expected_graduation_date=datetime.date(2024, 1, 1),
            dissertation_title='Dissertations',
            dissertation_score='15',
            dissertation_summary=[self.files_uuids[4]],
        )
        self.first_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            external_id='custom_id_11',
            educational_experience=self.experience,
            academic_year=self.academic_years[0],
            registered_credit_number=21,
            acquired_credit_number=20,
            result=Result.SUCCESS.name,
            transcript=[self.files_uuids[5]],
            transcript_translation=[self.files_uuids[7]],
            with_block_1=True,
            with_complement=True,
            fwb_registered_credit_number=11,
            fwb_acquired_credit_number=10,
            reduction=Reduction.A150.name,
            is_102_change_of_course=True,
        )
        self.second_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            external_id='custom_id_12',
            educational_experience=self.experience,
            academic_year=self.academic_years[1],
            registered_credit_number=31,
            acquired_credit_number=30,
            result=Result.SUCCESS.name,
            transcript=[self.files_uuids[6]],
            transcript_translation=[self.files_uuids[8]],
            with_block_1=False,
            with_complement=False,
            fwb_registered_credit_number=13,
            fwb_acquired_credit_number=12,
            reduction=Reduction.A151.name,
            is_102_change_of_course=False,
        )
        # Targeted url
        self.duplicate_url = resolve_url(
            'admission:general-education:update:curriculum:educational_duplicate',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )

        # Mock osis document api
        self.get_several_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        self.get_several_remote_metadata_patched = self.get_several_remote_metadata_patcher.start()
        self.get_several_remote_metadata_patched.return_value = {
            f'token{index}': {
                'name': f'the_file_{index}.pdf',
                'size': 1,
            }
            for index in range(len(self.files_uuids))
        }
        self.addCleanup(self.get_several_remote_metadata_patcher.stop)

        self.get_remote_tokens_patcher = mock.patch('osis_document.api.utils.get_remote_tokens')
        self.get_remote_tokens_patched = self.get_remote_tokens_patcher.start()
        self.get_remote_tokens_patched.return_value = {
            self.files_uuids_str[index]: f'token{index}' for index in range(len(self.files_uuids))
        }
        self.addCleanup(self.get_remote_tokens_patcher.stop)

        self.documents_remote_duplicate_patcher = mock.patch('osis_document.api.utils.documents_remote_duplicate')
        self.documents_remote_duplicate_patched = self.documents_remote_duplicate_patcher.start()
        self.documents_remote_duplicate_patched.return_value = {
            self.files_uuids_str[index]: self.duplicate_files_uuids_str[index] for index in range(len(self.files_uuids))
        }
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
                'admission:general-education:update:curriculum:educational_duplicate',
                uuid=self.general_admission.uuid,
                experience_uuid=uuid.uuid4(),
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @freezegun.freeze_time('2022-02-02')
    def test_duplicate_known_but_not_valuated_experience(self):
        self.client.force_login(self.sic_manager_user)

        educational_experiences = EducationalExperience.objects.filter(person=self.general_admission.candidate)

        self.assertEqual(educational_experiences.count(), 1)

        base_original_experience = educational_experiences.first()
        base_original_years = base_original_experience.educationalexperienceyear_set.all().order_by(
            'academic_year__year'
        )

        response = self.client.post(self.duplicate_url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check the data of the duplicated experience
        educational_experiences = EducationalExperience.objects.filter(person=self.general_admission.candidate)

        self.assertEqual(educational_experiences.count(), 2)

        if educational_experiences[0].uuid == base_original_experience.uuid:
            original_experience, duplicated_experience = educational_experiences
        else:
            duplicated_experience, original_experience = educational_experiences

        fields_to_duplicate = [
            'person',
            'institute_name',
            'country',
            'institute',
            'institute_address',
            'program',
            'fwb_equivalent_program',
            'education_name',
            'study_system',
            'evaluation_type',
            'linguistic_regime',
            'transcript_type',
            'obtained_diploma',
            'obtained_grade',
            'rank_in_diploma',
            'expected_graduation_date',
            'dissertation_title',
            'dissertation_score',
        ]

        fields_to_update = [
            'external_id',
            'graduate_degree',
            'graduate_degree_translation',
            'transcript',
            'transcript_translation',
            'dissertation_summary',
        ]

        fields_years_to_duplicate = [
            'academic_year',
            'registered_credit_number',
            'acquired_credit_number',
            'result',
            'with_block_1',
            'with_complement',
            'fwb_registered_credit_number',
            'fwb_acquired_credit_number',
            'reduction',
            'is_102_change_of_course',
        ]

        fields_years_to_update = [
            'external_id',
            'educational_experience',
            'transcript',
            'transcript_translation',
        ]

        # Check that the original experience has not been updated

        # Main object
        for field in itertools.chain(fields_to_duplicate, fields_to_update):
            self.assertEqual(
                getattr(base_original_experience, field),
                getattr(original_experience, field),
                f'"{field}" must not be updated',
            )

        # Sub objects (years)
        original_years = original_experience.educationalexperienceyear_set.all().order_by('academic_year__year')

        for index in range(len(original_years)):
            base_experience_year = base_original_years[index]
            original_experience_year = original_years[index]
            for field in itertools.chain(fields_years_to_duplicate, fields_years_to_update):
                self.assertEqual(getattr(base_experience_year, field), getattr(original_experience_year, field))

        # Check that the duplicated experience is a valid copy of the original

        # Main object
        for field in fields_to_duplicate:
            self.assertEqual(getattr(duplicated_experience, field), getattr(original_experience, field))

        for field in fields_to_update:
            self.assertNotEqual(getattr(duplicated_experience, field), getattr(original_experience, field))

        self.assertEqual(duplicated_experience.external_id, None)
        self.assertEqual(duplicated_experience.graduate_degree, [self.duplicate_files_uuids[0]])
        self.assertEqual(duplicated_experience.graduate_degree_translation, [self.duplicate_files_uuids[1]])
        self.assertEqual(duplicated_experience.transcript, [self.duplicate_files_uuids[2]])
        self.assertEqual(duplicated_experience.transcript_translation, [self.duplicate_files_uuids[3]])
        self.assertEqual(duplicated_experience.dissertation_summary, [self.duplicate_files_uuids[4]])

        # Sub objects (years)
        duplicated_years = duplicated_experience.educationalexperienceyear_set.all().order_by('academic_year__year')

        for index in range(len(original_years)):
            original_experience_year = original_years[index]
            duplicated_experience_year = duplicated_years[index]
            for field in fields_years_to_duplicate:
                self.assertEqual(getattr(duplicated_experience_year, field), getattr(original_experience_year, field))

            for field in fields_years_to_update:
                self.assertNotEqual(
                    getattr(duplicated_experience_year, field),
                    getattr(original_experience_year, field),
                )

            self.assertEqual(duplicated_experience_year.external_id, None)
            self.assertEqual(duplicated_experience_year.educational_experience, duplicated_experience)
            self.assertEqual(duplicated_experience_year.transcript, [self.duplicate_files_uuids[5 + index]])
            self.assertEqual(duplicated_experience_year.transcript_translation, [self.duplicate_files_uuids[7 + index]])

        self.documents_remote_duplicate_patched.assert_called_once()

        call_args = self.documents_remote_duplicate_patched.call_args[1]

        self.assertCountEqual(call_args.get('uuids'), self.files_uuids)
        self.assertEqual(call_args.get('with_modified_upload'), True)
        self.assertEqual(
            call_args.get('upload_path_by_uuid'),
            {
                self.files_uuids_str[index]: f'{self.general_admission.candidate.uuid}/curriculum/the_file_{index}.pdf'
                for index in range(len(self.files_uuids_str))
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

        educational_experiences = EducationalExperience.objects.filter(person=self.general_admission.candidate)

        self.assertEqual(educational_experiences.count(), 1)

        experience = educational_experiences.first()

        valuations = [
            AdmissionEducationalValuatedExperiences.objects.create(
                baseadmission_id=admission.uuid,
                educationalexperience_id=self.experience.uuid,
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
        educational_experiences = EducationalExperience.objects.filter(person=self.general_admission.candidate)

        self.assertEqual(educational_experiences.count(), 2)

        if educational_experiences[0].uuid == experience.uuid:
            original_experience, duplicated_experience = educational_experiences
        else:
            duplicated_experience, original_experience = educational_experiences

        default_checklist = Checklist.initialiser_checklist_experience(
            experience_uuid=str(duplicated_experience.uuid),
        ).to_dict()

        duplicated_valuations = AdmissionEducationalValuatedExperiences.objects.filter(
            educationalexperience_id=duplicated_experience.uuid,
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
