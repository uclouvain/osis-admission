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

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.models.exam import AdmissionExam
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.roles import SicManagementRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from ddd.logic.shared_kernel.profil.dtos.examens import ExamenDTO
from osis_profile.models import Exam
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience, \
    EtatAuthentificationParcours
from osis_profile.tests.factories.exam import ExamFactory, ExamTypeFactory


@freezegun.freeze_time('2022-01-01')
class ExamDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]

        cls.training = GeneralEducationTrainingFactory(
            academic_year=cls.academic_years[1],
            management_entity=EntityVersionFactory().entity,
        )

        cls.sic_manager_user = SicManagementRoleFactory(
            entity=cls.training.management_entity,
        ).person.user

        cls.exam_type = ExamTypeFactory(
            education_group_years=[cls.training],
        )

        cls.general_admission = GeneralEducationAdmissionFactory(
            training=cls.training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

    def setUp(self):
        self.url = resolve_url('admission:general-education:exam', uuid=self.general_admission.uuid)

    def test_get_with_sic_manager_user_is_allowed(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_with_exam_existing(self):
        self.client.force_login(self.sic_manager_user)

        exam = ExamFactory(
            person=self.general_admission.candidate,
            type=self.exam_type,
            year=self.academic_years[0],
            validation_status=ChoixStatutValidationExperience.AUTHENTIFICATION.name,
            authentication_status=EtatAuthentificationParcours.VRAI.name,
        )

        AdmissionExam.objects.create(admission=self.general_admission, exam=exam)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, str(self.academic_years[0].year + 1))

        exam: ExamenDTO | None = response.context['examen']

        self.assertIsNotNone(exam)

        self.assertEqual(exam.titre, self.exam_type.title)
        self.assertEqual(exam.annee, self.academic_years[0].year)
        self.assertEqual(exam.statut_validation, ChoixStatutValidationExperience.AUTHENTIFICATION.name)
        self.assertEqual(exam.statut_authentification, EtatAuthentificationParcours.VRAI.name)
