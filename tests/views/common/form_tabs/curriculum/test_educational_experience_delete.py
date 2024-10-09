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
from unittest import mock

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext
from rest_framework import status

from admission.contrib.models import EPCInjection as AdmissionEPCInjection, DoctorateAdmission
from admission.contrib.models.base import AdmissionEducationalValuatedExperiences
from admission.contrib.models.epc_injection import EPCInjectionType, EPCInjectionStatus as AdmissionEPCInjectionStatus
from admission.contrib.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
    AdmissionEducationalValuatedExperiencesFactory,
)
from admission.tests.factories.faculty_decision import FreeAdditionalApprovalConditionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.community import CommunityEnum
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from osis_profile.models import EducationalExperience, EducationalExperienceYear
from osis_profile.models.enums.curriculum import Reduction
from osis_profile.models.epc_injection import (
    EPCInjection as CurriculumEPCInjection,
    ExperienceType,
    EPCInjectionStatus as CurriculumEPCInjectionStatus,
)
from reference.models.enums.cycle import Cycle
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.diploma_title import DiplomaTitleFactory
from reference.tests.factories.language import LanguageFactory


@freezegun.freeze_time('2022-01-01')
class CurriculumEducationalExperienceDeleteViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        cls.be_country = CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)
        cls.french = LanguageFactory(code='FR')

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

    def setUp(self):
        # Create data
        self.experience: EducationalExperience = EducationalExperienceFactory(
            person=self.general_admission.candidate,
            country=self.be_country,
            program=self.first_cycle_diploma,
            fwb_equivalent_program=self.first_cycle_diploma,
            institute=self.first_institute,
            linguistic_regime=self.french,
            education_name='Computer science',
            institute_name='University of Louvain',
            institute_address='Rue de Louvain, 1000 Bruxelles',
            expected_graduation_date=datetime.date(2024, 1, 1),
        )
        self.first_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=self.experience,
            academic_year=self.academic_years[0],
            with_block_1=True,
            reduction='',
            is_102_change_of_course=True,
        )
        self.second_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=self.experience,
            academic_year=self.academic_years[2],
            with_complement=True,
            reduction=Reduction.A150.name,
        )
        # Targeted urls
        self.delete_url = resolve_url(
            'admission:general-education:update:curriculum:educational_delete',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )
        self.doctorate_delete_url = resolve_url(
            'admission:doctorate:update:curriculum:educational_delete',
            uuid=self.doctorate_admission.uuid,
            experience_uuid=self.experience.uuid,
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
        self.addCleanup(patcher.stop)

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

        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

        other_valuation = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=other_admission,
            educationalexperience=self.experience,
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
                'admission:general-education:update:curriculum:educational_delete',
                uuid=self.general_admission.uuid,
                experience_uuid=uuid.uuid4(),
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_experience_used_as_approval_condition_is_not_allowed(self):
        self.client.force_login(self.sic_manager_user)

        approval_condition = FreeAdditionalApprovalConditionFactory(
            admission=self.general_admission,
            related_experience=self.experience,
            name_fr='Condition de test',
            name_en='Test condition',
        )

        response = self.client.delete(self.delete_url, follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        messages = [m.message for m in response.context['messages']]
        self.assertIn(
            gettext(
                'Cannot delete the experience because it is used as additional condition for the '
                'proposition {admission}.'.format(admission=approval_condition.admission)
            ),
            messages,
        )

    def test_delete_known_experience(self):
        self.client.force_login(self.sic_manager_user)

        # Simulate a valuated experience
        AdmissionEducationalValuatedExperiences.objects.create(
            baseadmission_id=self.general_admission.uuid,
            educationalexperience_id=self.experience.uuid,
        )

        self.general_admission.checklist['current']['parcours_anterieur']['enfants'] = [
            Checklist.initialiser_checklist_experience(experience_uuid=self.experience.uuid).to_dict()
        ]

        self.general_admission.save()

        response = self.client.delete(self.delete_url)

        self.assertFalse(EducationalExperience.objects.filter(uuid=self.experience.uuid).exists())

        self.assertFalse(
            EducationalExperienceYear.objects.filter(
                educational_experience__uuid=self.experience.uuid,
            ).exists()
        )

        self.assertFalse(
            AdmissionEducationalValuatedExperiences.objects.filter(
                educationalexperience_id=self.experience.uuid
            ).exists()
        )

        self.general_admission.refresh_from_db()

        self.assertEqual(
            self.general_admission.checklist['current']['parcours_anterieur']['enfants'],
            [],
        )

        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())
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
                'admission:doctorate:update:curriculum:educational_delete',
                uuid=other_admission.uuid,
                experience_uuid=self.experience.uuid,
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_experience_from_doctorate_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.delete(self.doctorate_delete_url)

        self.assertRedirects(
            response=response,
            fetch_redirect_response=False,
            expected_url=resolve_url('admission:doctorate:curriculum', uuid=self.doctorate_admission.uuid),
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
