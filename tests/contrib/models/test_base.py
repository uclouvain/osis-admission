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
from django.db import IntegrityError
from django.test import TestCase

from admission.contrib.models import AdmissionViewer
from admission.contrib.models.base import admission_directory_path, BaseAdmission
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.admission_viewer import AdmissionViewerFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.tests.factories.academic_year import AcademicYearFactory


class BaseTestCase(TestCase):
    def setUp(self):
        self.base_admission = DoctorateAdmissionFactory()

    def test_valid_upload_to(self):
        self.assertEqual(
            admission_directory_path(self.base_admission, 'my_file.pdf'),
            'admission/{}/{}/my_file.pdf'.format(self.base_admission.candidate.uuid, self.base_admission.uuid),
        )


class BaseAnnotateSeveralAdmissionInProgress(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.academic_year = AcademicYearFactory(year=2020)
        cls.base_admission = GeneralEducationAdmissionFactory(
            determined_academic_year=cls.academic_year,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

    def test_annotate_several_admissions_in_progress_with_no_other_admission(self):
        with self.assertNumQueries(1):
            admission = BaseAdmission.objects.annotate_several_admissions_in_progress().first()
            self.assertFalse(admission.has_several_admissions_in_progress)

    def test_annotate_several_admissions_in_progress_with_other_admission_but_with_other_candidate(self):
        GeneralEducationAdmissionFactory(
            determined_academic_year=self.base_admission.determined_academic_year,
            status=self.base_admission.status,
        )
        with self.assertNumQueries(1):
            admission = BaseAdmission.objects.annotate_several_admissions_in_progress().all()[0]
            self.assertFalse(admission.has_several_admissions_in_progress)

    def test_annotate_several_admissions_in_progress_with_other_admission_but_with_in_progress_status(self):
        GeneralEducationAdmissionFactory(
            determined_academic_year=self.base_admission.determined_academic_year,
            status=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            candidate=self.base_admission.candidate,
        )
        with self.assertNumQueries(1):
            admission = BaseAdmission.objects.annotate_several_admissions_in_progress().all()[0]
            self.assertFalse(admission.has_several_admissions_in_progress)

    def test_annotate_several_admissions_in_progress_with_other_admission_but_with_cancelled_status(self):
        GeneralEducationAdmissionFactory(
            determined_academic_year=self.base_admission.determined_academic_year,
            status=ChoixStatutPropositionGenerale.ANNULEE.name,
            candidate=self.base_admission.candidate,
        )
        with self.assertNumQueries(1):
            admission = BaseAdmission.objects.annotate_several_admissions_in_progress().all()[0]
            self.assertFalse(admission.has_several_admissions_in_progress)

    def test_annotate_several_admissions_in_progress_with_other_admission(self):
        GeneralEducationAdmissionFactory(
            determined_academic_year=self.base_admission.determined_academic_year,
            status=self.base_admission.status,
            candidate=self.base_admission.candidate,
        )
        with self.assertNumQueries(1):
            admission = BaseAdmission.objects.annotate_several_admissions_in_progress().all()[0]
            self.assertTrue(admission.has_several_admissions_in_progress)


class AdmissionViewerTestCase(TestCase):
    def test_admission_viewers_duplicates(self):
        admission = GeneralEducationAdmissionFactory()

        AdmissionViewer.objects.all().delete()

        AdmissionViewer.add_viewer(admission.candidate, admission)
        AdmissionViewer.add_viewer(admission.candidate, admission)

        self.assertEqual(AdmissionViewer.objects.all().count(), 1)

        with self.assertRaises(IntegrityError):
            AdmissionViewerFactory(admission=admission, person=admission.candidate)
            AdmissionViewerFactory(admission=admission, person=admission.candidate)
