# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models import AdmissionType, DoctorateAdmission
from admission.ddd.preparation.projet_doctoral.domain.model._enums import ChoixStatusProposition
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import DoctoratNonTrouveException
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.groups import CandidateGroupFactory, CddManagerGroupFactory, CommitteeMemberGroupFactory, PromoterGroupFactory
from admission.tests.factories.roles import CddManagerFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class DoctorateAdmissionListApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.admission = DoctorateAdmissionFactory(doctorate__management_entity=cls.commission)
        # Create an admission supervision group
        promoter = PromoterFactory(actor_ptr__person__first_name="Jane")
        committee_member = CaMemberFactory(process=promoter.process)
        cls.admission.supervision_group = promoter.process
        cls.admission.save()
        # Users
        cls.candidate = cls.admission.candidate
        cls.candidate.user.groups.add(CandidateGroupFactory())
        cls.no_role_user = PersonFactory(first_name="Joe").user
        cls.cdd_manager_user = CddManagerFactory(entity=cls.commission).person.user
        cls.cdd_manager_user.groups.add(CddManagerGroupFactory())
        cls.promoter_user = promoter.person.user
        cls.promoter_user.groups.add(PromoterGroupFactory())
        cls.committee_member_user = committee_member.person.user
        cls.committee_member_user.groups.add(CommitteeMemberGroupFactory())

        cls.url = resolve_url("propositions")

    def test_list_propositions_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_list_propositions_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_list_propositions_cdd_manager(self):
        self.client.force_authenticate(user=self.cdd_manager_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_list_propositions_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_list_propositions_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

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


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class DoctorateAdmissionCreationApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        cls.candidate.user.groups.add(CandidateGroupFactory())
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.doctorate = DoctorateFactory(management_entity=cls.commission)
        # Users
        cls.no_role_user = PersonFactory(first_name="Joe").user
        cls.cdd_manager_user = CddManagerFactory(entity=cls.commission).person.user
        cls.cdd_manager_user.groups.add(CddManagerGroupFactory())
        cls.promoter_user = PersonFactory(first_name="Jane").user
        cls.promoter_user.groups.add(PromoterGroupFactory())
        cls.committee_member_user = PersonFactory(first_name="Jim").user
        cls.committee_member_user.groups.add(CommitteeMemberGroupFactory())

        cls.create_data = {
            "type_admission": AdmissionType.PRE_ADMISSION.name,
            "justification": "Some justification",
            "sigle_formation": cls.doctorate.acronym,
            "annee_formation": cls.doctorate.academic_year.year,
            "matricule_candidat": cls.candidate.global_id,
            "bureau_CDE": '',
            "documents_projet": [],
            "graphe_gantt": [],
            "proposition_programme_doctoral": [],
            "projet_formation_complementaire": [],
        }
        cls.url = resolve_url("propositions")

    def test_admission_doctorate_creation_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)
        admission = admissions.get(uuid=response.data["uuid"])
        self.assertEqual(admission.type, self.create_data["type_admission"])
        self.assertEqual(admission.comment, self.create_data["justification"])
        response = self.client.get(resolve_url("propositions"), format="json")
        self.assertEqual(response.json()[0]['sigle_doctorat'], self.doctorate.acronym)

    def test_admission_doctorate_creation_using_api_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_admission_doctorate_creation_using_api_cdd_manager(self):
        self.client.force_authenticate(user=self.cdd_manager_user)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_admission_doctorate_creation_using_api_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_admission_doctorate_creation_using_api_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_admission_doctorate_creation_using_api_with_wrong_doctorate(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, "sigle_formation": "UNKONWN"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], DoctoratNonTrouveException.status_code)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class DoctorateAdmissionUpdatingApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.admission = DoctorateAdmissionFactory(doctorate__management_entity=cls.commission)
        cls.update_data = {
            "uuid": cls.admission.uuid,
            "type_admission": AdmissionType.ADMISSION.name,
            "titre_projet": "A new title",
            "bureau_CDE": '',
            "documents_projet": [],
            "graphe_gantt": [],
            "proposition_programme_doctoral": [],
            "projet_formation_complementaire": [],
        }
        cls.url = resolve_url("propositions", uuid=cls.admission.uuid)
        # Create an admission supervision group
        promoter = PromoterFactory(actor_ptr__person__first_name="Jane")
        committee_member = CaMemberFactory(process=promoter.process)
        cls.admission.supervision_group = promoter.process
        cls.admission.save()
        # Users
        cls.candidate = cls.admission.candidate
        cls.candidate.user.groups.add(CandidateGroupFactory())
        cls.other_candidate_user = PersonFactory(first_name="Jim").user
        cls.other_candidate_user.groups.add(CandidateGroupFactory())
        cls.no_role_user = PersonFactory(first_name="Joe").user
        cls.cdd_manager_user = CddManagerFactory(entity=cls.commission).person.user
        cls.cdd_manager_user.groups.add(CddManagerGroupFactory())
        cls.other_cdd_manager_user = CddManagerFactory().person.user
        cls.other_cdd_manager_user.groups.add(CddManagerGroupFactory())
        cls.promoter_user = promoter.person.user
        cls.promoter_user.groups.add(PromoterGroupFactory())
        cls.other_promoter_user = PersonFactory(first_name="Jessy").user
        cls.other_promoter_user.groups.add(PromoterGroupFactory())
        cls.committee_member_user = committee_member.person.user
        cls.committee_member_user.groups.add(CommitteeMemberGroupFactory())
        cls.other_committee_member_user = PersonFactory(first_name="James").user
        cls.other_committee_member_user.groups.add(CommitteeMemberGroupFactory())


    def test_admission_doctorate_update_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.put(self.url, data=self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)
        admission = admissions.get()
        # The author must not change
        self.assertEqual(admission.candidate, self.candidate)
        # But all the following should
        self.assertEqual(admission.type, self.update_data["type_admission"])
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.json()['sigle_doctorat'], self.admission.doctorate.acronym)
        self.assertEqual(response.json()['titre_projet'], "A new title")

    def test_admission_doctorate_update_using_api_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.put(self.url, data=self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_update_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.put(self.url, data=self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_update_using_api_cdd_manager(self):
        self.client.force_authenticate(user=self.cdd_manager_user)
        response = self.client.put(self.url, data=self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admission_doctorate_update_using_api_other_cdd_manager(self):
        self.client.force_authenticate(user=self.other_cdd_manager_user)
        response = self.client.put(self.url, data=self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_update_using_api_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.put(self.url, data=self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_update_using_api_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.put(self.url, data=self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_update_using_api_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.put(self.url, data=self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_update_using_api_other_committee_member(self):
        self.client.force_authenticate(user=self.other_committee_member_user)
        response = self.client.put(self.url, data=self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['post', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class DoctorateAdmissionDeletingApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.admission = DoctorateAdmissionFactory(doctorate__management_entity=cls.commission)
        # Create an admission supervision group
        promoter = PromoterFactory()
        committee_member = CaMemberFactory(process=promoter.process)
        cls.admission.supervision_group = promoter.process
        cls.admission.save()
        # Users
        cls.candidate = cls.admission.candidate
        cls.candidate.user.groups.add(CandidateGroupFactory())
        cls.other_candidate_user = PersonFactory().user
        cls.other_candidate_user.groups.add(CandidateGroupFactory())
        cls.no_role_user = PersonFactory().user
        cls.cdd_manager_user = CddManagerFactory(entity=cls.commission).person.user
        cls.cdd_manager_user.groups.add(CddManagerGroupFactory())
        cls.other_cdd_manager_user = CddManagerFactory().person.user
        cls.other_cdd_manager_user.groups.add(CddManagerGroupFactory())
        cls.promoter_user = promoter.person.user
        cls.promoter_user.groups.add(PromoterGroupFactory())
        cls.other_promoter_user = PersonFactory().user
        cls.other_promoter_user.groups.add(PromoterGroupFactory())
        cls.committee_member_user = committee_member.person.user
        cls.committee_member_user.groups.add(CommitteeMemberGroupFactory())
        cls.other_committee_member_user = PersonFactory().user
        cls.other_committee_member_user.groups.add(CommitteeMemberGroupFactory())
        # Targeted url
        cls.url = resolve_url("propositions", uuid=cls.admission.uuid)

    def test_admission_doctorate_cancel_using_api(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        # This is a soft-delete
        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)
        admission = admissions.get()
        self.assertEqual(admission.status, ChoixStatusProposition.CANCELLED.name)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admission_doctorate_cancel_using_api_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_cancel_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_cancel_using_api_cdd_manager(self):
        self.client.force_authenticate(user=self.cdd_manager_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_cancel_using_api_other_cdd_manager(self):
        self.client.force_authenticate(user=self.other_cdd_manager_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_cancel_using_api_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_cancel_using_api_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_cancel_using_api_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_cancel_using_api_other_committee_member(self):
        self.client.force_authenticate(user=self.other_committee_member_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

  