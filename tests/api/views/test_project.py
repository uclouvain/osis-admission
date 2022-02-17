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
from unittest import mock

from django.shortcuts import resolve_url
from django.test import override_settings
from django.urls import reverse
from osis_signature.enums import SignatureState
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models import AdmissionType, DoctorateAdmission
from admission.ddd.preparation.projet_doctoral.domain.model._detail_projet import ChoixLangueRedactionThese
from admission.ddd.preparation.projet_doctoral.domain.model._enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixStatutProposition,
)
from admission.ddd.preparation.projet_doctoral.domain.model._financement import ChoixTypeFinancement
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    DoctoratNonTrouveException,
    MembreCAManquantException,
    PromoteurManquantException,
)
from admission.tests.factories import DoctorateAdmissionFactory, WriteTokenFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import CandidateFactory, CddManagerFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory, _ProcessFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class DoctorateAdmissionListApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()
        committee_member = CaMemberFactory(process=promoter.process)

        # Create doctorate management entity
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
        cls.admission = DoctorateAdmissionFactory(
            status=ChoixStatutProposition.CANCELLED.name,  # set the status to cancelled so we have access to creation
            doctorate__management_entity=cls.commission,
            supervision_group=promoter.process,
        )
        # Users
        cls.candidate = cls.admission.candidate
        cls.no_role_user = PersonFactory().user
        cls.cdd_manager_user = CddManagerFactory(entity=cls.commission).person.user
        cls.promoter_user = promoter.person.user
        cls.committee_member_user = committee_member.person.user

        cls.url = resolve_url("admission_api_v1:propositions")

    def test_list_propositions_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        # Check response data
        # Global links
        self.assertTrue('links' in response.data)
        self.assertTrue('create_proposition' in response.data['links'])
        self.assertEqual(
            response.data['links']['create_proposition'],
            {
                'method': 'POST',
                'url': reverse('admission_api_v1:propositions'),
            },
        )
        # Propositions
        self.assertTrue('propositions' in response.data)
        self.assertEqual(len(response.data['propositions']), 1)
        first_proposition = response.data['propositions'][0]
        # Check proposition links
        self.assertTrue('links' in first_proposition)
        allowed_actions = [
            'retrieve_person',
            'update_person',
            'retrieve_coordinates',
            'update_coordinates',
            'retrieve_secondary_studies',
            'update_secondary_studies',
            'retrieve_languages',
            'update_languages',
            'destroy_proposition',
            'retrieve_proposition',
            'update_proposition',
            'retrieve_cotutelle',
            'update_cotutelle',
            'retrieve_supervision',
        ]
        additional_actions = [
            'submit_proposition',
        ]
        self.assertCountEqual(
            list(first_proposition['links']),
            allowed_actions + additional_actions,
        )
        for action in allowed_actions:
            # Check the url
            self.assertTrue('url' in first_proposition['links'][action], '{} is not allowed'.format('action'))
            # Check the method type
            self.assertTrue('method' in first_proposition['links'][action])

    def test_list_propositions_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_list_propositions_cdd_manager(self):
        self.client.force_authenticate(user=self.cdd_manager_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_list_propositions_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_list_supervised_propositions_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(resolve_url("admission_api_v1:supervised_propositions"), format="json")
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


class DoctorateAdmissionCreationApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
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
        cls.institute = EntityVersionFactory(
            entity_type=EntityType.INSTITUTE.name,
        )

        cls.create_data = {
            "type_admission": AdmissionType.PRE_ADMISSION.name,
            "justification": "Some justification",
            "sigle_formation": cls.doctorate.acronym,
            "annee_formation": cls.doctorate.academic_year.year,
            "matricule_candidat": cls.candidate.global_id,
            "commission_proximite": '',
            "documents_projet": [],
            "graphe_gantt": [],
            "proposition_programme_doctoral": [],
            "projet_formation_complementaire": [],
            "lettres_recommandation": [],
            "institut_these": str(cls.institute.uuid),
        }
        cls.url = resolve_url("admission_api_v1:propositions")

    def test_admission_doctorate_creation_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)
        admission = admissions.get(uuid=response.data["uuid"])
        self.assertEqual(admission.type, self.create_data["type_admission"])
        self.assertEqual(admission.comment, self.create_data["justification"])

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.json()['propositions'][0]['sigle_doctorat'], self.doctorate.acronym)
        self.assertEqual(
            admission.reference,
            '{}-{}'.format(
                self.doctorate.academic_year.year % 100,
                300000 + admission.id,
            ),
        )

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


class DoctorateAdmissionApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()
        committee_member = CaMemberFactory(process=promoter.process)

        # Create doctorate management entity
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
        cls.admission = DoctorateAdmissionFactory(
            doctorate__management_entity=cls.commission,
            supervision_group=promoter.process,
        )

        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory().person.user
        cls.no_role_user = PersonFactory().user
        cls.cdd_manager_user = CddManagerFactory(entity=cls.commission).person.user
        cls.other_cdd_manager_user = CddManagerFactory().person.user
        cls.promoter_user = promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = committee_member.person.user
        cls.other_committee_member_user = CaMemberFactory().person.user
        # Targeted url
        cls.url = resolve_url("admission_api_v1:propositions", uuid=cls.admission.uuid)

    def test_admission_doctorate_cancel_using_api(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        # This is a soft-delete
        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)
        admission = admissions.get()
        self.assertEqual(admission.status, ChoixStatutProposition.CANCELLED.name)

    def test_user_not_logged_assert_cancel_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.delete(self.url)
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

    def test_admission_doctorate_get_proximity_commission(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        admission = DoctorateAdmissionFactory(
            candidate=self.other_candidate_user.person,
            doctorate__management_entity=self.commission,
            proximity_commission=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
        )
        response = self.client.get(resolve_url("admission_api_v1:propositions", uuid=admission.uuid), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        # Check response data
        self.assertEqual(response.json()['commission_proximite'], ChoixCommissionProximiteCDEouCLSM.ECONOMY.name)

        admission = DoctorateAdmissionFactory(
            candidate=self.other_candidate_user.person,
            doctorate__management_entity=self.commission,
            proximity_commission=ChoixCommissionProximiteCDSS.ECLI.name,
        )
        response = self.client.get(resolve_url("admission_api_v1:propositions", uuid=admission.uuid), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        # Check response data
        self.assertEqual(response.json()['commission_proximite'], ChoixCommissionProximiteCDSS.ECLI.name)

    def test_admission_doctorate_get_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        # Check response data
        # Check links
        self.assertTrue('links' in response.data)
        allowed_actions = [
            'retrieve_person',
            'update_person',
            'retrieve_coordinates',
            'update_coordinates',
            'retrieve_secondary_studies',
            'update_secondary_studies',
            'retrieve_languages',
            'update_languages',
            'destroy_proposition',
            'retrieve_proposition',
            'update_proposition',
            'retrieve_cotutelle',
            'update_cotutelle',
            'add_member',
            'remove_member',
            'retrieve_supervision',
        ]
        all_actions = allowed_actions + [
            'add_approval',
            'request_signatures',
            'submit_proposition',
        ]
        self.assertCountEqual(
            list(response.data['links']),
            all_actions,
        )
        for action in allowed_actions:
            # Check the url
            self.assertTrue('url' in response.data['links'][action], '{} is not allowed'.format(action))
            # Check the method type
            self.assertTrue('method' in response.data['links'][action])

    def test_admission_doctorate_get_using_api_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_get_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_get_using_api_cdd_manager(self):
        self.client.force_authenticate(user=self.cdd_manager_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admission_doctorate_get_using_api_other_cdd_manager(self):
        self.client.force_authenticate(user=self.other_cdd_manager_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_get_using_api_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admission_doctorate_get_using_api_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_get_using_api_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admission_doctorate_get_using_api_other_committee_member(self):
        self.client.force_authenticate(user=self.other_committee_member_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_get_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DoctorateAdmissionUpdatingApiTestCase(DoctorateAdmissionApiTestCase):
    def setUp(self):
        self.update_data = {
            "uuid": self.admission.uuid,
            "type_admission": AdmissionType.ADMISSION.name,
            "titre_projet": "A new title",
            "commission_proximite": '',
            "documents_projet": [],
            "graphe_gantt": [],
            "proposition_programme_doctoral": [],
            "projet_formation_complementaire": [],
            "lettres_recommandation": [],
        }

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
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['post', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class DoctorateAdmissionVerifyProjectTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admission = DoctorateAdmissionFactory(
            supervision_group=_ProcessFactory(),
            cotutelle=False,
            project_title="title",
            project_abstract="abstract",
            thesis_language=ChoixLangueRedactionThese.FRENCH.name,
            financing_type=ChoixTypeFinancement.SELF_FUNDING.name,
            project_document=[WriteTokenFactory().token],
            gantt_graph=[WriteTokenFactory().token],
            program_proposition=[WriteTokenFactory().token],
        )
        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory().person.user
        cls.no_role_user = PersonFactory().user
        cls.url = resolve_url("verify-project", uuid=cls.admission.uuid)

    @mock.patch(
        'admission.infrastructure.preparation.projet_doctoral.domain.service.promoteur.PromoteurTranslator.est_externe',
        return_value=False,
    )
    def test_verify_project_using_api(self, mock_is_external):
        self.client.force_authenticate(user=self.candidate.user)
        PromoterFactory(process=self.admission.supervision_group)
        CaMemberFactory(process=self.admission.supervision_group)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch(
        'admission.infrastructure.preparation.projet_doctoral.domain.service.promoteur.PromoteurTranslator.est_externe',
        return_value=False,
    )
    def test_verify_project_using_api_without_ca_members_must_fail(self, mock_is_external):
        self.client.force_authenticate(user=self.candidate.user)

        PromoterFactory(process=self.admission.supervision_group)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['status_code'], MembreCAManquantException.status_code)

    def test_verify_project_using_api_without_promoter_must_fail(self):
        self.client.force_authenticate(user=self.candidate.user)

        CaMemberFactory(process=self.admission.supervision_group)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['status_code'], PromoteurManquantException.status_code)

    def test_admission_doctorate_verify_project_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_verify_project_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class DoctorateAdmissionSubmitPropositionTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        # Create candidates
        # Complete candidate
        cls.first_candidate = CandidateFactory(person=CompletePersonFactory()).person
        cls.first_candidate.id_photo = [WriteTokenFactory().token]
        cls.first_candidate.id_card = [WriteTokenFactory().token]
        cls.first_candidate.passport = [WriteTokenFactory().token]
        cls.first_candidate.save()
        # Incomplete candidate
        cls.second_candidate = CandidateFactory(person__first_name="Jim").person
        # Create promoters
        cls.first_invited_promoter = PromoterFactory(actor_ptr__person__first_name="Joe")
        cls.first_invited_promoter.actor_ptr.switch_state(SignatureState.INVITED)
        cls.first_not_invited_promoter = PromoterFactory(actor_ptr__person__first_name="Jack")
        cls.second_invited_promoter = PromoterFactory(actor_ptr__person__first_name="Jim")
        cls.second_invited_promoter.actor_ptr.switch_state(SignatureState.INVITED)

        # Create admissions
        cls.first_admission_with_invitation = DoctorateAdmissionFactory(
            candidate=cls.first_candidate,
            supervision_group=cls.first_invited_promoter.actor_ptr.process,
        )
        cls.first_admission_without_invitation = DoctorateAdmissionFactory(
            candidate=cls.first_candidate,
            supervision_group=cls.first_not_invited_promoter.actor_ptr.process,
        )
        cls.second_admission = DoctorateAdmissionFactory(
            candidate=cls.second_candidate,
            supervision_group=cls.second_invited_promoter.actor_ptr.process,
        )
        # Create other users
        cls.no_role_user = PersonFactory(first_name="Joe").user

        # Targeted urls
        cls.first_admission_with_invitation_url = resolve_url(
            "submit-proposition",
            uuid=cls.first_admission_with_invitation.uuid,
        )
        cls.first_admission_without_invitation_url = resolve_url(
            "submit-proposition",
            uuid=cls.first_admission_without_invitation.uuid,
        )
        cls.second_admission_url = resolve_url(
            "submit-proposition",
            uuid=cls.second_admission.uuid,
        )

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.first_candidate.user)
        methods_not_allowed = ['post', 'patch', 'put', 'delete']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.first_admission_with_invitation_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_verify_valid_proposition_using_api(self):
        self.client.force_authenticate(user=self.first_candidate.user)

        response = self.client.get(self.first_admission_with_invitation_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_verify_invalid_proposition_using_api(self):
        self.client.force_authenticate(user=self.second_candidate.user)

        response = self.client.get(self.second_admission_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.json()) > 0)

    def test_admission_doctorate_verify_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.first_admission_with_invitation_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_verify_no_invited_promoters(self):
        self.client.force_authenticate(user=self.first_candidate.user)
        response = self.client.get(self.first_admission_without_invitation_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_verify_other_candidate(self):
        self.client.force_authenticate(user=self.second_candidate.user)
        response = self.client.get(self.first_admission_with_invitation_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.first_admission_with_invitation_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
