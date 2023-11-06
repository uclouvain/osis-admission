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
from typing import List

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext
from rest_framework import status

from admission.calendar.admission_calendar import SIGLES_WITH_QUOTA
from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.enums import Onglets
from admission.tests.factories.diplomatic_post import DiplomaticPostFactory
from admission.tests.factories.form_item import AdmissionFormItemInstantiationFactory, MessageAdmissionFormItemFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import (
    SicManagementRoleFactory,
    CandidateFactory,
    ProgramManagerRoleFactory,
)
from base.models.enums.person_address_type import PersonAddressType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import Master120TrainingFactory, EducationGroupYearBachelorFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person_address import PersonAddressFactory
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2022-01-01')
class SpecificQuestionsDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.be_country = CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')
        cls.ca_country = CountryFactory(iso_code='CA', european_union=False)

        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(
            entity=first_doctoral_commission,
        )

        cls.master_training = Master120TrainingFactory(
            management_entity=first_doctoral_commission,
            academic_year=cls.academic_years[1],
        )
        cls.bachelor_training = EducationGroupYearBachelorFactory(
            management_entity=first_doctoral_commission,
            academic_year=cls.academic_years[1],
        )
        cls.bachelor_training_with_quota = EducationGroupYearBachelorFactory(
            management_entity=first_doctoral_commission,
            academic_year=cls.academic_years[1],
            acronym=SIGLES_WITH_QUOTA[0],
            partial_acronym=SIGLES_WITH_QUOTA[0],
        )

        cls.specific_questions = [
            AdmissionFormItemInstantiationFactory(
                form_item=MessageAdmissionFormItemFactory(),
                tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
                academic_year=cls.academic_years[1],
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=MessageAdmissionFormItemFactory(),
                tab=Onglets.CURRICULUM.name,
                academic_year=cls.academic_years[1],
            ),
        ]

        cls.diplomatic_post = DiplomaticPostFactory(
            name_fr='Londres',
            name_en='London',
            email='london@example.be',
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.master_training.education_group
        ).person.user

    def setUp(self):
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.master_training,
            candidate__language=settings.LANGUAGE_CODE_EN,
            admitted=True,
            determined_academic_year=self.academic_years[1],
            is_non_resident=False,
            diplomatic_post=self.diplomatic_post,
        )

        self.url = resolve_url('admission:general-education:specific-questions', uuid=self.general_admission.uuid)

    def test_general_specific_questions_access(self):
        # If the user is not authenticated, they should be redirected to the login page
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + self.url)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, they should be able to access the page
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_general_specific_questions(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['proposition'].uuid, self.general_admission.uuid)

        specific_questions: List[QuestionSpecifiqueDTO] = response.context.get('specific_questions', [])
        self.assertEqual(len(specific_questions), 1)
        self.assertEqual(specific_questions[0].uuid, str(self.specific_questions[0].form_item.uuid))

        self.assertEqual(response.context.get('display_visa_question'), False)
        self.assertNotContains(response, self.diplomatic_post.name_fr)

        self.assertEqual(response.context.get('eligible_for_reorientation'), False)
        self.assertNotContains(response, gettext('Course change'))

        self.assertEqual(response.context.get('eligible_for_modification'), False)
        self.assertNotContains(response, gettext('Change of enrolment'))

        self.assertEqual(response.context.get('enrolled_for_contingent_training'), False)
        self.assertNotContains(response, gettext('Enrolment in limited enrolment bachelor\'s course'))

        # Display visa question: not ue+5 nationality and foreign residential country
        self.general_admission.candidate.country_of_citizenship = self.ca_country
        self.general_admission.candidate.save()
        PersonAddressFactory(
            person=self.general_admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
            country=self.ca_country,
        )

        # Display pool questions: bachelor with quota
        self.general_admission.training = self.bachelor_training_with_quota
        self.general_admission.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context.get('display_visa_question'), True)
        self.assertContains(response, self.diplomatic_post.name_fr)

        self.assertEqual(response.context.get('eligible_for_reorientation'), True)
        self.assertContains(response, gettext('Course change'))

        self.assertEqual(response.context.get('eligible_for_modification'), True)
        self.assertContains(response, gettext('Change of enrolment'))

        self.assertEqual(response.context.get('enrolled_for_contingent_training'), True)
        self.assertContains(response, gettext('Enrolment in limited enrolment bachelor\'s course'))

        # Hide reorientation and modification questions because the candidate is not resident as defined by decree
        self.general_admission.is_non_resident = True
        self.general_admission.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context.get('eligible_for_reorientation'), False)
        self.assertNotContains(response, gettext('Course change'))

        self.assertEqual(response.context.get('eligible_for_modification'), False)
        self.assertNotContains(response, gettext('Change of enrolment'))

        self.assertEqual(response.context.get('enrolled_for_contingent_training'), True)
        self.assertContains(response, gettext('Enrolment in limited enrolment bachelor\'s course'))

        # Show reorientation and modification because the training has no quota
        self.general_admission.training = self.bachelor_training
        self.general_admission.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context.get('eligible_for_reorientation'), True)
        self.assertContains(response, gettext('Course change'))

        self.assertEqual(response.context.get('eligible_for_modification'), True)
        self.assertContains(response, gettext('Change of enrolment'))

        self.assertEqual(response.context.get('enrolled_for_contingent_training'), False)
        self.assertNotContains(response, gettext('Enrolment in limited enrolment bachelor\'s course'))
