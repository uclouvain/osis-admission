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

import datetime
import uuid
from unittest import mock
from unittest.mock import patch

import freezegun
from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.translation import gettext_lazy as _
from osis_history.models import HistoryEntry
from osis_notification.models import WebNotification
from osis_signature.enums import SignatureState
from rest_framework import status
from rest_framework.test import APITestCase

from admission.models import AdmissionFormItemInstantiation, DoctorateAdmission, AdmissionTask
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    MembreCAManquantException,
    PromoteurDeReferenceManquantException,
    PromoteurManquantException,
    AbsenceDeDetteNonCompleteeDoctoratException,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD, ChoixStatutSIC
from admission.ddd.admission.domain.service.i_elements_confirmation import IElementsConfirmation
from admission.ddd.admission.domain.validator.exceptions import (
    NombrePropositionsSoumisesDepasseException,
    QuestionsSpecifiquesChoixFormationNonCompleteesException,
    QuestionsSpecifiquesCurriculumNonCompleteesException,
)
from admission.ddd.admission.enums.question_specifique import Onglets
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.tests import CheckActionLinksMixin
from admission.tests.factories import DoctorateAdmissionFactory, WriteTokenFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.curriculum import EducationalExperienceFactory, EducationalExperienceYearFactory
from admission.tests.factories.form_item import (
    AdmissionFormItemInstantiationFactory,
    TextAdmissionFormItemFactory,
    AdmissionFormItemFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import CandidateFactory, ProgramManagerRoleFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory, _ProcessFactory
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.community import CommunityEnum
from base.models.enums.entity_type import EntityType
from base.tests import QueriesAssertionsMixin
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.views.learning_achievement import update
from infrastructure.financabilite.domain.service.financabilite import PASS_ET_LAS_LABEL
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import FrenchLanguageFactory


@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class DoctorateAdmissionListApiTestCase(QueriesAssertionsMixin, CheckActionLinksMixin, APITestCase):
    @classmethod
    @freezegun.freeze_time('2023-01-01')
    def setUpTestData(cls):
        # Create supervision group members
        cls.promoter = PromoterFactory()
        committee_member = CaMemberFactory(process=cls.promoter.process)

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
            status=ChoixStatutPropositionDoctorale.ANNULEE.name,  # set the status to cancelled so we have access to creation
            training__management_entity=cls.commission,
            supervision_group=cls.promoter.process,
        )
        cls.other_admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
        )
        cls.other_commission = EntityVersionFactory(
            entity_type=EntityType.FACULTY.name,
            acronym='CMC',
        )
        cls.general_education_admission = GeneralEducationAdmissionFactory(
            candidate=cls.admission.candidate,
            training__management_entity=cls.other_commission.entity,
        )
        cls.general_campus_name = (
            cls.general_education_admission.training.educationgroupversion_set.first().root_group.main_teaching_campus.name
        )
        cls.continuing_education_admission = ContinuingEducationAdmissionFactory(
            candidate=cls.admission.candidate,
            training__management_entity=cls.other_commission.entity,
        )
        cls.continuing_campus_name = (
            cls.continuing_education_admission.training.educationgroupversion_set.first().root_group.main_teaching_campus.name
        )

        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate = cls.other_admission.candidate
        cls.no_role_user = PersonFactory().user
        cls.promoter_user = cls.promoter.person.user
        cls.committee_member_user = committee_member.person.user

        cls.url = resolve_url("admission_api_v1:propositions")

    def test_list_propositions_candidate_for_global_links(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response data
        self.assertTrue('links' in response.data)

        self.assertActionLinks(
            response.data['links'],
            allowed_actions=[
                'create_training_choice',
            ],
            forbidden_actions=[],
        )

    def test_list_propositions_candidate_for_general_education(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response data
        self.assertTrue('general_education_propositions' in response.data)
        self.assertEqual(len(response.data['general_education_propositions']), 1)
        proposition = response.data['general_education_propositions'][0]

        self.assertEqual(proposition['uuid'], str(self.general_education_admission.uuid))
        self.assertEqual(proposition['matricule_candidat'], self.general_education_admission.candidate.global_id)
        self.assertEqual(proposition['prenom_candidat'], self.general_education_admission.candidate.first_name)
        self.assertEqual(proposition['nom_candidat'], self.general_education_admission.candidate.last_name)
        self.assertEqual(proposition['statut'], ChoixStatutPropositionGenerale.EN_BROUILLON.name)

        self.assertDictEqual(
            proposition['formation'],
            {
                'sigle': self.general_education_admission.training.acronym,
                'code': self.general_education_admission.training.partial_acronym,
                'annee': self.general_education_admission.training.academic_year.year,
                'date_debut': self.general_education_admission.training.academic_year.start_date.isoformat(),
                'intitule': self.general_education_admission.training.title,
                'intitule_fr': self.general_education_admission.training.title,
                'intitule_en': self.general_education_admission.training.title_english,
                'campus': self.general_campus_name,
                'type': self.general_education_admission.training.education_group_type.name,
                'code_domaine': self.general_education_admission.training.main_domain.code,
                'campus_inscription': self.general_education_admission.training.enrollment_campus.name,
                'sigle_entite_gestion': self.other_commission.acronym,
                'credits': self.general_education_admission.training.credits,
            },
        )

        self.assertActionLinks(
            proposition['links'],
            allowed_actions=[
                'retrieve_person',
                'retrieve_coordinates',
                'retrieve_secondary_studies',
                'retrieve_curriculum',
                'retrieve_training_choice',
                'retrieve_specific_question',
                'retrieve_accounting',
                'update_person',
                'update_coordinates',
                'update_secondary_studies',
                'update_curriculum',
                'update_training_choice',
                'update_specific_question',
                'update_accounting',
                'submit_proposition',
                'destroy_proposition',
            ],
            forbidden_actions=[
                'retrieve_documents',
                'update_documents',
                'pay_after_submission',
                'pay_after_request',
            ],
        )

    def test_list_propositions_candidate_for_continuing_education(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check continuing education propositions
        self.assertTrue('continuing_education_propositions' in response.data)
        self.assertEqual(len(response.data['continuing_education_propositions']), 1)
        proposition = response.data['continuing_education_propositions'][0]

        self.assertEqual(proposition['uuid'], str(self.continuing_education_admission.uuid))
        self.assertEqual(proposition['matricule_candidat'], self.continuing_education_admission.candidate.global_id)
        self.assertEqual(proposition['prenom_candidat'], self.continuing_education_admission.candidate.first_name)
        self.assertEqual(proposition['nom_candidat'], self.continuing_education_admission.candidate.last_name)
        self.assertEqual(proposition['statut'], ChoixStatutPropositionDoctorale.EN_BROUILLON.name)

        self.assertDictEqual(
            proposition['formation'],
            {
                'sigle': self.continuing_education_admission.training.acronym,
                'code': self.continuing_education_admission.training.partial_acronym,
                'annee': self.continuing_education_admission.training.academic_year.year,
                'date_debut': self.continuing_education_admission.training.academic_year.start_date.isoformat(),
                'intitule': self.continuing_education_admission.training.title,
                'intitule_fr': self.continuing_education_admission.training.title,
                'intitule_en': self.continuing_education_admission.training.title_english,
                'campus': self.continuing_campus_name,
                'type': self.continuing_education_admission.training.education_group_type.name,
                'code_domaine': self.continuing_education_admission.training.main_domain.code,
                'campus_inscription': self.continuing_education_admission.training.enrollment_campus.name,
                'sigle_entite_gestion': self.other_commission.acronym,
                'credits': self.continuing_education_admission.training.credits,
            },
        )

        self.assertActionLinks(
            proposition['links'],
            allowed_actions=[
                'retrieve_person',
                'retrieve_coordinates',
                'retrieve_secondary_studies',
                'retrieve_curriculum',
                'retrieve_training_choice',
                'retrieve_specific_question',
                'update_person',
                'update_coordinates',
                'update_secondary_studies',
                'update_curriculum',
                'update_training_choice',
                'update_specific_question',
                'submit_proposition',
                'destroy_proposition',
            ],
            forbidden_actions=[
                'retrieve_documents',
                'update_documents',
            ],
        )

    def test_list_propositions_candidate_for_doctorate_education(self):
        self.client.force_authenticate(user=self.other_candidate.user)

        response = self.client.get(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check global links
        self.assertActionLinks(
            response.data['links'],
            allowed_actions=[
                'create_training_choice',
            ],
            forbidden_actions=[],
        )

        # Check doctorate proposition
        self.assertTrue('doctorate_propositions' in response.data)
        self.assertEqual(len(response.data['doctorate_propositions']), 1)

        proposition = response.data['doctorate_propositions'][0]

        self.assertTrue('links' in proposition)
        allowed_actions = [
            'retrieve_person',
            'retrieve_coordinates',
            'retrieve_secondary_studies',
            'retrieve_languages',
            'retrieve_project',
            'retrieve_cotutelle',
            'retrieve_supervision',
            'retrieve_curriculum',
            'retrieve_training_choice',
            'destroy_proposition',
            'update_person',
            'update_coordinates',
            'update_secondary_studies',
            'update_languages',
            'update_project',
            'update_cotutelle',
            'update_curriculum',
            'update_training_choice',
            'retrieve_accounting',
            'update_accounting',
            'submit_proposition',
        ]
        forbidden_actions = [
            'retrieve_confirmation',
            'update_confirmation',
            'retrieve_doctoral_training',
            'retrieve_complementary_training',
            'retrieve_course_enrollment',
            'retrieve_jury_preparation',
            'retrieve_documents',
            'update_documents',
        ]

        self.assertActionLinks(proposition['links'], allowed_actions, forbidden_actions)

    def test_list_propositions_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_list_propositions_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_list_supervised_propositions_promoter(self):
        DoctorateAdmissionFactory(
            training__management_entity=self.commission,
            supervision_group=self.promoter.process,
        )
        self.client.force_authenticate(user=self.promoter_user)
        with self.assertNumQueriesLessThan(13):
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
        cls.url = resolve_url("admission_api_v1:project", uuid=cls.admission.uuid)
        cls.dto_url = resolve_url("admission_api_v1:doctorate_propositions", uuid=cls.admission.uuid)

    @patch("osis_document.contrib.fields.FileField._confirm_multiple_upload")
    def test_admission_doctorate_update_using_api_candidate(self, confirm_upload):
        confirm_upload.side_effect = lambda _, value, __: ["550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"] if value else []
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
        response = self.client.get(self.dto_url, format="json")
        self.assertEqual(response.json()['doctorat']['sigle'], self.admission.doctorate.acronym)
        self.assertEqual(response.json()['titre_projet'], "A new title")

    def test_admission_doctorate_update_using_api_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.put(self.url, data=self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_update_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
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
        methods_not_allowed = ['post', 'patch', 'delete']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class DoctorateAdmissionVerifyProjectTestCase(APITestCase):
    @classmethod
    @patch("osis_document.contrib.fields.FileField._confirm_multiple_upload")
    def setUpTestData(cls, confirm_upload):
        confirm_upload.side_effect = lambda _, value, __: ["550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"] if value else []
        cls.admission = DoctorateAdmissionFactory(
            supervision_group=_ProcessFactory(),
            cotutelle=False,
            project_title="title",
            project_abstract="abstract",
            thesis_language=FrenchLanguageFactory(),
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
        'admission.infrastructure.admission.doctorat.preparation.domain.service.promoteur.PromoteurTranslator.est_externe',
        return_value=False,
    )
    def test_verify_project_using_api(self, mock_is_external):
        self.client.force_authenticate(user=self.candidate.user)
        PromoterFactory(process=self.admission.supervision_group)
        CaMemberFactory(process=self.admission.supervision_group)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch(
        'admission.infrastructure.admission.doctorat.preparation.domain.service.promoteur.PromoteurTranslator.est_externe',
        return_value=False,
    )
    def test_verify_project_using_api_without_ca_members_must_fail(self, mock_is_external):
        self.client.force_authenticate(user=self.candidate.user)

        PromoterFactory(process=self.admission.supervision_group, is_reference_promoter=True)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['status_code'], MembreCAManquantException.status_code)

    def test_verify_project_using_api_without_promoter_must_fail(self):
        self.client.force_authenticate(user=self.candidate.user)

        CaMemberFactory(process=self.admission.supervision_group)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        status_codes = [e['status_code'] for e in response.json()]
        self.assertIn(PromoteurManquantException.status_code, status_codes)

    def test_verify_project_using_api_without_reference_promoter_must_fail(self):
        self.client.force_authenticate(user=self.candidate.user)

        CaMemberFactory(process=self.admission.supervision_group)
        CaMemberFactory(process=self.admission.supervision_group)
        PromoterFactory(process=self.admission.supervision_group)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['status_code'], PromoteurDeReferenceManquantException.status_code)

    @mock.patch(
        'admission.infrastructure.admission.doctorat.preparation.domain.service.promoteur.PromoteurTranslator.est_externe',
        return_value=False,
    )
    def test_verify_project_with_specific_questions(self, mock_is_external):
        self.client.force_authenticate(user=self.candidate.user)

        admission = DoctorateAdmission.objects.get(pk=self.admission.pk)

        form_item_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year=self.admission.doctorate.academic_year,
            tab=Onglets.CHOIX_FORMATION.name,
            required=True,
        )

        form_item_instantiation = AdmissionFormItemInstantiation.objects.get(pk=form_item_instantiation.pk)

        # The question is required for this admission and the field is not completed
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        status_codes = [e['status_code'] for e in response.json()]
        self.assertIn(
            QuestionsSpecifiquesChoixFormationNonCompleteesException.status_code,
            status_codes,
        )

        # The question is for this admission but not required
        form_item_instantiation.required = False
        form_item_instantiation.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        status_codes = [e['status_code'] for e in response.json()]
        self.assertNotIn(
            QuestionsSpecifiquesChoixFormationNonCompleteesException.status_code,
            status_codes,
        )

        form_item_instantiation.required = True

        # The question is required but for another year
        form_item_instantiation.academic_year = AcademicYearFactory(
            year=self.admission.doctorate.academic_year.year - 1
        )
        form_item_instantiation.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        status_codes = [e['status_code'] for e in response.json()]
        self.assertNotIn(
            QuestionsSpecifiquesChoixFormationNonCompleteesException.status_code,
            status_codes,
        )

        form_item_instantiation.academic_year = self.admission.doctorate.academic_year
        form_item_instantiation.save()

        # The question if for this admission but not active
        form_item_instantiation.form_item.active = False
        form_item_instantiation.form_item.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        status_codes = [e['status_code'] for e in response.json()]
        self.assertNotIn(
            QuestionsSpecifiquesChoixFormationNonCompleteesException.status_code,
            status_codes,
        )

        form_item_instantiation.form_item.active = True
        form_item_instantiation.form_item.save()

        # Required question for this admission but in unchecked tab
        form_item_instantiation.tab = Onglets.CURRICULUM.name
        form_item_instantiation.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        status_codes = [e['status_code'] for e in response.json()]
        self.assertNotIn(
            QuestionsSpecifiquesChoixFormationNonCompleteesException.status_code,
            status_codes,
        )

        form_item_instantiation.tab = Onglets.CHOIX_FORMATION.name
        form_item_instantiation.save()

        # The question is required for this admission and the field is completed
        admission.specific_question_answers = {'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response.'}
        admission.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        status_codes = [e['status_code'] for e in response.json()]
        self.assertNotIn(
            QuestionsSpecifiquesChoixFormationNonCompleteesException.status_code,
            status_codes,
        )

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


@freezegun.freeze_time('2020-12-15')
class DoctorateAdmissionSubmitPropositionTestCase(APITestCase):
    @classmethod
    @patch("osis_document.contrib.fields.FileField._confirm_multiple_upload")
    def setUpTestData(cls, confirm_upload):
        AdmissionAcademicCalendarFactory.produce_all_required()
        language_fr = FrenchLanguageFactory()

        confirm_upload.side_effect = lambda _, value, __: ["550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"] if value else []
        # Create candidates
        # Complete candidate
        cls.first_candidate = CompletePersonFactory()
        cls.first_candidate.id_photo = [WriteTokenFactory().token]
        cls.first_candidate.id_card = [WriteTokenFactory().token]
        cls.first_candidate.passport = [WriteTokenFactory().token]
        cls.first_candidate.curriculum = [WriteTokenFactory().token]
        cls.first_candidate.save()
        experience = EducationalExperienceFactory(
            person_id=cls.first_candidate.pk,
            education_name='A custom education',
            country__iso_code="BE",
            obtained_diploma=True,
            transcript=['transcript.pdf'],
        )
        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=AcademicYearFactory(year=get_current_year()),
        )
        # Incomplete candidate
        cls.second_candidate = PersonFactory(first_name="Jim")
        # Create promoters
        cls.first_invited_promoter = PromoterFactory(actor_ptr__person__first_name="Joe", is_reference_promoter=True)
        cls.first_invited_promoter.actor_ptr.switch_state(SignatureState.APPROVED)
        cls.first_not_invited_promoter = PromoterFactory(actor_ptr__person__first_name="Jack")
        cls.first_ca_member = CaMemberFactory(process=cls.first_invited_promoter.actor_ptr.process)
        cls.first_ca_member.actor_ptr.switch_state(SignatureState.APPROVED)
        cls.second_ca_member = CaMemberFactory(process=cls.first_invited_promoter.actor_ptr.process)
        cls.second_ca_member.actor_ptr.switch_state(SignatureState.APPROVED)
        cls.second_invited_promoter = PromoterFactory(actor_ptr__person__first_name="Jim")
        cls.second_invited_promoter.actor_ptr.switch_state(SignatureState.INVITED)

        # Create admissions
        cls.first_admission_with_invitation = DoctorateAdmissionFactory(
            candidate=cls.first_candidate,
            status=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
            supervision_group=cls.first_invited_promoter.actor_ptr.process,
            thesis_language=language_fr,
        )
        cls.first_admission_without_invitation = DoctorateAdmissionFactory(
            candidate=cls.first_candidate,
            supervision_group=cls.first_not_invited_promoter.actor_ptr.process,
            thesis_language=language_fr,
        )
        cls.second_admission = DoctorateAdmissionFactory(
            candidate=cls.second_candidate,
            status=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
            supervision_group=cls.second_invited_promoter.actor_ptr.process,
            thesis_language=language_fr,
        )
        # Create other users
        cls.no_role_user = PersonFactory(first_name="Joe").user

        # Create required specific questions
        AdmissionFormItemFactory(internal_label=PASS_ET_LAS_LABEL)

        # Targeted urls
        cls.first_admission_with_invitation_url = resolve_url(
            "admission_api_v1:submit-doctoral-proposition",
            uuid=cls.first_admission_with_invitation.uuid,
        )
        cls.first_admission_without_invitation_url = resolve_url(
            "admission_api_v1:submit-doctoral-proposition",
            uuid=cls.first_admission_without_invitation.uuid,
        )
        cls.second_admission_url = resolve_url(
            "admission_api_v1:submit-doctoral-proposition",
            uuid=cls.second_admission.uuid,
        )

        cls.submitted_data = {
            'pool': AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT.name,
            'annee': 2020,
            'elements_confirmation': {
                'reglement_doctorat': IElementsConfirmation.REGLEMENT_DOCTORAT,
                'reglement_doctorat_deontologie': IElementsConfirmation.REGLEMENT_DOCTORAT_DEONTOLOGIE,
                'protection_donnees': IElementsConfirmation.PROTECTION_DONNEES,
                'professions_reglementees': IElementsConfirmation.PROFESSIONS_REGLEMENTEES,
                'justificatifs': IElementsConfirmation.JUSTIFICATIFS % {'by_service': _("by the Enrolment Office")},
                'declaration_sur_lhonneur': IElementsConfirmation.DECLARATION_SUR_LHONNEUR
                % {'to_service': _("to the UCLouvain Registration Service")},
            },
        }

    def assertInErrors(self, response, exception):
        errors = response.json().get('non_field_errors', [])
        self.assertTrue(any(exc for exc in errors if exc['status_code'] == exception.status_code))

    def assertNotInErrors(self, response, exception):
        errors = response.json().get('non_field_errors', [])
        self.assertFalse(any(exc for exc in errors if exc['status_code'] == exception.status_code))

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.first_candidate.user)
        methods_not_allowed = ['patch', 'put', 'delete']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.first_admission_with_invitation_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, f"{method} is allowed")

    def test_verify_valid_proposition_using_api(self):
        self.client.force_authenticate(user=self.first_candidate.user)

        response = self.client.get(self.first_admission_with_invitation_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["errors"]), 0)

    def test_verify_invalid_proposition_using_api(self):
        self.client.force_authenticate(user=self.second_candidate.user)

        response = self.client.get(self.second_admission_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.json()) > 0)

    def test_verify_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.first_admission_with_invitation_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_verify_no_invited_promoters(self):
        self.client.force_authenticate(user=self.first_candidate.user)
        response = self.client.get(self.first_admission_without_invitation_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_other_candidate(self):
        self.client.force_authenticate(user=self.second_candidate.user)
        response = self.client.get(self.first_admission_with_invitation_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.first_admission_with_invitation_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_submit_valid_proposition_using_api(self):
        admission = DoctorateAdmissionFactory(
            training__academic_year__current=True,
            candidate=self.first_candidate,
            status=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
            supervision_group=self.first_invited_promoter.actor_ptr.process,
        )
        manager = ProgramManagerRoleFactory(education_group_id=admission.training.education_group_id)

        self.client.force_authenticate(user=self.first_candidate.user)

        url = resolve_url("admission_api_v1:submit-doctoral-proposition", uuid=admission.uuid)
        response = self.client.post(url, self.submitted_data)

        updated_admission: DoctorateAdmission = DoctorateAdmission.objects.get(uuid=admission.uuid)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('uuid'), str(admission.uuid))

        self.assertEqual(updated_admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)
        self.assertEqual(updated_admission.status_sic, ChoixStatutCDD.TO_BE_VERIFIED.name)
        self.assertEqual(updated_admission.status_cdd, ChoixStatutSIC.TO_BE_VERIFIED.name)
        self.assertEqual(updated_admission.post_enrolment_status, ChoixStatutDoctorat.ADMISSION_IN_PROGRESS.name)
        self.assertEqual(updated_admission.last_update_author, self.first_candidate)

        self.assertEqual(updated_admission.submitted_at.date(), datetime.date.today())
        self.assertEqual(
            updated_admission.submitted_profile,
            {
                'identification': {
                    'first_name': self.first_candidate.first_name,
                    'last_name': self.first_candidate.last_name,
                    'gender': self.first_candidate.gender,
                    'country_of_citizenship': self.first_candidate.country_of_citizenship.iso_code,
                    'date_of_birth': self.first_candidate.birth_date.isoformat(),
                },
                'coordinates': {
                    'country': 'BE',
                    'postal_code': '1348',
                    'city': 'Louvain-la-Neuve',
                    'street': 'University street',
                    'street_number': '2',
                    'postal_box': 'B2',
                },
            },
        )
        self.assertEqual(WebNotification.objects.count(), 1)
        self.assertEqual(WebNotification.objects.first().person, manager.person)

        admission_tasks = AdmissionTask.objects.filter(admission=admission).order_by('type')
        self.assertEqual(len(admission_tasks), 2)
        self.assertEqual(admission_tasks[0].type, AdmissionTask.TaskType.DOCTORATE_MERGE.name)
        self.assertEqual(admission_tasks[1].type, AdmissionTask.TaskType.DOCTORATE_RECAP.name)

        history_entry = HistoryEntry.objects.filter(object_uuid=admission.uuid).first()
        self.assertIsNotNone(history_entry)
        self.assertCountEqual(history_entry.tags, ['proposition', 'status-changed', 'soumission'])

    def test_submit_valid_proposition_using_api_but_too_much_submitted_propositions(self):
        DoctorateAdmissionFactory(
            training__academic_year__current=True,
            candidate=self.first_candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            supervision_group=self.first_invited_promoter.actor_ptr.process,
        )

        admission = DoctorateAdmissionFactory(
            training__academic_year__current=True,
            candidate=self.first_candidate,
            status=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
            supervision_group=self.first_invited_promoter.actor_ptr.process,
        )

        self.client.force_authenticate(user=self.first_candidate.user)

        url = resolve_url("admission_api_v1:submit-doctoral-proposition", uuid=admission.uuid)
        response = self.client.post(url, self.submitted_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        ret = response.json()
        self.assertIn(
            NombrePropositionsSoumisesDepasseException.status_code, [e["status_code"] for e in ret['non_field_errors']]
        )

    def test_submit_invalid_proposition_using_api(self):
        admission = DoctorateAdmissionFactory(
            candidate=self.second_candidate,
            status=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
            supervision_group=self.first_invited_promoter.actor_ptr.process,
        )

        self.client.force_authenticate(user=self.second_candidate.user)

        url = resolve_url("admission_api_v1:submit-doctoral-proposition", uuid=admission.uuid)
        response = self.client.post(url, self.submitted_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.json().get('non_field_errors'))

    def test_submit_invalid_proposition_using_api_accounting(self):
        admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
            supervision_group=self.first_invited_promoter.actor_ptr.process,
        )
        url = resolve_url("admission_api_v1:submit-doctoral-proposition", uuid=admission.uuid)

        self.client.force_authenticate(user=admission.candidate.user)

        # No academic experience -> the absence of debt certificate is not required
        response = self.client.post(url, self.submitted_data)
        self.assertNotInErrors(response, AbsenceDeDetteNonCompleteeDoctoratException)

        # Experience in a french speaking community institute -> the absence of debt certificate is required
        experience = EducationalExperienceFactory(
            person=admission.candidate,
            obtained_diploma=False,
            country=CountryFactory(iso_code="BE"),
            institute=OrganizationFactory(
                community=CommunityEnum.FRENCH_SPEAKING.name,
                acronym='INSTITUTE',
                name='First institute',
            ),
        )
        experience_year = EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=AcademicYearFactory(year=get_current_year()),
        )

        response = self.client.post(url, self.submitted_data)
        self.assertInErrors(response, AbsenceDeDetteNonCompleteeDoctoratException)

        # Experience in UCL -> the absence of debt certificate is not required
        experience.institute.acronym = "UCL"
        experience.institute.save()

        response = self.client.post(url, self.submitted_data)
        self.assertNotInErrors(response, AbsenceDeDetteNonCompleteeDoctoratException)

        # Experience in a german speaking community institute -> the absence of debt certificate is not required
        experience.institute.acronym = "INSTITUTE"
        experience.institute.community = CommunityEnum.GERMAN_SPEAKING.name
        experience.institute.save()

        response = self.client.post(url, self.submitted_data)
        self.assertNotInErrors(response, AbsenceDeDetteNonCompleteeDoctoratException)

        # Too old experience in a french speaking community institute -> the absence of debt certificate is not required
        experience.institute.community = CommunityEnum.FRENCH_SPEAKING.name
        experience.institute.save()

        experience_year.academic_year = AcademicYearFactory(year=2000)
        experience_year.save()

        response = self.client.post(url, self.submitted_data)
        self.assertNotInErrors(response, AbsenceDeDetteNonCompleteeDoctoratException)

    @mock.patch(
        'admission.infrastructure.admission.doctorat.preparation.domain.service.promoteur.PromoteurTranslator.est_externe',
        return_value=False,
    )
    def test_submit_invalid_proposition_using_api_specific_questions(self, mock_is_external):
        admission = DoctorateAdmissionFactory(
            training__academic_year__current=True,
            candidate=self.first_candidate,
            status=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
            supervision_group=self.first_invited_promoter.actor_ptr.process,
        )
        self.client.force_authenticate(user=admission.candidate.user)

        admission = DoctorateAdmission.objects.get(pk=admission.pk)

        url = resolve_url("admission_api_v1:submit-doctoral-proposition", uuid=admission.uuid)

        form_item_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year=admission.doctorate.academic_year,
            tab=Onglets.CURRICULUM.name,
            required=True,
        )

        form_item_instantiation = AdmissionFormItemInstantiation.objects.get(pk=form_item_instantiation.pk)

        # The question is required for this admission and the field is not completed
        response = self.client.post(url, self.submitted_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertInErrors(response, QuestionsSpecifiquesCurriculumNonCompleteesException)

        # Required question for this admission but in unchecked tab
        form_item_instantiation.tab = Onglets.CHOIX_FORMATION.name
        form_item_instantiation.save()

        response = self.client.post(url, self.submitted_data)
        self.assertNotInErrors(response, QuestionsSpecifiquesCurriculumNonCompleteesException)

        form_item_instantiation.tab = Onglets.CURRICULUM.name
        form_item_instantiation.save()

        # The question is required for this admission and the field is completed
        admission.specific_question_answers = {'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response.'}
        admission.save()

        response = self.client.post(url, self.submitted_data)
        self.assertNotInErrors(response, QuestionsSpecifiquesCurriculumNonCompleteesException)
