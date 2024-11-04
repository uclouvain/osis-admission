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
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from admission.models import JuryMember
from admission.ddd.parcours_doctoral.jury.domain.model.enums import TitreMembre, GenreMembre, RoleJury
from admission.forms.doctorate.jury.membre import JuryMembreForm
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.jury import JuryMemberFactory
from admission.tests.factories.supervision import PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from reference.tests.factories.country import CountryFactory


class DoctorateAdmissionJuryPreparationDetailViewTestCase(TestCase):
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

        # User with one cdd
        cls.manager = ProgramManagerFactory(education_group=cls.admission.training.education_group).person.user
        cls.detail_path = 'admission:doctorate:jury-preparation'

    def setUp(self):
        self.client.force_login(user=self.manager)

    def test_get_jury_preparation_detail_cdd_user_with_unknown_doctorate(self):
        url = reverse(self.detail_path, args=[uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_jury_preparation_detail_cdd_user(self):
        url = reverse(self.detail_path, args=[self.admission.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(
            response.context.get('doctorate').uuid,
            str(self.admission.uuid),
        )


class DoctorateAdmissionJuryViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create admission
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
        cls.path = 'admission:doctorate:jury'

    def setUp(self):
        self.client.force_login(user=self.manager)

    def test_get_jury_detail_cdd_user_with_unknown_doctorate(self):
        url = reverse(self.path, args=[uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_jury_detail_cdd_user(self):
        url = reverse(self.path, args=[self.admission.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(
            response.context.get('doctorate').uuid,
            str(self.admission.uuid),
        )
        self.assertEqual(
            response.context.get('membres')[0].uuid,
            str(self.membre.uuid),
        )

    def test_post_jury_membre_cdd_user(self):
        url = reverse(self.path, args=[self.admission.uuid])

        response = self.client.post(
            url,
            data={
                'institution': 'Nouveau membre',
                'matricule': '',
                'institution_principale': JuryMembreForm.InstitutionPrincipaleChoices.UCL.name,
                'autre_institution': 'autre institution',
                'pays': self.country.id,
                'nom': 'nom',
                'prenom': 'prenom',
                'titre': TitreMembre.DOCTEUR.name,
                'justification_non_docteur': '',
                'genre': GenreMembre.AUTRE.name,
                'email': 'email@example.org',
            },
        )

        self.assertRedirects(response, resolve_url(self.path, uuid=self.admission.uuid))

        new_member = JuryMember.objects.get(
            institute='Nouveau membre',
        )
        self.assertEqual(new_member.institute, 'Nouveau membre')
        self.assertEqual(new_member.role, RoleJury.MEMBRE.name)
        self.assertEqual(new_member.doctorate, self.admission)
        self.assertEqual(new_member.other_institute, 'autre institution')
        self.assertEqual(new_member.promoter, None)
        self.assertEqual(new_member.person, None)
        self.assertEqual(new_member.country, self.country)
        self.assertEqual(new_member.last_name, 'nom')
        self.assertEqual(new_member.first_name, 'prenom')
        self.assertEqual(new_member.title, TitreMembre.DOCTEUR.name)
        self.assertEqual(new_member.non_doctor_reason, '')
        self.assertEqual(new_member.gender, GenreMembre.AUTRE.name)
        self.assertEqual(new_member.email, 'email@example.org')
