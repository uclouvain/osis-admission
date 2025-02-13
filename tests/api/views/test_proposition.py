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
import uuid

import freezegun
from django.test import override_settings
from django.shortcuts import resolve_url
from osis_history.models import HistoryEntry
from rest_framework import status
from rest_framework.test import APITestCase

from admission.models import GeneralEducationAdmission, ContinuingEducationAdmission, DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
    ChoixStatutPropositionDoctorale,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    ChoixInscriptionATitre,
    ChoixTypeAdresseFacturation,
)
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests import CheckActionLinksMixin
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, ProgramManagerRoleFactory
from admission.tests.factories.supervision import PromoterFactory, CaMemberFactory
from base.models.enums.entity_type import EntityType
from base.models.specific_iufc_informations import SpecificIUFCInformations
from base.tests import QueriesAssertionsMixin
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from osis_profile import BE_ISO_CODE
from reference.tests.factories.country import CountryFactory


class PropositionCreatePermissionsViewTestCase(CheckActionLinksMixin, APITestCase):
    @classmethod
    @freezegun.freeze_time('2023-01-01')
    def setUpTestData(cls):
        cls.commission = EntityVersionFactory(
            entity_type=EntityType.FACULTY.name,
            acronym='CMC',
        )
        cls.admission = GeneralEducationAdmissionFactory(training__management_entity=cls.commission.entity)
        cls.teaching_campus = cls.admission.training.educationgroupversion_set.first().root_group.main_teaching_campus
        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate = CandidateFactory().person

        cls.url = resolve_url("admission_api_v1:proposition_create_permissions")

    def test_get(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        json_response = response.json()
        self.assertActionLinks(
            json_response['links'],
            ['create_person', 'create_coordinates', 'create_training_choice'],
            [],
        )

    def test_get_with_submitted_admission(self):
        self.admission.status = ChoixStatutPropositionGenerale.CONFIRMEE.name
        self.admission.save()
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        json_response = response.json()
        self.assertActionLinks(
            json_response['links'],
            ['create_training_choice', 'create_coordinates'],
            ['create_person'],
        )


class GeneralPropositionViewSetApiTestCase(CheckActionLinksMixin, APITestCase):
    @classmethod
    @freezegun.freeze_time('2023-01-01')
    def setUpTestData(cls):
        cls.commission = EntityVersionFactory(
            entity_type=EntityType.FACULTY.name,
            acronym='CMC',
        )
        cls.admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            training__management_entity=cls.commission.entity,
            training__credits=180,
        )
        cls.teaching_campus = cls.admission.training.educationgroupversion_set.first().root_group.main_teaching_campus
        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate = CandidateFactory().person
        cls.no_role_user = PersonFactory().user

        cls.url = resolve_url("admission_api_v1:general_propositions", uuid=str(cls.admission.uuid))

    def test_get_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        json_response = response.json()
        training_json = {
            'sigle': self.admission.training.acronym,
            'annee': self.admission.training.academic_year.year,
            'date_debut': self.admission.training.academic_year.start_date.isoformat(),
            'intitule': self.admission.training.title,
            'intitule_fr': self.admission.training.title,
            'intitule_en': self.admission.training.title_english,
            'campus': self.teaching_campus.name,
            'campus_uuid': str(self.teaching_campus.uuid),
            'type': self.admission.training.education_group_type.name,
            'code_domaine': self.admission.training.main_domain.code,
            'campus_inscription': self.admission.training.enrollment_campus.name,
            'sigle_entite_gestion': self.commission.acronym,
            'code': self.admission.training.partial_acronym,
            'credits': 180,
        }
        double_degree_scholarship_json = {
            'uuid': str(self.admission.double_degree_scholarship.uuid),
            'nom_court': self.admission.double_degree_scholarship.short_name,
            'nom_long': self.admission.double_degree_scholarship.long_name,
            'type': self.admission.double_degree_scholarship.type,
        }
        international_scholarship_json = {
            'uuid': str(self.admission.international_scholarship.uuid),
            'nom_court': self.admission.international_scholarship.short_name,
            'nom_long': self.admission.international_scholarship.long_name,
            'type': self.admission.international_scholarship.type,
        }
        erasmus_mundus_scholarship_json = {
            'uuid': str(self.admission.erasmus_mundus_scholarship.uuid),
            'nom_court': self.admission.erasmus_mundus_scholarship.short_name,
            'nom_long': self.admission.erasmus_mundus_scholarship.long_name,
            'type': self.admission.erasmus_mundus_scholarship.type,
        }
        self.assertEqual(json_response['uuid'], str(self.admission.uuid))
        self.assertEqual(json_response['reference'], f'M-CMC22-{str(self.admission)}')
        self.assertDictEqual(json_response['formation'], training_json)
        self.assertEqual(json_response['matricule_candidat'], self.admission.candidate.global_id)
        self.assertEqual(json_response['prenom_candidat'], self.admission.candidate.first_name)
        self.assertEqual(json_response['nom_candidat'], self.admission.candidate.last_name)
        self.assertEqual(json_response['statut'], self.admission.status)
        self.assertEqual(json_response['bourse_double_diplome'], double_degree_scholarship_json)
        self.assertEqual(json_response['bourse_internationale'], international_scholarship_json)
        self.assertEqual(json_response['bourse_erasmus_mundus'], erasmus_mundus_scholarship_json)
        self.assertEqual(json_response['erreurs'], [])
        self.assertActionLinks(
            links=json_response['links'],
            allowed_actions=[
                'retrieve_person',
                'retrieve_coordinates',
                'retrieve_secondary_studies',
                'retrieve_curriculum',
                'retrieve_training_choice',
                'update_training_choice',
                'update_person',
                'update_coordinates',
                'update_secondary_studies',
                'update_curriculum',
                'submit_proposition',
                'retrieve_specific_question',
                'update_specific_question',
                'retrieve_accounting',
                'destroy_proposition',
                'update_accounting',
            ],
            forbidden_actions=[
                'retrieve_documents',
                'update_documents',
                'pay_after_submission',
                'pay_after_request',
                'view_payment',
            ],
        )

    def test_get_proposition_other_candidate_is_forbidden(self):
        self.client.force_authenticate(user=self.other_candidate.user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_proposition_no_role_user_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)

        # Create a new admission
        admission = GeneralEducationAdmissionFactory(candidate=self.candidate)
        self.assertEqual(admission.status, ChoixStatutPropositionGenerale.EN_BROUILLON.name)

        # Cancel it
        admission_to_cancel_url = resolve_url("admission_api_v1:general_propositions", uuid=str(admission.uuid))
        response = self.client.delete(admission_to_cancel_url, format="json")

        self.assertEqual(response.json()['uuid'], str(admission.uuid))

        admission = GeneralEducationAdmission.objects.get(pk=admission.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionGenerale.ANNULEE.name)

        history_entry: HistoryEntry = HistoryEntry.objects.filter(
            object_uuid=admission.uuid,
            tags__contains=['proposition', 'status-changed'],
        ).last()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.message_fr, 'La proposition a été annulée.')

    def test_delete_proposition_other_candidate_is_forbidden(self):
        self.client.force_authenticate(user=self.other_candidate.user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_proposition_no_role_user_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)


