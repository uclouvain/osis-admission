# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase

from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.models.exam import AdmissionExam
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CentralManagerRoleFactory
from base.tests.factories.entity_version import EntityVersionFactory
from ddd.logic.shared_kernel.profil.domain.enums import TypeExperience
from osis_profile.models import Exam
from osis_profile.models.education import HighSchoolDiploma
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience, \
    EtatAuthentificationParcours
from osis_profile.tests.factories.exam import ExamTypeFactory


class InitializeExperienceViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):

        cls.admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            training__management_entity = EntityVersionFactory().entity,
        )
        cls.sic_manager_user = CentralManagerRoleFactory(entity=cls.admission.training.management_entity).person.user
        cls.path = 'admission:general-education:initialize-experience'
        cls.redirect_url = resolve_url('admission:general-education:checklist', uuid=cls.admission.uuid)

    def test_initialize_secondary_studies(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(self.path, uuid=self.admission.uuid, experience_type=TypeExperience.ETUDES_SECONDAIRES.name)

        high_school_diploma_qs = HighSchoolDiploma.objects.filter(person=self.admission.candidate)

        self.assertFalse(high_school_diploma_qs.exists())

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)

        high_school_diploma = high_school_diploma_qs.first()

        self.assertIsNotNone(high_school_diploma)

        self.assertRedirects(
            response=response,
            fetch_redirect_response=False,
            expected_url=f'{self.redirect_url}#parcours_anterieur__{high_school_diploma.uuid}',
        )

        self.assertEqual(high_school_diploma.person, self.admission.candidate)
        self.assertEqual(high_school_diploma.got_diploma, '')
        self.assertEqual(high_school_diploma.academic_graduation_year, None)
        self.assertEqual(high_school_diploma.validation_status, ChoixStatutValidationExperience.A_TRAITER.name)
        self.assertEqual(high_school_diploma.authentication_status, EtatAuthentificationParcours.NON_CONCERNE.name)

    def test_initialize_exam(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(self.path, uuid=self.admission.uuid, experience_type=TypeExperience.EXAMEN.name)

        exam_qs = Exam.objects.filter(person=self.admission.candidate)

        self.assertFalse(exam_qs.exists())

        # No exam type is defined for the admission training so no exam is created
        response = self.client.post(url)

        self.assertRedirects(
            response=response,
            fetch_redirect_response=False,
            expected_url=f'{self.redirect_url}#parcours_anterieur',
        )

        # An exam type is defined for the admission training so an exam is created
        exam_type = ExamTypeFactory(education_group_years=[self.admission.training])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)

        exam = exam_qs.first()

        self.assertIsNotNone(exam)

        self.assertRedirects(
            response=response,
            fetch_redirect_response=False,
            expected_url=f'{self.redirect_url}#parcours_anterieur__{exam.uuid}',
        )

        self.assertEqual(exam.person, self.admission.candidate)
        self.assertEqual(exam.certificate, [])
        self.assertEqual(exam.type, exam_type)
        self.assertEqual(exam.year, None)
        self.assertEqual(exam.validation_status, ChoixStatutValidationExperience.A_TRAITER.name)
        self.assertEqual(exam.authentication_status, EtatAuthentificationParcours.NON_CONCERNE.name)

        self.assertTrue(AdmissionExam.objects.filter(admission=self.admission, exam=exam).exists())