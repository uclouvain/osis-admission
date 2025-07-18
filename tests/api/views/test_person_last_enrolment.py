# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

import freezegun
from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.models import ContinuingEducationAdmission, GeneralEducationAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.person import PersonFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
@freezegun.freeze_time('2020-01-01 12:00:00')
class PersonLastEnrolmentTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.agnostic_url = resolve_url('person_last_enrolment')
        cls.updated_data = {
            'last_registration_id': '',
            'last_registration_year': None,
        }
        cls.doctoral_commission = EntityFactory()
        cls.candidate_user_without_admission = CandidateFactory().person.user
        cls.no_role_user = PersonFactory(first_name='Joe').user
        AdmissionAcademicCalendarFactory.produce_all_required()

    def setUp(self):
        super().setUp()

        promoter = PromoterFactory(actor_ptr__person__first_name='Jane')
        self.promoter_user = promoter.person.user
        self.committee_member_user = CaMemberFactory(
            actor_ptr__person__first_name='James',
            process=promoter.process,
        ).person.user
        self.admission = DoctorateAdmissionFactory(
            candidate__first_name='John',
            training__management_entity=self.doctoral_commission,
        )
        self.admission_url = resolve_url('doctorate_person_last_enrolment', uuid=self.admission.uuid)
        self.candidate_user = self.admission.candidate.user

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.agnostic_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(self.admission_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate_user)
        methods_not_allowed = ['delete', 'post', 'patch', 'get']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.admission_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_person_last_enrolment_update_no_role(self):
        self.client.force_authenticate(self.no_role_user)
        response = self.client.put(self.agnostic_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        response = self.client.put(self.admission_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())

    def test_person_last_enrolment__with_candidate_depending_on_admission_statuses(self):
        self.client.force_authenticate(self.candidate_user)

        valid_statuses_on_update = {
            ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
        }

        other_admission = DoctorateAdmissionFactory(
            candidate=self.candidate_user.person,
        )
        other_admission_url = resolve_url('doctorate_person_last_enrolment', uuid=other_admission.uuid)

        for current_status in ChoixStatutPropositionDoctorale:
            other_admission.status = current_status.name
            other_admission.save(update_fields=['status'])

            response = self.client.put(other_admission_url, self.updated_data)
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK if current_status.name in valid_statuses_on_update else status.HTTP_403_FORBIDDEN,
            )

    def test_person_last_enrolment_with_candidate_not_depending_on_other_doctorate_admissions(self):
        self.client.force_authenticate(self.candidate_user)

        other_admission = DoctorateAdmissionFactory(
            candidate=self.candidate_user.person,
            status=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
        )

        response = self.client.put(self.admission_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(self.agnostic_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_person_last_enrolment_update_candidate(self):
        self.client.force_authenticate(self.candidate_user_without_admission)
        response = self.client.put(self.agnostic_url, self.updated_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(response.json()['last_registration_id'], '')
        self.assertEqual(response.json()['last_registration_year'], None)

        self.candidate_user_without_admission.person.refresh_from_db()
        self.assertEqual(self.candidate_user_without_admission.person.last_registration_id, '')
        self.assertEqual(self.candidate_user_without_admission.person.last_registration_year, None)

        self.client.force_authenticate(self.candidate_user)
        response = self.client.put(
            self.admission_url,
            {
                'last_registration_id': '12345678',
                'last_registration_year': self.admission.training.academic_year.year,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(response.json()['last_registration_id'], '12345678')
        self.assertEqual(response.json()['last_registration_year'], self.admission.training.academic_year.year)

        self.candidate_user.person.refresh_from_db()
        self.assertEqual(self.candidate_user.person.last_registration_id, '12345678')
        self.assertEqual(self.candidate_user.person.last_registration_year, self.admission.training.academic_year)

        self.admission.refresh_from_db()
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.admission.last_update_author, self.candidate_user.person)

    def test_person_last_enrolment_update_promoter(self):
        self.client.force_authenticate(self.promoter_user)
        response = self.client.put(self.agnostic_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(response.json()['last_registration_id'], '')

        response = self.client.put(self.admission_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())

    def test_person_last_enrolment_update_committee_member(self):
        self.client.force_authenticate(self.committee_member_user)
        response = self.client.put(self.agnostic_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(response.json()['last_registration_id'], '')

        response = self.client.put(self.admission_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())

    def test_person_last_enrolment_update_candidate_with_general_admission(self):
        self.client.force_authenticate(self.candidate_user)
        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=self.candidate_user.person,
        )
        admission_url = resolve_url('general_person_last_enrolment', uuid=general_admission.uuid)
        response = self.client.put(admission_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        general_admission.refresh_from_db()
        self.assertEqual(general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(general_admission.last_update_author, self.candidate_user.person)

    def test_person_last_enrolment_update_candidate_with_continuing_admission(self):
        self.client.force_authenticate(self.candidate_user)
        continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            candidate=self.candidate_user.person,
        )
        admission_url = resolve_url('continuing_person_last_enrolment', uuid=continuing_admission.uuid)
        response = self.client.put(admission_url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        continuing_admission.refresh_from_db()
        self.assertEqual(continuing_admission.modified_at, datetime.datetime.now())
        self.assertEqual(continuing_admission.last_update_author, self.candidate_user.person)
