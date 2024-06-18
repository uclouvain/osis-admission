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

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from admission.contrib.models import ContinuingEducationAdmission, DoctorateAdmission, GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import (
    CentralManagerRoleFactory,
    SicManagementRoleFactory,
    ProgramManagerRoleFactory,
)
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from reference.tests.factories.country import CountryFactory


class PersonDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')

        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(
            entity=first_doctoral_commission,
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user

        cls.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_FR,
        )

        cls.continuing_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.continuing_admission.training.education_group,
        ).person.user

        cls.continuing_url = resolve_url(
            'admission:continuing-education:person',
            uuid=cls.continuing_admission.uuid,
        )

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
        )

        cls.general_url = resolve_url(
            'admission:general-education:person',
            uuid=cls.general_admission.uuid,
        )

        cls.general_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user

        cls.confirmed_general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=cls.general_admission.training,
            candidate=cls.general_admission.candidate,
            admitted=True,
        )

        cls.confirmed_general_url = resolve_url(
            'admission:general-education:person',
            uuid=cls.confirmed_general_admission.uuid,
        )

        cls.central_manager = CentralManagerRoleFactory(entity=first_doctoral_commission)
        cls.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_FR,
        )

        cls.doctorate_url = resolve_url('admission:doctorate:person', uuid=cls.doctorate_admission.uuid)

        cls.confirmed_doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=cls.doctorate_admission.training,
            candidate=cls.doctorate_admission.candidate,
            admitted=True,
        )

        cls.confirmed_doctorate_url = resolve_url(
            'admission:doctorate:person',
            uuid=cls.confirmed_doctorate_admission.uuid,
        )

    def test_continuing_person_detail_program_manager(self):
        self.client.force_login(user=self.continuing_program_manager_user)

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)

    def test_continuing_person_detail_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.continuing_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.continuing_admission.uuid)
        self.assertEqual(response.context['person'], self.continuing_admission.candidate)
        self.assertEqual(response.context['contact_language'], _('French'))

    def test_general_person_detail_program_manager(self):
        self.client.force_login(user=self.general_program_manager_user)

        response = self.client.get(self.general_url)

        self.assertEqual(response.status_code, 200)

    def test_general_person_detail_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(self.general_url)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)
        self.assertEqual(response.context['person'], self.general_admission.candidate)
        self.assertEqual(response.context['contact_language'], _('English'))
        self.assertIsNone(response.context['profil_candidat'])

        response = self.client.get(self.confirmed_general_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context.get('profil_candidat'),
            ProfilCandidatDTO(
                nom='Doe',
                prenom='John',
                genre='H',
                nationalite='BE',
                nom_pays_nationalite='Belgique',
                pays='BE',
                nom_pays='Belgique',
                code_postal='1348',
                ville='Louvain-La-Neuve',
                rue="Place de l'Université",
                numero_rue='2',
                boite_postale='',
            ),
        )

    def test_doctoral_person_detail_cdd_manager_user(self):
        self.client.force_login(user=self.central_manager.person.user)

        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.doctorate_admission.uuid)
        self.assertEqual(response.context['person'], self.doctorate_admission.candidate)

    def test_doctoral_person_detail_sic_manager(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.doctorate_admission.uuid)
        self.assertEqual(response.context['person'], self.doctorate_admission.candidate)
        self.assertEqual(response.context['contact_language'], _('French'))
        self.assertIsNone(response.context.get('profil_candidat'))

        response = self.client.get(self.confirmed_doctorate_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context.get('profil_candidat'),
            ProfilCandidatDTO(
                nom='Doe',
                prenom='John',
                genre='H',
                nationalite='BE',
                nom_pays_nationalite='Belgique',
                pays='BE',
                nom_pays='Belgique',
                code_postal='1348',
                ville='Louvain-la-Neuve',
                rue="Place de l'Université",
                numero_rue='2',
                boite_postale='',
            ),
        )

    def test_permissions_with_several_permissions(self):
        # The candidate has a program manager role from admission
        admission_program_manager = ProgramManagerRoleFactory(
            education_group=self.general_admission.training.education_group
        )

        user = admission_program_manager.person.user

        self.client.force_login(user=user)

        response = self.client.get(self.confirmed_general_url)

        self.assertEqual(response.status_code, 200)

        # The candidate has a program manager role from admission and another one from base from different groups
        base_program_manager = ProgramManagerFactory(
            person=admission_program_manager.person,
            education_group=self.continuing_admission.training.education_group,
        )

        response = self.client.get(self.confirmed_general_url)

        self.assertEqual(response.status_code, 200)
