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

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.models import EPCInjection as AdmissionEPCInjection, DoctorateAdmission
from admission.models.base import (
    AdmissionProfessionalValuatedExperiences,
)
from admission.models.epc_injection import EPCInjectionType, EPCInjectionStatus as AdmissionEPCInjectionStatus
from admission.models.general_education import GeneralEducationAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import (
    ProfessionalExperienceFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from osis_profile.models import ProfessionalExperience
from osis_profile.models.enums.curriculum import ActivityType, ActivitySector
from osis_profile.models.epc_injection import (
    EPCInjection as CurriculumEPCInjection,
    ExperienceType,
    EPCInjectionStatus as CurriculumEPCInjectionStatus,
)
from reference.tests.factories.country import CountryFactory


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

        # Targeted urls
        self.delete_url = resolve_url(
            'admission:general-education:update:curriculum:non_educational_delete',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )
        self.doctorate_delete_url = resolve_url(
            'admission:doctorate:update:curriculum:non_educational_delete',
            uuid=self.doctorate_admission.uuid,
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

    def test_delete_experience_from_curriculum_is_not_allowed_for_injected_experiences(self):
        self.client.force_login(self.sic_manager_user)

        # The experience come from EPC
        self.experience.external_id = 'EPC1'
        self.experience.save(update_fields=['external_id'])

        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Reset the experience
        self.experience.external_id = ''
        self.experience.save(update_fields=['external_id'])

        # The experience has been injected from the curriculum
        cv_injection = CurriculumEPCInjection.objects.create(
            person=self.general_admission.candidate,
            type_experience=ExperienceType.PROFESSIONAL.name,
            experience_uuid=self.experience.uuid,
            status=CurriculumEPCInjectionStatus.OK.name,
        )

        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        cv_injection.delete()

        # The experience has been injected from another admission
        other_admission = GeneralEducationAdmissionFactory(candidate=self.general_admission.candidate)

        other_admission_injection = AdmissionEPCInjection.objects.create(
            admission=other_admission,
            type=EPCInjectionType.DEMANDE.name,
            status=AdmissionEPCInjectionStatus.OK.name,
        )

        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        other_valuation = AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=other_admission,
            professionalexperience=self.experience,
        )

        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        other_admission.delete()
        other_valuation.delete()

        # The current admission has been injected
        admission_injection = AdmissionEPCInjection.objects.create(
            admission=self.general_admission,
            type=EPCInjectionType.DEMANDE.name,
            status=AdmissionEPCInjectionStatus.OK.name,
        )

        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

        response = self.client.post(self.delete_url)

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
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertNotIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            self.general_admission.requested_documents,
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_delete_experience_from_doctorate_curriculum_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.doctorate_program_manager_user)
        other_admission = DoctorateAdmissionFactory(
            training=self.doctorate_admission.training,
            candidate=self.doctorate_admission.candidate,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        response = self.client.post(
            resolve_url(
                'admission:doctorate:update:curriculum:non_educational_delete',
                uuid=other_admission.uuid,
                experience_uuid=self.experience.uuid,
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_experience_from_doctorate_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)

        admission_url = resolve_url('admission')
        expected_url = f'{admission_url}#custom_hash'

        response = self.client.delete(f'{self.doctorate_delete_url}?next={admission_url}&next_hash_url=custom_hash')

        self.assertRedirects(
            response=response,
            fetch_redirect_response=False,
            expected_url=expected_url,
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