class ContinuingPropositionViewSetApiTestCase(CheckActionLinksMixin, APITestCase):
    @classmethod
    @freezegun.freeze_time('2023-01-01')
    def setUpTestData(cls):
        cls.commission = EntityVersionFactory(
            entity_type=EntityType.FACULTY.name,
            acronym='CMC',
        )
        cls.admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=cls.commission.entity,
            training__credits=180,
        )
        cls.admission_without_specific_iufc_info: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=cls.commission.entity,
            training__credits=180,
        )
        cls.first_program_manager = ProgramManagerRoleFactory(
            education_group=cls.admission.training.education_group,
            person__email='john.doe@example.be',
        )
        cls.second_program_manager = ProgramManagerRoleFactory(
            education_group=cls.admission.training.education_group,
            person__email='joe.doe@example.be',
        )
        cls.admission_without_specific_iufc_info.training.specificiufcinformations.delete()
        cls.admission_with_billing_address = ContinuingEducationAdmissionFactory(
            residence_permit=[uuid.uuid4()],
            registration_as=ChoixInscriptionATitre.PROFESSIONNEL.name,
            head_office_name='UCL',
            unique_business_number='1',
            vat_number='1A',
            professional_email='john.doe@example.be',
            billing_address_type=ChoixTypeAdresseFacturation.AUTRE.name,
            billing_address_recipient='John Doe',
            billing_address_street='rue du moulin',
            billing_address_street_number='1',
            billing_address_postal_box='PB1',
            billing_address_postal_code='1348',
            billing_address_city='Louvain-la-Neuve',
            billing_address_country=CountryFactory(iso_code=BE_ISO_CODE),
            training__management_entity=cls.commission.entity,
            training__credits=180,
        )
        cls.teaching_campus = cls.admission.training.educationgroupversion_set.first().root_group.main_teaching_campus
        # Users
        cls.candidate = cls.admission.candidate
        cls.candidate.country_of_citizenship = CountryFactory(
            iso_code=BE_ISO_CODE,
            european_union=True,
        )
        cls.candidate.save(update_fields=['country_of_citizenship'])
        cls.other_candidate = CandidateFactory().person
        cls.no_role_user = PersonFactory().user

        cls.url = resolve_url("admission_api_v1:continuing_propositions", uuid=str(cls.admission.uuid))
        cls.url_admission_without_specific_iufc_info = resolve_url(
            "admission_api_v1:continuing_propositions",
            uuid=str(cls.admission_without_specific_iufc_info.uuid),
        )
        cls.url_admission_with_address = resolve_url(
            "admission_api_v1:continuing_propositions",
            uuid=str(cls.admission_with_billing_address.uuid),
        )

    def test_get_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        json_response = response.json()
        training_json = {
            'sigle': self.admission.training.acronym,
            'annee': self.admission.training.academic_year.year,
            'date_debut': self.admission.training.academic_year.start_date.isoformat(),
            'intitule': self.admission.training.title,
            'intitule_fr': self.admission.training.title,
            'intitule_en': self.admission.training.title_english,
            'campus': self.teaching_campus.name,
            'campus_uuid': str(self.teaching_campus.uuid),
            'type': self.admission.training.education_group_type.name,
            'code_domaine': self.admission.training.main_domain.code,
            'campus_inscription': self.admission.training.enrollment_campus.name,
            'sigle_entite_gestion': self.commission.acronym,
            'code': self.admission.training.partial_acronym,
            'credits': 180,
        }
        self.assertEqual(json_response['uuid'], str(self.admission.uuid))
        self.assertEqual(json_response['reference'], f'M-CMC22-{str(self.admission)}')
        self.assertDictEqual(json_response['formation'], training_json)
        self.assertEqual(json_response['matricule_candidat'], self.admission.candidate.global_id)
        self.assertEqual(json_response['prenom_candidat'], self.admission.candidate.first_name)
        self.assertEqual(json_response['nom_candidat'], self.admission.candidate.last_name)
        self.assertEqual(
            json_response['pays_nationalite_candidat'],
            self.admission.candidate.country_of_citizenship.iso_code,
        )
        self.assertEqual(
            json_response['pays_nationalite_ue_candidat'],
            self.admission.candidate.country_of_citizenship.european_union,
        )
        self.assertEqual(json_response['statut'], self.admission.status)
        self.assertEqual(json_response['erreurs'], [])
        self.assertEqual(json_response.get('inscription_a_titre'), self.admission.registration_as)
        self.assertEqual(json_response.get('nom_siege_social'), self.admission.head_office_name)
        self.assertEqual(json_response.get('numero_unique_entreprise'), self.admission.unique_business_number)
        self.assertEqual(json_response.get('numero_tva_entreprise'), self.admission.vat_number)
        self.assertEqual(json_response.get('adresse_mail_professionnelle'), self.admission.professional_email)
        self.assertEqual(json_response.get('type_adresse_facturation'), self.admission.billing_address_type)
        self.assertIsNone(json_response.get('adresse_facturation'))
        self.assertEqual(json_response.get('motivations'), self.admission.motivations)
        self.assertEqual(
            json_response.get('moyens_decouverte_formation'),
            self.admission.ways_to_find_out_about_the_course,
        )
        self.assertEqual(
            json_response.get('autre_moyen_decouverte_formation'),
            self.admission.other_way_to_find_out_about_the_course,
        )
        self.assertCountEqual(
            json_response.get('adresses_emails_gestionnaires_formation'),
            [self.first_program_manager.person.email, self.second_program_manager.person.email],
        )
        self.assertEqual(json_response.get('marque_d_interet'), self.admission.interested_mark)

        # Custom information about the training
        specific_information: SpecificIUFCInformations = self.admission.training.specificiufcinformations
        self.assertEqual(json_response.get('aide_a_la_formation'), specific_information.training_assistance)
        self.assertEqual(
            json_response.get('inscription_au_role_obligatoire'),
            specific_information.registration_required,
        )
        self.assertEqual(json_response.get('etat_formation'), specific_information.state)

        self.assertActionLinks(
            links=json_response['links'],
            allowed_actions=[
                'retrieve_person',
                'retrieve_coordinates',
                'retrieve_secondary_studies',
                'retrieve_curriculum',
                'retrieve_training_choice',
                'update_training_choice',
                'update_person',
                'update_coordinates',
                'update_secondary_studies',
                'update_curriculum',
                'submit_proposition',
                'retrieve_specific_question',
                'update_specific_question',
                'destroy_proposition',
            ],
            forbidden_actions=[
                'retrieve_documents',
                'update_documents',
            ],
        )

    def test_get_proposition_without_specific_information_about_training(self):
        self.client.force_authenticate(user=self.admission_without_specific_iufc_info.candidate.user)

        response = self.client.get(self.url_admission_without_specific_iufc_info, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        json_response = response.json()

        # Custom information about the training
        self.assertEqual(json_response.get('aide_a_la_formation'), None)
        self.assertEqual(json_response.get('inscription_au_role_obligatoire'), None)
        self.assertEqual(json_response.get('etat_formation'), '')

    def test_get_proposition_with_custom_address(self):
        self.client.force_authenticate(user=self.admission_with_billing_address.candidate.user)

        response = self.client.get(self.url_admission_with_address, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        json_response = response.json()
        self.assertEqual(
            json_response.get('copie_titre_sejour'),
            [str(self.admission_with_billing_address.residence_permit[0])],
        )
        adresse_facturation = json_response.get('adresse_facturation')
        self.assertEqual(
            json_response.get('inscription_a_titre'),
            self.admission_with_billing_address.registration_as,
        )
        self.assertEqual(
            json_response.get('nom_siege_social'),
            self.admission_with_billing_address.head_office_name,
        )
        self.assertEqual(
            json_response.get('numero_unique_entreprise'),
            self.admission_with_billing_address.unique_business_number,
        )
        self.assertEqual(
            json_response.get('numero_tva_entreprise'),
            self.admission_with_billing_address.vat_number,
        )
        self.assertEqual(
            json_response.get('adresse_mail_professionnelle'),
            self.admission_with_billing_address.professional_email,
        )
        self.assertEqual(
            json_response.get('type_adresse_facturation'),
            self.admission_with_billing_address.billing_address_type,
        )
        self.assertIsNotNone(adresse_facturation)
        self.assertEqual(
            adresse_facturation.get('rue'),
            self.admission_with_billing_address.billing_address_street,
        )
        self.assertEqual(
            adresse_facturation.get('code_postal'),
            self.admission_with_billing_address.billing_address_postal_code,
        )
        self.assertEqual(
            adresse_facturation.get('ville'),
            self.admission_with_billing_address.billing_address_city,
        )
        self.assertEqual(
            adresse_facturation.get('pays'),
            self.admission_with_billing_address.billing_address_country.iso_code,
        )
        self.assertEqual(
            adresse_facturation.get('numero_rue'),
            self.admission_with_billing_address.billing_address_street_number,
        )
        self.assertEqual(
            adresse_facturation.get('boite_postale'),
            self.admission_with_billing_address.billing_address_postal_box,
        )
        self.assertEqual(
            adresse_facturation.get('destinataire'),
            self.admission_with_billing_address.billing_address_recipient,
        )

    def test_get_proposition_other_candidate_is_forbidden(self):
        self.client.force_authenticate(user=self.other_candidate.user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_proposition_no_role_user_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)

        # Create a new admission
        admission = ContinuingEducationAdmissionFactory(candidate=self.candidate)
        self.assertEqual(admission.status, ChoixStatutPropositionContinue.EN_BROUILLON.name)

        # Cancel it
        admission_to_cancel_url = resolve_url("admission_api_v1:continuing_propositions", uuid=str(admission.uuid))
        response = self.client.delete(admission_to_cancel_url, format="json")

        self.assertEqual(response.json()['uuid'], str(admission.uuid))

        admission = ContinuingEducationAdmission.objects.get(pk=admission.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionContinue.ANNULEE.name)

        # Check that an entry has been created in the history
        history_entry: HistoryEntry = HistoryEntry.objects.filter(
            object_uuid=admission.uuid,
            tags__contains=['proposition', 'status-changed'],
        ).last()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.message_fr, 'La proposition a été annulée.')

    def test_delete_proposition_other_candidate_is_forbidden(self):
        self.client.force_authenticate(user=self.other_candidate.user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_proposition_no_role_user_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)


@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class DoctorateAdmissionApiTestCase(CheckActionLinksMixin, QueriesAssertionsMixin, APITestCase):
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
            training__management_entity=cls.commission,
            supervision_group=promoter.process,
            with_answers_to_specific_questions=True,
        )

        cls.update_data = {
            "uuid": cls.admission.uuid,
            "type_admission": ChoixTypeAdmission.ADMISSION.name,
            "titre_projet": "A new title",
            "commission_proximite": '',
            "bourse_preuve": [],
            "documents_projet": [],
            "graphe_gantt": [],
            "proposition_programme_doctoral": [],
            "projet_formation_complementaire": [],
            "lettres_recommandation": [],
        }

        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory().person.user
        cls.no_role_user = PersonFactory().user
        cls.promoter_user = promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = committee_member.person.user
        cls.other_committee_member_user = CaMemberFactory().person.user
        AdmissionAcademicCalendarFactory.produce_all_required()
        # Targeted url
        cls.url = resolve_url("admission_api_v1:doctorate_propositions", uuid=cls.admission.uuid)

    def test_admission_doctorate_cancel_using_api(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        # This is a soft-delete
        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)
        admission = admissions.get()
        self.assertEqual(admission.status, ChoixStatutPropositionDoctorale.ANNULEE.name)
        self.assertEqual(admission.last_update_author, self.candidate)

        history_entry = HistoryEntry.objects.filter(object_uuid=self.admission.uuid).first()
        self.assertIsNotNone(history_entry)
        self.assertCountEqual(history_entry.tags, ['proposition', 'status-changed'])

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
            training__management_entity=self.commission,
            proximity_commission=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
        )
        response = self.client.get(
            resolve_url("admission_api_v1:doctorate_propositions", uuid=admission.uuid), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        # Check response data
        self.assertEqual(response.json()['commission_proximite'], ChoixCommissionProximiteCDEouCLSM.ECONOMY.name)

        admission = DoctorateAdmissionFactory(
            candidate=self.other_candidate_user.person,
            training__management_entity=self.commission,
            proximity_commission=ChoixCommissionProximiteCDSS.ECLI.name,
        )
        response = self.client.get(
            resolve_url("admission_api_v1:doctorate_propositions", uuid=admission.uuid), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        # Check response data
        self.assertEqual(response.json()['commission_proximite'], ChoixCommissionProximiteCDSS.ECLI.name)

        admission = DoctorateAdmissionFactory(
            candidate=self.other_candidate_user.person,
            training__management_entity=self.commission,
            training__acronym="SC3DP",
            proximity_commission=ChoixSousDomaineSciences.CHEMISTRY.name,
        )
        response = self.client.get(
            resolve_url("admission_api_v1:doctorate_propositions", uuid=admission.uuid), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        # Check response data
        self.assertEqual(response.json()['commission_proximite'], ChoixSousDomaineSciences.CHEMISTRY.name)

    def test_admission_doctorate_get_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        with self.assertNumQueriesLessThan(17):
            response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        # Check response data
        self.assertEqual(
            response.json()['reponses_questions_specifiques'],
            {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
                'fe254203-17c7-47d6-95e4-3c5c532da552': ['ae254203-17c7-47d6-95e4-3c5c532da550'],
            },
        )
        # Check links
        self.assertTrue('links' in response.data)
        allowed_actions = [
            'retrieve_person',
            'update_person',
            'retrieve_coordinates',
            'update_coordinates',
            'retrieve_training_choice',
            'update_training_choice',
            'retrieve_secondary_studies',
            'update_secondary_studies',
            'retrieve_languages',
            'update_languages',
            'destroy_proposition',
            'retrieve_project',
            'update_project',
            'retrieve_cotutelle',
            'update_cotutelle',
            'add_member',
            'edit_external_member',
            'remove_member',
            'set_reference_promoter',
            'retrieve_supervision',
            'update_curriculum',
            'retrieve_curriculum',
            'retrieve_accounting',
            'update_accounting',
            'request_signatures',
            'submit_proposition',
        ]
        forbidden_actions = [
            'add_approval',
            'approve_by_pdf',
            'retrieve_documents',
            'update_documents',
        ]
        self.assertActionLinks(response.data['links'], allowed_actions, forbidden_actions)

    def test_admission_doctorate_get_using_api_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_get_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
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

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['post', 'patch', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
