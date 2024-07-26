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
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.models import DoctorateAdmission, JuryMember
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.jury import JuryMemberFactory
from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.person import PersonFactory
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import FrenchLanguageFactory


class JuryApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        doctoral_commission = EntityFactory()
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=doctoral_commission,
            passed_confirmation=True,
        )
        cls.updated_data = {
            'titre_propose': 'titre api',
            'formule_defense': 'DEUX_TEMPS',
            'date_indicative': '2023-12-25',
            'langue_redaction': FrenchLanguageFactory().pk,
            'langue_soutenance': 'FRENCH',
            'commentaire': 'commentaire',
        }
        # Targeted url
        cls.url = resolve_url("admission_api_v1:jury-preparation", uuid=cls.admission.uuid)
        # Create an admission supervision group
        promoter = PromoterFactory()
        committee_member = CaMemberFactory(process=promoter.process)
        cls.admission.supervision_group = promoter.process
        cls.admission.save()
        AdmissionAcademicCalendarFactory.produce_all_required()
        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory().person.user
        cls.no_role_user = PersonFactory().user
        cls.promoter_user = promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = committee_member.person.user
        cls.other_committee_member_user = CaMemberFactory().person.user

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_jury_get_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_update_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_update_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        admission = DoctorateAdmission.objects.get()
        self.assertEqual(admission.thesis_proposed_title, "Thesis title")

        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        admission = DoctorateAdmission.objects.get()
        self.assertEqual(admission.thesis_proposed_title, "titre api")

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.json()['titre_propose'], "titre api")

    def test_jury_get_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_update_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_update_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_get_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_update_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_update_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)


class JuryMembersListApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        doctoral_commission = EntityFactory()
        country = CountryFactory()
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=doctoral_commission,
            passed_confirmation=True,
        )
        cls.created_data = {
            'matricule': '',
            'institution': 'institution',
            'autre_institution': 'autre_institution',
            'pays': country.name,
            'nom': 'nom',
            'prenom': 'nouveau prenom',
            'titre': 'DOCTEUR',
            'justification_non_docteur': '',
            'genre': 'AUTRE',
            'email': 'email@example.org',
        }
        AdmissionAcademicCalendarFactory.produce_all_required()
        # Targeted url
        cls.url = resolve_url("admission_api_v1:jury-members-list", uuid=cls.admission.uuid)
        # Create an admission supervision group
        promoter = PromoterFactory()
        committee_member = CaMemberFactory(process=promoter.process)
        cls.admission.supervision_group = promoter.process
        cls.admission.save()
        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory().person.user
        cls.no_role_user = PersonFactory().user
        cls.promoter_user = promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = committee_member.person.user
        cls.other_committee_member_user = CaMemberFactory().person.user

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_jury_get_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_update_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_create_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        admission = DoctorateAdmission.objects.get()
        self.assertEqual(admission.thesis_proposed_title, "Thesis title")

        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        admission = DoctorateAdmission.objects.get()
        membre = admission.jury_members.filter(promoter__isnull=True).first()
        self.assertEqual(membre.first_name, "nouveau prenom")

        response = self.client.get(self.url, format="json")
        created_member = next((member for member in response.json() if member['uuid'] == str(membre.uuid)), None)
        self.assertIsNotNone(created_member)
        self.assertEqual(created_member['prenom'], "nouveau prenom")

    def test_jury_get_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_post_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_post_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

    def test_jury_get_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_post_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_post_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)


class JuryMembersDetailApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        doctoral_commission = EntityFactory()
        country = CountryFactory()
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=doctoral_commission,
            passed_confirmation=True,
        )
        AdmissionAcademicCalendarFactory.produce_all_required()
        cls.member = JuryMemberFactory(doctorate=cls.admission)
        cls.udpated_data = {
            'matricule': '',
            'institution': 'institution',
            'autre_institution': 'autre_institution',
            'pays': country.name,
            'nom': 'nom',
            'prenom': 'nouveau prenom',
            'titre': 'DOCTEUR',
            'justification_non_docteur': '',
            'genre': 'AUTRE',
            'email': 'email@example.org',
        }
        cls.updated_role_data = {'role': 'PRESIDENT'}
        # Targeted url
        cls.url = resolve_url(
            "admission_api_v1:jury-member-detail", uuid=cls.admission.uuid, member_uuid=cls.member.uuid
        )
        # Create an admission supervision group
        promoter = PromoterFactory()
        committee_member = CaMemberFactory(process=promoter.process)
        cls.admission.supervision_group = promoter.process
        cls.admission.save()
        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory().person.user
        cls.no_role_user = PersonFactory().user
        cls.promoter_user = promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = committee_member.person.user
        cls.other_committee_member_user = CaMemberFactory().person.user

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['post']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # GET
    def test_jury_get_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        admission = DoctorateAdmission.objects.get()
        self.assertEqual(admission.thesis_proposed_title, "Thesis title")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        membre = JuryMember.objects.get(uuid=self.member.uuid)
        self.assertEqual(membre.first_name, "first_name")

    def test_get_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_get_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    # PUT
    def test_jury_put_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_put_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        admission = DoctorateAdmission.objects.get()
        self.assertEqual(admission.thesis_proposed_title, "Thesis title")

        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        membre = JuryMember.objects.get(uuid=self.member.uuid)
        self.assertEqual(membre.first_name, "nouveau prenom")

    def test_put_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_put_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_put_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_put_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    # PATCH
    def test_patch_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_patch_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        admission = DoctorateAdmission.objects.get()
        self.assertEqual(admission.thesis_proposed_title, "Thesis title")

        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        membre = JuryMember.objects.get(uuid=self.member.uuid)
        self.assertEqual(membre.role, "PRESIDENT")

    def test_patch_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_patch_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_patch_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_patch_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    # DELETE
    def test_delete_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

        with self.assertRaises(JuryMember.DoesNotExist):
            JuryMember.objects.get(uuid=self.member.uuid)

    def test_delete_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_delete_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)
