# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import patch

from django.db import connection
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models import (
    GeneralEducationAdmission,
    ContinuingEducationAdmission,
    AdmissionType,
    DoctorateAdmission,
)
from admission.contrib.models.doctorate import REFERENCE_SEQ_NAME
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    DoctoratNonTrouveException,
    MaximumPropositionsAtteintException,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.domain.validator.exceptions import BourseNonTrouveeException
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_continue.domain.validator import exceptions as continuing_education_exceptions
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.validator import exceptions as general_education_exceptions
from admission.ddd.admission.doctorat.preparation.domain.validator import exceptions as doctorate_education_exceptions
from admission.tests.api.views.test_project import DoctorateAdmissionApiTestCase
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.continuing_education import (
    ContinuingEducationTrainingFactory,
    ContinuingEducationAdmissionFactory,
)
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.form_item import (
    TextAdmissionFormItemFactory,
    DocumentAdmissionFormItemFactory,
    AdmissionFormItemInstantiationFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.scholarship import (
    ErasmusMundusScholarshipFactory,
    InternationalScholarshipFactory,
    DoubleDegreeScholarshipFactory,
)
from base.models.enums.entity_type import EntityType
from base.tests.factories.education_group_year import Master120TrainingFactory
from base.tests.factories.entity_version import EntityVersionFactory

from base.tests.factories.person import PersonFactory


def create_default_propositions_in_progress(candidate):
    DoctorateAdmissionFactory(candidate=candidate, status=ChoixStatutPropositionDoctorale.IN_PROGRESS.name)
    DoctorateAdmissionFactory(candidate=candidate, status=ChoixStatutPropositionDoctorale.SIGNING_IN_PROGRESS.name)
    GeneralEducationAdmissionFactory(candidate=candidate, status=ChoixStatutPropositionGenerale.IN_PROGRESS.name)
    GeneralEducationAdmissionFactory(candidate=candidate, status=ChoixStatutPropositionGenerale.IN_PROGRESS.name)
    ContinuingEducationAdmissionFactory(candidate=candidate, status=ChoixStatutPropositionContinue.IN_PROGRESS.name)


class DoctorateAdmissionTrainingChoiceInitializationApiTestCase(APITestCase):
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
        cls.scholarship = ErasmusMundusScholarshipFactory()

        cls.create_data = {
            "type_admission": AdmissionType.PRE_ADMISSION.name,
            "justification": "Some justification",
            "sigle_formation": cls.doctorate.acronym,
            "annee_formation": cls.doctorate.academic_year.year,
            "matricule_candidat": cls.candidate.global_id,
            "commission_proximite": '',
            "bourse_erasmus_mundus": cls.scholarship.uuid,
        }
        cls.url = resolve_url("admission_api_v1:doctorate_training_choice")
        cls.list_url = resolve_url("admission_api_v1:propositions")

    def test_admission_doctorate_creation_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        with connection.cursor() as cursor:
            cursor.execute("SELECT last_value FROM %(sequence)s" % {'sequence': REFERENCE_SEQ_NAME})
            seq_value = cursor.fetchone()[0]
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)
        first_admission = admissions[0]
        first_admission.status = ChoixStatutPropositionDoctorale.CANCELLED.name
        first_admission.save()
        admission = admissions.get(uuid=response.data["uuid"])
        self.assertEqual(admission.type, self.create_data["type_admission"])
        self.assertEqual(admission.comment, self.create_data["justification"])
        self.assertEqual(admission.erasmus_mundus_scholarship_id, self.scholarship.pk)

        response = self.client.get(self.list_url, format="json")
        self.assertEqual(response.json()['doctorate_propositions'][0]["doctorat"]['sigle'], self.doctorate.acronym)
        self.assertEqual(
            admission.reference,
            '{}-{}'.format(
                self.doctorate.academic_year.year % 100,
                300000 + seq_value + 1,
            ),
        )

    def test_admission_doctorate_creation_using_api_with_wrong_doctorate(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, "sigle_formation": "UNKONWN"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], DoctoratNonTrouveException.status_code)

    def test_admission_doctorate_creation_using_api_with_wrong_scholarship(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, 'bourse_erasmus_mundus': str(uuid.uuid4())}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], BourseNonTrouveeException.status_code)

    def test_admission_doctorate_creation_using_api_with_too_much_propositions_in_parallel(self):
        self.client.force_authenticate(user=self.candidate.user)
        create_default_propositions_in_progress(candidate=self.candidate)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GeneralEducationAdmissionTrainingChoiceInitializationApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        cls.training = Master120TrainingFactory()
        cls.erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory()
        cls.international_scholarship = InternationalScholarshipFactory()
        cls.double_degree_scholarship = DoubleDegreeScholarshipFactory()
        AdmissionAcademicCalendarFactory.produce_all_required()

        cls.create_data = {
            'sigle_formation': cls.training.acronym,
            'annee_formation': cls.training.academic_year.year,
            'matricule_candidat': cls.candidate.global_id,
            'bourse_erasmus_mundus': str(cls.erasmus_mundus_scholarship.uuid),
            'bourse_internationale': str(cls.international_scholarship.uuid),
            'bourse_double_diplome': str(cls.double_degree_scholarship.uuid),
        }

        cls.url = resolve_url('admission_api_v1:general_training_choice')

    def test_training_choice_initialization_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        admissions: QuerySet[GeneralEducationAdmission] = GeneralEducationAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)

        admission = admissions.get(uuid=response.data['uuid'])
        self.assertEqual(admission.training_id, self.training.pk)
        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.international_scholarship_id, self.international_scholarship.pk)
        self.assertEqual(admission.erasmus_mundus_scholarship_id, self.erasmus_mundus_scholarship.pk)
        self.assertEqual(admission.double_degree_scholarship_id, self.double_degree_scholarship.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionGenerale.IN_PROGRESS.name)

    def test_training_choice_initialization_using_api_candidate_with_wrong_training(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, 'sigle_formation': 'UNKNOWN'}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            general_education_exceptions.FormationNonTrouveeException.status_code,
        )

    def test_training_choice_initialization_using_api_candidate_with_wrong_scholarship(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, 'bourse_erasmus_mundus': str(uuid.uuid4())}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], BourseNonTrouveeException.status_code)

    def test_training_choice_initialization_using_api_candidate_with_too_much_propositions_in_parallel(self):
        self.client.force_authenticate(user=self.candidate.user)
        create_default_propositions_in_progress(candidate=self.candidate)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ContinuingEducationAdmissionTrainingChoiceInitializationApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        cls.training = ContinuingEducationTrainingFactory()
        cls.create_data = {
            'sigle_formation': cls.training.acronym,
            'annee_formation': cls.training.academic_year.year,
            'matricule_candidat': cls.candidate.global_id,
        }

        cls.url = resolve_url('admission_api_v1:continuing_training_choice')

    def test_training_choice_initialization_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        admissions: QuerySet[ContinuingEducationAdmission] = ContinuingEducationAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)

        admission = admissions.get(uuid=response.data['uuid'])
        self.assertEqual(admission.training_id, self.training.pk)
        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionContinue.IN_PROGRESS.name)

    def test_training_choice_initialization_using_api_candidate_with_wrong_training(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, 'sigle_formation': 'UNKNOWN'}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            continuing_education_exceptions.FormationNonTrouveeException.status_code,
        )

    def test_training_choice_initialization_using_api_candidate_with_too_much_propositions_in_parallel(self):
        self.client.force_authenticate(user=self.candidate.user)
        create_default_propositions_in_progress(candidate=self.candidate)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class GeneralEducationAdmissionTrainingChoiceUpdateApiTestCase(APITestCase):
    file_uuid = str(uuid.uuid4())

    @classmethod
    def setUpTestData(cls):
        cls.admission = GeneralEducationAdmissionFactory()
        cls.candidate = cls.admission.candidate
        cls.training = Master120TrainingFactory()
        cls.erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory()
        cls.international_scholarship = InternationalScholarshipFactory()
        cls.double_degree_scholarship = DoubleDegreeScholarshipFactory()

        cls.update_data = {
            'sigle_formation': cls.training.acronym,
            'annee_formation': cls.training.academic_year.year,
            'uuid_proposition': cls.admission.uuid,
            'bourse_erasmus_mundus': str(cls.erasmus_mundus_scholarship.uuid),
            'bourse_internationale': str(cls.international_scholarship.uuid),
            'bourse_double_diplome': str(cls.double_degree_scholarship.uuid),
            'reponses_questions_specifiques': {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
                'fe254203-17c7-47d6-95e4-3c5c532da552': [cls.file_uuid, 'token:abcdef'],
            },
        }

        AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year=cls.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da552'),
                internal_label='document_item_1',
            ),
            academic_year=cls.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da553'),
                active=False,
                internal_label='document_item_2',
            ),
            academic_year=cls.training.academic_year,
        )

        cls.url = resolve_url('admission_api_v1:general_training_choice', uuid=str(cls.admission.uuid))

    def setUp(self) -> None:
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)

    def test_training_choice_update_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data=self.update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        admissions: QuerySet[GeneralEducationAdmission] = GeneralEducationAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)

        admission = admissions.get(uuid=response.data['uuid'])
        self.assertEqual(admission.training_id, self.training.pk)
        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.international_scholarship_id, self.international_scholarship.pk)
        self.assertEqual(admission.erasmus_mundus_scholarship_id, self.erasmus_mundus_scholarship.pk)
        self.assertEqual(admission.double_degree_scholarship_id, self.double_degree_scholarship.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionGenerale.IN_PROGRESS.name)
        expected = {
            'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
            'fe254203-17c7-47d6-95e4-3c5c532da552': [self.file_uuid, '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'],
        }
        self.assertEqual(admission.specific_question_answers, expected)

    def test_training_choice_update_using_api_candidate_with_wrong_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'uuid_proposition': str(uuid.uuid4())}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            general_education_exceptions.PropositionNonTrouveeException.status_code,
        )

    def test_training_choice_update_using_api_candidate_with_wrong_training(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'sigle_formation': 'UNKNOWN'}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            general_education_exceptions.FormationNonTrouveeException.status_code,
        )

    def test_training_choice_update_using_api_candidate_with_wrong_scholarship(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'bourse_erasmus_mundus': str(uuid.uuid4())}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], BourseNonTrouveeException.status_code)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class ContinuingEducationAdmissionTrainingChoiceUpdateApiTestCase(APITestCase):
    file_uuid = str(uuid.uuid4())

    @classmethod
    def setUpTestData(cls):
        cls.admission = ContinuingEducationAdmissionFactory()
        cls.candidate = cls.admission.candidate
        cls.training = ContinuingEducationTrainingFactory()

        cls.update_data = {
            'sigle_formation': cls.training.acronym,
            'annee_formation': cls.training.academic_year.year,
            'uuid_proposition': cls.admission.uuid,
            'reponses_questions_specifiques': {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
                'fe254203-17c7-47d6-95e4-3c5c532da552': [cls.file_uuid, 'token:abcdef'],
            },
        }

        AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year=cls.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da552'),
                internal_label='document_item_1',
            ),
            academic_year=cls.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da553'),
                active=False,
                internal_label='document_item_2',
            ),
            academic_year=cls.training.academic_year,
        )

        cls.url = resolve_url('admission_api_v1:continuing_training_choice', uuid=str(cls.admission.uuid))

    def setUp(self) -> None:
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)

    def test_training_choice_update_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data=self.update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        admissions: QuerySet[ContinuingEducationAdmission] = ContinuingEducationAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)

        admission = admissions.get(uuid=response.data['uuid'])
        self.assertEqual(admission.training_id, self.training.pk)
        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionContinue.IN_PROGRESS.name)
        expected = {
            'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
            'fe254203-17c7-47d6-95e4-3c5c532da552': [self.file_uuid, '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'],
        }
        self.assertEqual(admission.specific_question_answers, expected)

    def test_training_choice_update_using_api_candidate_with_wrong_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'uuid_proposition': str(uuid.uuid4())}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            continuing_education_exceptions.PropositionNonTrouveeException.status_code,
        )

    def test_training_choice_update_using_api_candidate_with_wrong_training(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'sigle_formation': 'UNKNOWN'}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            continuing_education_exceptions.FormationNonTrouveeException.status_code,
        )

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DoctorateEducationAdmissionTypeUpdateApiTestCase(DoctorateAdmissionApiTestCase):
    file_uuid = str(uuid.uuid4())

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory()
        cls.update_data = {
            'uuid_proposition': cls.admission.uuid,
            'type_admission': AdmissionType.PRE_ADMISSION.name,
            'justification': 'Justification',
            'bourse_erasmus_mundus': str(cls.erasmus_mundus_scholarship.uuid),
            'reponses_questions_specifiques': {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
                'fe254203-17c7-47d6-95e4-3c5c532da552': [cls.file_uuid, 'token:abcdef'],
            },
        }

        AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year=cls.admission.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da552'),
                internal_label='document_item_1',
            ),
            academic_year=cls.admission.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da553'),
                active=False,
                internal_label='document_item_2',
            ),
            academic_year=cls.admission.training.academic_year,
        )

        cls.url = resolve_url('admission_api_v1:doctorate_admission_type_update', uuid=str(cls.admission.uuid))

    def setUp(self) -> None:
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)

    def test_admission_type_update_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data=self.update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)
        admission: DoctorateAdmission = admissions.get(uuid=response.data['uuid'])

        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionDoctorale.IN_PROGRESS.name)
        self.assertEqual(admission.type, AdmissionType.PRE_ADMISSION.name)
        self.assertEqual(admission.comment, 'Justification')
        self.assertEqual(admission.erasmus_mundus_scholarship_id, self.erasmus_mundus_scholarship.pk)
        expected = {
            'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
            'fe254203-17c7-47d6-95e4-3c5c532da552': [self.file_uuid, '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'],
        }
        self.assertEqual(admission.specific_question_answers, expected)

    def test_admission_type_update_using_api_candidate_with_wrong_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'uuid_proposition': str(uuid.uuid4())}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            doctorate_education_exceptions.PropositionNonTrouveeException.status_code,
        )

    def test_admission_type_update_using_api_candidate_with_wrong_scholarship(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'bourse_erasmus_mundus': str(uuid.uuid4())}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], BourseNonTrouveeException.status_code)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
