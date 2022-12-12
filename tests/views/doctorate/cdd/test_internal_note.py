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
import datetime
from typing import List, Optional

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework import status

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.doctorate import InternalNote
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE, ENTITY_CDSS
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.internal_note import InternalNoteFactory
from admission.tests.factories.roles import CddManagerFactory, DoctorateReaderRoleFactory
from admission.tests.factories.supervision import PromoterFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory


class InternalNoteTestCase(TestCase):
    first_admission: Optional[DoctorateAdmission] = None
    second_admission: Optional[DoctorateAdmission] = None

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.user = User.objects.create_user(
            username='john_doe',
            password='top_secret',
        )

        # Create an academic year
        academic_year = AcademicYearFactory(year=2021)

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(
            entity=first_doctoral_commission,
            acronym=ENTITY_CDE,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        )

        second_doctoral_commission = EntityFactory()
        EntityVersionFactory(
            entity=second_doctoral_commission,
            acronym=ENTITY_CDSS,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        )

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create admissions
        cls.first_admission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_year,
            cotutelle=False,
            supervision_group=promoter.process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            pre_admission_submission_date=datetime.datetime.now(),
        )
        cls.second_admission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_year,
            cotutelle=False,
            supervision_group=promoter.process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            pre_admission_submission_date=datetime.datetime.now(),
        )

        # Cdd user
        cdd_person_person = CddManagerFactory(entity=first_doctoral_commission).person
        cls.one_cdd_user = cdd_person_person.user

        cls.doctorate_reader_user = DoctorateReaderRoleFactory().person.user

        # Targeted url
        cls.url = reverse('admission:doctorate:internal-note', args=[cls.first_admission.uuid])

    def setUp(self) -> None:
        # Create internal notes
        self.first_admission_note_1 = InternalNoteFactory(
            admission=self.first_admission,
            author=self.one_cdd_user.person,
            text='T11',
        )
        self.first_admission_note_2 = InternalNoteFactory(
            admission=self.first_admission,
            author=self.one_cdd_user.person,
            text='T12',
        )
        self.second_admission_note_1 = InternalNoteFactory(
            admission=self.second_admission,
            author=self.one_cdd_user.person,
            text='T21',
        )

    def test_get_with_user_without_person_is_forbidden(self):
        self.client.force_login(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_with_candidate_user_is_forbidden(self):
        self.client.force_login(user=self.first_admission.candidate.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_with_doctorate_reader_is_allowed(self):
        self.client.force_login(user=self.doctorate_reader_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_with_doctorate_reader_is_forbidden(self):
        self.client.force_login(user=self.doctorate_reader_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_with_cdd_user_retrieves_previous_notes(self):
        self.client.force_login(user=self.one_cdd_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        internal_notes = response.context.get('internal_notes')

        self.assertEqual(len(internal_notes), 2)
        first_note = {
            'author__first_name': self.first_admission_note_2.author.first_name,
            'author__last_name': self.first_admission_note_2.author.last_name,
            'created': self.first_admission_note_2.created,
            'text': self.first_admission_note_2.text,
        }
        self.assertEqual(internal_notes[0], first_note)
        second_note = {
            'author__first_name': self.first_admission_note_1.author.first_name,
            'author__last_name': self.first_admission_note_1.author.last_name,
            'created': self.first_admission_note_1.created,
            'text': self.first_admission_note_1.text,
        }
        self.assertEqual(internal_notes[1], second_note)

        self.assertIn('form', response.context.keys())

    def test_post_with_cdd_user_and_missing_text_prevents_the_note_creation(self):
        self.client.force_login(user=self.one_cdd_user)
        response = self.client.post(self.url, data={'text': ''})

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'text', 'Ce champ est obligatoire.')

        self.assertEqual(InternalNote.objects.filter(admission=self.first_admission).count(), 2)

    def test_post_with_cdd_user_and_valid_form_creates_a_new_note(self):
        self.client.force_login(user=self.one_cdd_user)
        response = self.client.post(self.url, data={'text': 'A fantastic text'})

        self.assertRedirects(response, self.url)

        internal_notes: List[InternalNote] = InternalNote.objects.filter(admission=self.first_admission)

        self.assertEqual(len(internal_notes), 3)
        self.assertEqual(internal_notes[0].author, self.one_cdd_user.person)
        self.assertEqual(internal_notes[0].text, 'A fantastic text')
