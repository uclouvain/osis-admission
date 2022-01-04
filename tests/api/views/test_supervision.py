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

from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    MembreCANonTrouveException,
    PromoteurNonTrouveException,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.groups import CandidateGroupFactory, CddManagerGroupFactory,\
    CommitteeMemberGroupFactory, PromoterGroupFactory
from admission.tests.factories.roles import CddManagerFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class SupervisionApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        cls.commission = EntityVersionFactory(
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.admission = DoctorateAdmissionFactory(doctorate__management_entity=cls.commission)
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
        # Target url
        cls.url = resolve_url("supervision", uuid=cls.admission.uuid)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Get
    def test_supervision_get_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'signatures_promoteurs': [], 'signatures_membres_CA': []})

        promoter = PromoterFactory(actor_ptr__person__first_name="Joe")
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()

        response = self.client.get(self.url, format="json")
        promoteurs = response.json()['signatures_promoteurs']
        self.assertEqual(len(promoteurs), 1)
        self.assertEqual(promoteurs[0]['status'], 'NOT_INVITED')
        self.assertEqual(promoteurs[0]['promoteur']['prenom'], 'Joe')

    def test_supervision_get_using_api_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_get_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_get_using_api_cdd_manager(self):
        self.client.force_authenticate(user=self.cdd_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_supervision_get_using_api_other_cdd_manager(self):
        self.client.force_authenticate(user=self.other_cdd_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_get_using_api_promoter(self):
        # Current user
        promoter = PromoterFactory()
        promoter.person.user.groups.add(PromoterGroupFactory())

        # Other user
        other_promoter = PromoterFactory()
        self.admission.supervision_group = other_promoter.actor_ptr.process
        self.admission.save()

        # The current user is not yet a supervisor of the current admission
        self.client.force_authenticate(user=promoter.person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the current admission
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_supervision_get_using_api_committee_member(self):
        # Current user
        member = CaMemberFactory()
        member.person.user.groups.add(CommitteeMemberGroupFactory())

        # Other user
        other_member = CaMemberFactory()
        self.admission.supervision_group = other_member.actor_ptr.process
        self.admission.save()

        # The current user is not yet a supervisor of the admission
        self.client.force_authenticate(user=member.person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the admission
        self.admission.supervision_group = member.actor_ptr.process
        self.admission.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Add member
    def test_supervision_ajouter_membre_ca(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data={
            'member': PersonFactory(first_name="Joe").global_id,
            'type': ActorType.CA_MEMBER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.url, format="json")
        promoteurs = response.json()['signatures_membres_CA']
        self.assertEqual(promoteurs[0]['membre_CA']['prenom'], 'Joe')

    def test_supervision_ajouter_membre_ca_inexistant(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data={
            'member': "inexistant",
            'type': ActorType.CA_MEMBER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], MembreCANonTrouveException.status_code)

    def test_supervision_ajouter_promoteur(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data={
            'member': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.url, format="json")
        promoteurs = response.json()['signatures_promoteurs']
        self.assertEqual(len(promoteurs), 1)
        self.assertEqual(promoteurs[0]['promoteur']['prenom'], 'Joe')

    def test_supervision_ajouter_promoteur_inexistant(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data={
            'member': "inexistant",
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], PromoteurNonTrouveException.status_code)

    def test_supervision_ajouter_membre_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.put(self.url, data={
            'member': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_ajouter_membre_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.put(self.url, data={
            'member': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_ajouter_membre_cdd_manager(self):
        self.client.force_authenticate(user=self.cdd_manager_user)
        response = self.client.put(self.url, data={
            'member': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_supervision_ajouter_membre_other_cdd_manager(self):
        self.client.force_authenticate(user=self.other_cdd_manager_user)
        response = self.client.put(self.url, data={
            'member': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_ajouter_membre_promoter(self):
        # Current user
        promoter = PromoterFactory()
        promoter.person.user.groups.add(PromoterGroupFactory())

        # Other user
        other_promoter = PromoterFactory()
        self.admission.supervision_group = other_promoter.actor_ptr.process
        self.admission.save()

        # The current user is not yet a supervisor of the current admission
        self.client.force_authenticate(user=promoter.person.user)
        response = self.client.put(self.url, data={
            'member': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the current admission
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()
        response = self.client.put(self.url, data={
            'member': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_ajouter_membre_committee_member(self):
        # Current user
        member = CaMemberFactory()
        member.person.user.groups.add(CommitteeMemberGroupFactory())

        # Other user
        other_member = CaMemberFactory()
        self.admission.supervision_group = other_member.actor_ptr.process
        self.admission.save()

        # The current user is not yet a supervisor of the admission
        self.client.force_authenticate(user=member.person.user)
        response = self.client.put(self.url, data={
            'member': PersonFactory(first_name="Joe").global_id,
            'type': ActorType.CA_MEMBER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the admission
        self.admission.supervision_group = member.actor_ptr.process
        self.admission.save()
        response = self.client.put(self.url, data={
            'member': PersonFactory(first_name="Joe").global_id,
            'type': ActorType.CA_MEMBER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Remove member
    def test_supervision_supprimer_promoteur_using_api(self):
        self.client.force_authenticate(user=self.candidate.user)

        promoter = PromoterFactory()
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()

        response = self.client.post(self.url, data={
            'member': promoter.person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_supervision_supprimer_membre_ca_using_api(self):
        self.client.force_authenticate(user=self.candidate.user)

        member = CaMemberFactory()
        self.admission.supervision_group = member.actor_ptr.process
        self.admission.save()

        response = self.client.post(self.url, data={
            'member': member.person.global_id,
            'type': ActorType.CA_MEMBER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_supervision_supprimer_membre_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
    
        promoter = PromoterFactory()
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()

        response = self.client.post(self.url, data={
            'member': promoter.person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_supprimer_membre_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
    
        promoter = PromoterFactory()
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()

        response = self.client.post(self.url, data={
            'member': promoter.person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_supprimer_membre_cdd_manager(self):
        self.client.force_authenticate(user=self.cdd_manager_user)
    
        promoter = PromoterFactory()
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()

        response = self.client.post(self.url, data={
            'member': promoter.person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_supervision_supprimer_membre_other_cdd_manager(self):
        self.client.force_authenticate(user=self.other_cdd_manager_user)
    
        promoter = PromoterFactory()
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()

        response = self.client.post(self.url, data={
            'member': promoter.person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_supprimer_membre_promoter(self):
        # Current user
        promoter = PromoterFactory()
        promoter.person.user.groups.add(PromoterGroupFactory())

        # Other user
        other_promoter = PromoterFactory()
        self.admission.supervision_group = other_promoter.actor_ptr.process
        self.admission.save()

        # The current user is not yet a supervisor of the admission
        self.client.force_authenticate(user=promoter.person.user)
        response = self.client.post(self.url, data={
            'member': promoter.person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the admission
        self.admission.supervision_group = promoter.actor_ptr.process
        self.admission.save()
        response = self.client.post(self.url, data={
            'member': promoter.person.global_id,
            'type': ActorType.PROMOTER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_supprimer_membre_committee_member(self):
        # Current user
        member = CaMemberFactory()
        member.person.user.groups.add(CommitteeMemberGroupFactory())

        # Other user
        other_member = CaMemberFactory()
        self.admission.supervision_group = other_member.actor_ptr.process
        self.admission.save()

        # The current user is not yet a supervisor of the admission
        self.client.force_authenticate(user=member.person.user)
        response = self.client.put(self.url, data={
            'member': member.person.global_id,
            'type': ActorType.CA_MEMBER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the admission
        self.admission.supervision_group = member.actor_ptr.process
        self.admission.save()
        response = self.client.put(self.url, data={
            'member': member.person.global_id,
            'type': ActorType.CA_MEMBER.name,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
