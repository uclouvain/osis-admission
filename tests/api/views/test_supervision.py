# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    MembreCANonTrouveException,
    PromoteurNonTrouveException,
)
from admission.tests import QueriesAssertionsMixin
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.supervision import CaMemberFactory, ExternalPromoterFactory, PromoterFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory
from osis_signature.enums import SignatureState
from osis_signature.models import StateHistory
from reference.tests.factories.country import CountryFactory


class SupervisionApiTestCase(QueriesAssertionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        cls.commission = EntityVersionFactory(
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.promoter = PromoterFactory(actor_ptr__person__first_name="Joe")
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=cls.commission,
            supervision_group=cls.promoter.actor_ptr.process,
        )
        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory(person__first_name="Jim").person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user
        # Target url
        cls.url = resolve_url("admission_api_v1:supervision", uuid=cls.admission.uuid)
        cls.empty_external_data = {
            'prenom': '',
            'nom': '',
            'email': '',
            'est_docteur': False,
            'institution': '',
            'ville': '',
            'pays': '',
            'langue': '',
        }
        CountryFactory(iso_code='FR')

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Get
    def test_supervision_get_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.url)
        promoteurs = response.json()['signatures_promoteurs']
        self.assertEqual(len(promoteurs), 1)
        self.assertEqual(promoteurs[0]['statut'], 'NOT_INVITED')
        self.assertEqual(promoteurs[0]['promoteur']['prenom'], 'Joe')

    def test_supervision_get_using_api_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_get_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_get_using_api_promoter(self):
        # Other user
        other_promoter = PromoterFactory()

        # The current user is not yet a supervisor of the current admission
        self.client.force_authenticate(user=other_promoter.person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the current admission
        self.client.force_authenticate(user=self.promoter.person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_supervision_get_using_api_committee_member(self):
        # Current user
        member = CaMemberFactory(process=self.promoter.actor_ptr.process)

        # Other user
        other_member = CaMemberFactory()

        # The current user is not yet a supervisor of the admission
        self.client.force_authenticate(user=other_member.person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the admission
        self.client.force_authenticate(user=member.person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    # Add member
    def test_supervision_ajouter_membre_process_inexistant(self):
        admission = DoctorateAdmissionFactory(
            training__management_entity=self.commission,
            supervision_group=None,
        )
        self.client.force_authenticate(user=admission.candidate.user)
        self.assertIsNone(admission.supervision_group)
        url = resolve_url("admission_api_v1:supervision", uuid=admission.uuid)
        data = {
            'matricule': PersonFactory(first_name="John").global_id,
            'type': ActorType.CA_MEMBER.name,
            **self.empty_external_data,
        }
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        response = self.client.get(url)
        promoteurs = response.json()['signatures_membres_CA']
        self.assertEqual(promoteurs[0]['membre_CA']['prenom'], 'John')
        admission.refresh_from_db()
        self.assertIsNotNone(admission.supervision_group)

    def test_supervision_ajouter_membre_ca(self):
        self.client.force_authenticate(user=self.candidate.user)

        data = {
            'matricule': PersonFactory(first_name="John").global_id,
            'type': ActorType.CA_MEMBER.name,
            **self.empty_external_data,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        response = self.client.get(self.url)
        membres_ca = response.json()['signatures_membres_CA']
        self.assertEqual(membres_ca[0]['membre_CA']['prenom'], 'John')

    def test_supervision_ajouter_membre_ca_externe(self):
        self.client.force_authenticate(user=self.candidate.user)

        data = {
            'matricule': "",
            'type': ActorType.CA_MEMBER.name,
            'prenom': 'Jean',
            'nom': 'Pierre',
            'email': 'jeanpierre@example.org',
            'est_docteur': True,
            'institution': 'Psychiatrique',
            'ville': 'Somewhere',
            'pays': 'FR',
            'langue': 'fr-be',
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        response = self.client.get(self.url)
        membres_ca = response.json()['signatures_membres_CA']
        self.assertEqual(len(membres_ca), 1)
        self.assertEqual(membres_ca[0]['membre_CA']['prenom'], 'Jean')

    def test_supervision_ajouter_membre_ca_inexistant(self):
        self.client.force_authenticate(user=self.candidate.user)

        data = {'matricule': "inexistant", 'type': ActorType.CA_MEMBER.name, **self.empty_external_data}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], MembreCANonTrouveException.status_code)

    def test_supervision_ajouter_promoteur(self):
        self.client.force_authenticate(user=self.candidate.user)

        data = {
            'matricule': TutorFactory(person__first_name="John").person.global_id,
            'type': ActorType.PROMOTER.name,
            **self.empty_external_data,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        response = self.client.get(self.url)
        promoteurs = response.json()['signatures_promoteurs']
        self.assertEqual(len(promoteurs), 2)
        self.assertIn('John', [promoteur['promoteur']['prenom'] for promoteur in promoteurs])

    def test_supervision_ajouter_promoteur_externe(self):
        self.client.force_authenticate(user=self.candidate.user)

        data = {
            'matricule': "",
            'type': ActorType.PROMOTER.name,
            'prenom': 'Jean',
            'nom': 'Pierre',
            'email': 'jeanpierre@example.org',
            'est_docteur': True,
            'institution': 'Psychiatrique',
            'ville': 'Somewhere',
            'pays': 'FR',
            'langue': 'fr-be',
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        response = self.client.get(self.url)
        promoteurs = response.json()['signatures_promoteurs']
        self.assertEqual(len(promoteurs), 2)
        self.assertEqual(promoteurs[-1]['promoteur']['prenom'], 'Jean')

    def test_supervision_ajouter_promoteur_inexistant(self):
        self.client.force_authenticate(user=self.candidate.user)

        data = {
            'matricule': "inexistant",
            'type': ActorType.PROMOTER.name,
            **self.empty_external_data,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], PromoteurNonTrouveException.status_code)

    def test_supervision_ajouter_membre_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        data = {
            'matricule': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
            **self.empty_external_data,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_ajouter_membre_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        data = {
            'matricule': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
            **self.empty_external_data,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_ajouter_membre_promoter(self):
        # Other user
        other_promoter = PromoterFactory()

        # The current user is not yet a supervisor of the current admission
        self.client.force_authenticate(user=other_promoter.person.user)
        data = {
            'matricule': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
            **self.empty_external_data,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the current admission
        self.client.force_authenticate(user=self.promoter.person.user)
        data = {
            'matricule': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
            **self.empty_external_data,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_ajouter_membre_committee_member(self):
        # Current user
        member = CaMemberFactory(process=self.promoter.actor_ptr.process)

        # Other user
        other_member = CaMemberFactory()

        # The current user is not yet a supervisor of the admission
        self.client.force_authenticate(user=other_member.person.user)
        data = {
            'matricule': PersonFactory(first_name="Joe").global_id,
            'type': ActorType.CA_MEMBER.name,
            **self.empty_external_data,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the admission
        self.client.force_authenticate(user=member.person.user)
        data = {
            'matricule': PersonFactory(first_name="Joe").global_id,
            'type': ActorType.CA_MEMBER.name,
            **self.empty_external_data,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Remove member
    def test_supervision_supprimer_promoteur_using_api(self):
        self.client.force_authenticate(user=self.candidate.user)

        promoter = PromoterFactory(process=self.promoter.actor_ptr.process)

        response = self.client.post(
            self.url,
            data={
                'type': ActorType.PROMOTER.name,
                'uuid_membre': promoter.uuid,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_supervision_supprimer_membre_ca_using_api(self):
        self.client.force_authenticate(user=self.candidate.user)

        member = CaMemberFactory(process=self.promoter.actor_ptr.process)

        response = self.client.post(
            self.url,
            data={
                'type': ActorType.CA_MEMBER.name,
                'uuid_membre': member.uuid,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_supervision_supprimer_membre_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)

        PromoterFactory(process=self.promoter.actor_ptr.process)

        response = self.client.post(
            self.url,
            data={
                'type': ActorType.PROMOTER.name,
                'uuid_membre': self.promoter.uuid,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_supprimer_membre_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)

        response = self.client.post(
            self.url,
            data={
                'type': ActorType.PROMOTER.name,
                'uuid_membre': self.promoter.uuid,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_supprimer_membre_promoter(self):
        # Other user
        other_promoter = PromoterFactory()

        # The current user is not yet a supervisor of the admission
        self.client.force_authenticate(user=other_promoter.person.user)
        data = {
            'type': ActorType.PROMOTER.name,
            'uuid_membre': self.promoter.uuid,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the admission
        self.client.force_authenticate(user=self.promoter.person.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_supprimer_membre_committee_member(self):
        # Current user
        member = CaMemberFactory(process=self.promoter.actor_ptr.process)

        # Other user
        other_member = CaMemberFactory()

        # The current user is not yet a supervisor of the admission
        self.client.force_authenticate(user=other_member.person.user)
        data = {
            'matricule': member.uuid,
            'type': ActorType.CA_MEMBER.name,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The current user is now a supervisor of the admission
        self.client.force_authenticate(user=member.person.user)
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_modification_impossible_par_doctorant_apres_envoi(self):
        self.client.force_authenticate(user=self.candidate.user)

        self.admission.status = ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name
        self.admission.save()

        data = {
            'matricule': self.promoter.uuid,
            'type': ActorType.PROMOTER.name,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        data = {
            'matricule': TutorFactory(person__first_name="Joe").person.global_id,
            'type': ActorType.PROMOTER.name,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.admission.status = ChoixStatutPropositionDoctorale.EN_BROUILLON.name
        self.admission.save()

    def test_supervision_modification_par_doctorant_apres_refus(self):
        self.client.force_authenticate(user=self.candidate.user)

        promoter = PromoterFactory(process=self.admission.supervision_group)
        StateHistory.objects.create(
            actor=promoter.actor_ptr,
            state=SignatureState.DECLINED.name,
        )

        # Check supervision before
        response = self.client.get(self.url)
        promoters = response.json()['signatures_promoteurs']
        membres_CA = response.json()['signatures_membres_CA']
        self.assertEqual(len(promoters), 2)
        self.assertEqual(len(membres_CA), 0)

        # Add CA member
        data = {
            'matricule': PersonFactory(first_name="Joe").global_id,
            'type': ActorType.CA_MEMBER.name,
            **self.empty_external_data,
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Remove promoter
        data = {
            'type': ActorType.PROMOTER.name,
            'uuid_membre': promoter.uuid,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check supervision after
        response = self.client.get(self.url)
        promoters = response.json()['signatures_promoteurs']
        membres_CA = response.json()['signatures_membres_CA']
        self.assertEqual(len(promoters), 1)
        self.assertEqual(membres_CA[0]['membre_CA']['prenom'], 'Joe')

    def test_supervision_modification_externe_par_doctorant(self):
        self.client.force_authenticate(user=self.candidate.user)

        external = ExternalPromoterFactory(process=self.admission.supervision_group, first_name="John")

        # Check supervision before
        response = self.client.get(self.url)
        data = response.json()
        self.assertEqual(len(data['signatures_promoteurs']), 2)
        self.assertEqual(data['signatures_promoteurs'][1]['promoteur']['prenom'], 'John')

        # Edit member
        data = {
            'uuid_proposition': self.admission.uuid,
            'uuid_membre': external.uuid,
            'prenom': 'Joe',
            'nom': 'Dalton',
            'email': 'joe@example.org',
            'est_docteur': False,
            'institution': 'Nope',
            'ville': 'Nope',
            'pays': 'FR',
            'langue': 'fr-be',
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check supervision after
        response = self.client.get(self.url)
        data = response.json()
        self.assertEqual(len(data['signatures_promoteurs']), 2)
        self.assertEqual(len(data['signatures_membres_CA']), 0)
        self.assertEqual(data['signatures_promoteurs'][1]['promoteur']['prenom'], 'Joe')

    def test_supervision_designer_promoteur_reference(self):
        self.client.force_authenticate(user=self.candidate.user)
        promoter1 = PromoterFactory(process=self.admission.supervision_group)
        promoter2 = PromoterFactory(process=self.admission.supervision_group)

        url = resolve_url("admission_api_v1:set-reference-promoter", uuid=self.admission.uuid)
        data = {
            'uuid_promoteur': promoter1.uuid,
            'uuid_proposition': self.admission.uuid,
        }
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        response = self.client.get(self.url)
        self.assertEqual(response.json()['promoteur_reference'], str(promoter1.uuid))

        # Now change promoter
        data = {
            'uuid_promoteur': promoter2.uuid,
            'uuid_proposition': self.admission.uuid,
        }
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        response = self.client.get(self.url)
        self.assertEqual(response.json()['promoteur_reference'], str(promoter2.uuid))
