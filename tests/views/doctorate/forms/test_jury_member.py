# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_302_FOUND

from admission.contrib.models import JuryMember
from admission.ddd.parcours_doctoral.jury.domain.model.enums import TitreMembre, GenreMembre, RoleJury
from admission.forms.doctorate.jury.membre import JuryMembreForm
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.jury import JuryMemberFactory
from admission.tests.factories.supervision import PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from reference.tests.factories.country import CountryFactory


class DoctorateAdmissionJuryMemberUpdateFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create admissions
        cls.admission = DoctorateAdmissionFactory(
            training__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=promoter.process,
            submitted_at=datetime.datetime.now(),
            passed_confirmation=True,
        )

        # Create member
        cls.membre = JuryMemberFactory(doctorate=cls.admission)
        cls.country = CountryFactory()

        # User with one cdd
        cls.manager = ProgramManagerFactory(education_group=cls.admission.training.education_group).person.user
        cls.read_path = 'admission:doctorate:jury'
        cls.update_path = 'admission:doctorate:update:jury-member:update'

    def setUp(self):
        self.client.force_login(user=self.manager)

    def test_get_jury_membre_detail_cdd_user_with_unknown_doctorate(self):
        url = reverse(self.update_path, args=[uuid.uuid4(), uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_jury_membre_detail_cdd_user_with_unknown_member(self):
        url = reverse(self.update_path, args=[self.admission.uuid, uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_jury_membre_detail_cdd_user(self):
        url = reverse(self.update_path, args=[self.admission.uuid, self.membre.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(
            response.context.get('doctorate').uuid,
            str(self.admission.uuid),
        )
        self.assertEqual(
            response.context.get('membre').uuid,
            str(self.membre.uuid),
        )
        self.assertEqual(
            response.context['form'].initial,
            {
                'matricule': '',
                'institution_principale': JuryMembreForm.InstitutionPrincipaleChoices.OTHER.name,
                'institution': self.membre.institute,
                'autre_institution': self.membre.other_institute,
                'pays': self.membre.country,
                'nom': self.membre.last_name,
                'prenom': self.membre.first_name,
                'titre': self.membre.title,
                'justification_non_docteur': self.membre.non_doctor_reason,
                'genre': self.membre.gender,
                'email': self.membre.email,
            },
        )

    def test_post_jury_membre_detail_cdd_user(self):
        url = reverse(self.update_path, args=[self.admission.uuid, self.membre.uuid])

        response = self.client.post(
            url,
            data={
                'matricule': '',
                'institution_principale': JuryMembreForm.InstitutionPrincipaleChoices.OTHER.name,
                'institution': 'nouvelle institution',
                'autre_institution': 'autre institution',
                'pays': self.country.pk,
                'nom': 'nouveau nom',
                'prenom': 'nouveau prenom',
                'titre': TitreMembre.DOCTEUR.name,
                'justification_non_docteur': '',
                'genre': GenreMembre.AUTRE.name,
                'email': 'nouvel_email@example.org',
            },
        )

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.admission.uuid))

        updated_member = JuryMember.objects.get(
            uuid=self.membre.uuid,
        )
        self.assertEqual(updated_member.person, None)
        self.assertEqual(updated_member.institute, 'nouvelle institution')
        self.assertEqual(updated_member.other_institute, 'autre institution')
        self.assertEqual(updated_member.country, self.country)
        self.assertEqual(updated_member.last_name, 'nouveau nom')
        self.assertEqual(updated_member.first_name, 'nouveau prenom')
        self.assertEqual(updated_member.title, TitreMembre.DOCTEUR.name)
        self.assertEqual(updated_member.non_doctor_reason, '')
        self.assertEqual(updated_member.gender, GenreMembre.AUTRE.name)
        self.assertEqual(updated_member.email, 'nouvel_email@example.org')


class DoctorateAdmissionJuryMemberDeleteFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create admissions
        cls.admission = DoctorateAdmissionFactory(
            training__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=promoter.process,
            submitted_at=datetime.datetime.now(),
            passed_confirmation=True,
        )

        # Create member
        cls.membre = JuryMemberFactory(doctorate=cls.admission)
        cls.country = CountryFactory()

        # User with one cdd
        cls.manager = ProgramManagerFactory(education_group=cls.admission.training.education_group).person.user
        cls.read_path = 'admission:doctorate:jury'
        cls.remove_path = 'admission:doctorate:update:jury-member:remove'

    def setUp(self):
        self.client.force_login(user=self.manager)

    def test_post_jury_membre_remove_cdd_user_with_unknown_doctorate(self):
        url = reverse(self.remove_path, args=[uuid.uuid4(), uuid.uuid4()])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_jury_membre_remove_cdd_user_with_unknown_member(self):
        url = reverse(self.remove_path, args=[self.admission.uuid, uuid.uuid4()])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_302_FOUND)

    def test_post_jury_membre_remove_cdd_user(self):
        url = reverse(self.remove_path, args=[self.admission.uuid, self.membre.uuid])

        response = self.client.post(url)

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.admission.uuid))

        with self.assertRaises(JuryMember.DoesNotExist):
            JuryMember.objects.get(
                uuid=self.membre.uuid,
            )


class DoctorateAdmissionJuryMemberChangeRoleFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create admissions
        cls.admission = DoctorateAdmissionFactory(
            training__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=promoter.process,
            submitted_at=datetime.datetime.now(),
            passed_confirmation=True,
        )

        # Create member
        cls.membre = JuryMemberFactory(doctorate=cls.admission)
        cls.country = CountryFactory()

        # User with one cdd
        cls.manager = ProgramManagerFactory(education_group=cls.admission.training.education_group).person.user
        cls.read_path = 'admission:doctorate:jury'
        cls.update_path = 'admission:doctorate:update:jury-member:change-role'

    def setUp(self):
        self.client.force_login(user=self.manager)

    def test_post_jury_membre_change_role_cdd_user_with_unknown_doctorate(self):
        url = reverse(self.update_path, args=[uuid.uuid4(), uuid.uuid4()])

        response = self.client.post(
            url,
            data={
                'role': RoleJury.PRESIDENT.name,
            },
        )

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_jury_membre_change_role_cdd_user_with_unknown_member(self):
        url = reverse(self.update_path, args=[self.admission.uuid, uuid.uuid4()])

        response = self.client.post(
            url,
            data={
                'role': RoleJury.PRESIDENT.name,
            },
        )

        self.assertEqual(response.status_code, HTTP_302_FOUND)

    def test_post_jury_membre_change_role_cdd_user(self):
        url = reverse(self.update_path, args=[self.admission.uuid, self.membre.uuid])

        response = self.client.post(
            url,
            data={
                'role': RoleJury.PRESIDENT.name,
            },
        )

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.admission.uuid))

        updated_member = JuryMember.objects.get(
            uuid=self.membre.uuid,
        )
        self.assertEqual(updated_member.role, RoleJury.PRESIDENT.name)
