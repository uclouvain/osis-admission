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
import uuid

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import (
    Checklist,
)
from admission.models import ContinuingEducationAdmission, DoctorateAdmission
from admission.models.base import AdmissionEducationalValuatedExperiences
from admission.models.general_education import GeneralEducationAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
)
from admission.tests.factories.curriculum import EducationalExperienceFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from osis_profile.models import EducationalExperience


@freezegun.freeze_time('2022-01-01')
class CurriculumEducationalExperienceValuateViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        entity = EntityWithVersionFactory()

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        cls.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=entity,
            training__academic_year=cls.academic_years[0],
            candidate=cls.general_admission.candidate,
            submitted=True,
        )

        cls.other_continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=entity,
            training__academic_year=cls.academic_years[0],
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=entity).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user
        cls.doctorate_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.doctorate_admission.training.education_group,
        ).person.user
        cls.other_continuing_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.other_continuing_admission.training.education_group,
        ).person.user

    def setUp(self):
        # Create data
        self.experience: EducationalExperience = EducationalExperienceFactory(
            person=self.general_admission.candidate,
        )

        # Targeted url
        self.valuate_url = resolve_url(
            'admission:general-education:update:curriculum:educational_valuate',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )
        self.doctorate_valuate_url = resolve_url(
            'admission:doctorate:update:curriculum:educational_valuate',
            uuid=self.doctorate_admission.uuid,
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
                'admission:general-education:update:curriculum:educational_valuate',
                uuid=self.general_admission.uuid,
                experience_uuid=uuid.uuid4(),
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_valuate_known_experience(self):
        self.client.force_login(self.sic_manager_user)

        default_experience_checklist = Checklist.initialiser_checklist_experience(str(self.experience.uuid)).to_dict()

        response = self.client.post(self.valuate_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check that the experience has been valuated
        valuation = AdmissionEducationalValuatedExperiences.objects.filter(
            educationalexperience_id=self.experience.uuid,
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
        valuation = AdmissionEducationalValuatedExperiences.objects.filter(
            educationalexperience_id=self.experience.uuid,
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

    def test_valuate_experience_from_doctorate_curriculum_is_allowed_for_fac_users(self):
        self.client.force_login(self.doctorate_program_manager_user)

        other_admission = DoctorateAdmissionFactory(
            training=self.doctorate_admission.training,
            candidate=self.doctorate_admission.candidate,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        response = self.client.post(
            resolve_url(
                'admission:doctorate:update:curriculum:educational_valuate',
                uuid=other_admission.uuid,
                experience_uuid=self.experience.uuid,
            )
            + '?next='
            + resolve_url('admission'),
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_valuate_experience_from_doctorate_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)

        admission_url = resolve_url('admission')
        expected_url = f'{admission_url}#custom_hash'

        response = self.client.post(f'{self.doctorate_valuate_url}?next={admission_url}&next_hash_url=custom_hash')

        self.assertRedirects(response=response, fetch_redirect_response=False, expected_url=expected_url)

    def test_valuate_experience_from_continuing_curriculum_for_fac_users(self):
        self.client.force_login(self.other_continuing_program_manager_user)

        experience = EducationalExperienceFactory(
            person=self.other_continuing_admission.candidate,
        )

        url = resolve_url(
            'admission:continuing-education:update:curriculum:educational_valuate',
            uuid=self.other_continuing_admission.uuid,
            experience_uuid=experience.uuid,
        )

        doctorate_admission = DoctorateAdmissionFactory(
            candidate=experience.person,
            submitted=True,
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        doctorate_admission.delete()

        general_admission = GeneralEducationAdmissionFactory(
            candidate=experience.person,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        general_admission.delete()

        response = self.client.post(url)

        base_curriculum_url = resolve_url(
            'admission:continuing-education:checklist',
            uuid=self.other_continuing_admission.uuid,
        )

        self.assertRedirects(
            response=response,
            fetch_redirect_response=False,
            expected_url=base_curriculum_url,
        )

    def test_valuate_experience_from_continuing_curriculum_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)

        experience = EducationalExperienceFactory(
            person=self.other_continuing_admission.candidate,
        )

        url = resolve_url(
            'admission:continuing-education:update:curriculum:educational_valuate',
            uuid=self.other_continuing_admission.uuid,
            experience_uuid=experience.uuid,
        )

        doctorate_admission = DoctorateAdmissionFactory(
            candidate=experience.person,
            submitted=True,
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        doctorate_admission.delete()

        general_admission = GeneralEducationAdmissionFactory(
            candidate=experience.person,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        general_admission.delete()

        response = self.client.post(url)

        base_curriculum_url = resolve_url(
            'admission:continuing-education:checklist',
            uuid=self.other_continuing_admission.uuid,
        )

        self.assertRedirects(
            response=response,
            fetch_redirect_response=False,
            expected_url=base_curriculum_url,
        )
