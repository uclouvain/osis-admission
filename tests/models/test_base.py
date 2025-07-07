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
import datetime

import freezegun
from django.db import IntegrityError
from django.test import TestCase

from admission.constants import CONTEXT_GENERAL, CONTEXT_CONTINUING, CONTEXT_DOCTORATE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    continuing_education_types_as_set,
    doctorate_types_as_set,
)
from admission.models import AdmissionViewer, ContinuingEducationAdmissionProxy
from admission.models.base import admission_directory_path, BaseAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.admission_viewer import AdmissionViewerFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_types import TrainingType, AllTypes
from base.models.enums.entity_type import EntityType
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.entity_version import MainEntityVersionFactory, EntityVersionFactory
from base.tests.factories.person import PersonFactory
from epc.tests.factories.inscription_programme_annuel import InscriptionProgrammeAnnuelFactory


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


class AdmissionInQuarantineTestCase(TestCase):
    def test_admission_in_quarantine(self):
        # With no person proposal
        admission = GeneralEducationAdmissionFactory()

        self.assertFalse(admission.is_in_quarantine)

        # With a person proposal
        related_person = PersonFactory()
        other_person = PersonFactory()

        proposal = PersonMergeProposal(
            status=PersonMergeStatus.MATCH_FOUND.name,
            original_person=other_person,
            proposal_merge_person=related_person,
            last_similarity_result_update=datetime.datetime.now(),
        )

        admission = BaseAdmission.objects.get(pk=admission.pk)
        self.assertFalse(admission.is_in_quarantine)

        proposal.original_person = admission.candidate
        proposal.save()

        admission = BaseAdmission.objects.get(pk=admission.pk)
        self.assertTrue(admission.is_in_quarantine)

        in_quarantine_statuses = {
            PersonMergeStatus.MATCH_FOUND,
            PersonMergeStatus.PENDING,
            PersonMergeStatus.ERROR,
            PersonMergeStatus.IN_PROGRESS,
        }

        for status in PersonMergeStatus:
            proposal.status = status.name
            proposal.validation = {}
            proposal.save()

            admission = BaseAdmission.objects.get(pk=admission.pk)

            # The admission is in quarantine depending on the proposal status
            self.assertEqual(admission.is_in_quarantine, status in in_quarantine_statuses)

            # The admission is always in quarantine if there is an error during the digit ticket validation
            proposal.validation = {'valid': False}
            proposal.save()

            admission = BaseAdmission.objects.get(pk=admission.pk)

            self.assertTrue(admission.is_in_quarantine)


@freezegun.freeze_time('2023-01-01')
class AdmissionFormattedReferenceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = {
            academic_year.year: academic_year
            for academic_year in AcademicYearFactory.produce(
                base_year=2022,
                number_past=2,
                number_future=2,
            )
        }

        root = MainEntityVersionFactory(parent=None, entity_type='')

        cls.faculty = EntityVersionFactory(
            entity_type=EntityType.FACULTY.name,
            acronym='FFC',
            parent=root.entity,
            end_date=datetime.date(2023, 1, 2),
        )

        cls.school = EntityVersionFactory(
            entity_type=EntityType.SCHOOL.name,
            acronym='SFC',
            parent=root.entity,
            end_date=datetime.date(2023, 1, 2),
        )

    def test_get_formatted_reference_depending_on_management_entity(self):
        created_admission = ContinuingEducationAdmissionFactory(training__management_entity=self.school.entity)

        # With school as management entity
        admission = ContinuingEducationAdmissionProxy.objects.for_dto().get(uuid=created_admission.uuid)
        self.assertEqual(admission.sigle_entite_gestion, 'SFC')
        self.assertEqual(admission.training_management_faculty, None)
        self.assertEqual(admission.formatted_reference, f'M-SFC22-{str(admission)}')

        # With faculty as parent entity of the school
        self.school.parent = self.faculty.entity
        self.school.save()
        EntityVersion.objects.filter(uuid=self.school.uuid).update(parent=self.faculty.entity)
        admission = ContinuingEducationAdmissionProxy.objects.for_dto().get(uuid=created_admission.uuid)
        self.assertEqual(admission.sigle_entite_gestion, 'SFC')
        self.assertEqual(admission.training_management_faculty, 'FFC')
        self.assertEqual(admission.formatted_reference, f'M-FFC22-{str(admission)}')

    def test_get_formatted_reference_depending_on_academic_year(self):
        created_admission = ContinuingEducationAdmissionFactory(
            training__management_entity=self.school.entity,
            training__academic_year=self.academic_years[2021],
            submitted_at=datetime.date(2022, 1, 1),
            determined_academic_year=AcademicYearFactory.create(year=2023),
        )

        reference = 'M-SFC%(year)s-' + str(created_admission)

        # The admission has been submitted, only use the training academic year
        admission = BaseAdmission.objects.with_training_management_and_reference().get(uuid=created_admission.uuid)

        self.assertEqual(admission.formatted_reference, reference % {'year': '21'})

        created_admission.determined_academic_year = None
        created_admission.save()

        admission = BaseAdmission.objects.with_training_management_and_reference().get(uuid=created_admission.uuid)

        self.assertEqual(admission.formatted_reference, reference % {'year': '21'})

        # The admission has not been submitted
        created_admission.submitted_at = None
        created_admission.determined_academic_year = self.academic_years[2023]
        created_admission.save()

        # > use the determined academic year if specified
        admission = BaseAdmission.objects.with_training_management_and_reference().get(uuid=created_admission.uuid)

        self.assertEqual(admission.formatted_reference, reference % {'year': '23'})

        # > else use training academic year
        created_admission.determined_academic_year = None
        created_admission.save()

        admission = BaseAdmission.objects.with_training_management_and_reference().get(uuid=created_admission.uuid)

        self.assertEqual(admission.formatted_reference, reference % {'year': '21'})


class OtherCandidateTrainingsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admission = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.BACHELOR.name,
        )

    def setUp(self):
        try:
            delattr(self.admission, 'other_candidate_trainings')
        except AttributeError:
            pass

    def test_by_excluding_the_current_admission(self):
        # Don't use the current admission
        other_contexts = self.admission.other_candidate_trainings

        self.assertEqual(other_contexts[CONTEXT_GENERAL], set())
        self.assertEqual(other_contexts[CONTEXT_CONTINUING], set())
        self.assertEqual(other_contexts[CONTEXT_DOCTORATE], set())

    def test_with_general_admission(self):
        excluding_statuses = {
            ChoixStatutPropositionGenerale.EN_BROUILLON,
            ChoixStatutPropositionGenerale.ANNULEE,
        }

        other_admission = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.MASTER_MC.name,
            candidate=self.admission.candidate,
        )

        for status in ChoixStatutPropositionGenerale:
            other_admission.status = status.name
            other_admission.save(update_fields=['status'])

            other_contexts = self.admission.other_candidate_trainings

            self.assertEqual(
                other_contexts[CONTEXT_GENERAL],
                {TrainingType.MASTER_MC.name} if status not in excluding_statuses else set(),
            )
            self.assertEqual(other_contexts[CONTEXT_CONTINUING], set())
            self.assertEqual(other_contexts[CONTEXT_DOCTORATE], set())

            delattr(self.admission, 'other_candidate_trainings')

    def test_with_doctorate_admission(self):
        excluding_statuses = {
            ChoixStatutPropositionDoctorale.EN_BROUILLON,
            ChoixStatutPropositionDoctorale.ANNULEE,
        }

        other_admission = DoctorateAdmissionFactory(
            training__education_group_type__name=TrainingType.PHD.name,
            candidate=self.admission.candidate,
        )

        for status in ChoixStatutPropositionDoctorale:
            other_admission.status = status.name
            other_admission.save(update_fields=['status'])

            other_contexts = self.admission.other_candidate_trainings

            self.assertEqual(
                other_contexts[CONTEXT_DOCTORATE],
                {TrainingType.PHD.name} if status not in excluding_statuses else set(),
            )
            self.assertEqual(other_contexts[CONTEXT_GENERAL], set())
            self.assertEqual(other_contexts[CONTEXT_CONTINUING], set())

            delattr(self.admission, 'other_candidate_trainings')

    def test_with_continuing_admission(self):
        excluding_statuses = {
            ChoixStatutPropositionContinue.EN_BROUILLON,
            ChoixStatutPropositionContinue.ANNULEE,
        }

        other_admission = ContinuingEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.CERTIFICATE_OF_SUCCESS.name,
            candidate=self.admission.candidate,
        )

        for status in ChoixStatutPropositionContinue:
            other_admission.status = status.name
            other_admission.save(update_fields=['status'])

            other_contexts = self.admission.other_candidate_trainings

            self.assertEqual(
                other_contexts[CONTEXT_CONTINUING],
                {TrainingType.CERTIFICATE_OF_SUCCESS.name} if status not in excluding_statuses else set(),
            )
            self.assertEqual(other_contexts[CONTEXT_GENERAL], set())
            self.assertEqual(other_contexts[CONTEXT_DOCTORATE], set())

            delattr(self.admission, 'other_candidate_trainings')

    def test_with_internal_experiences(self):
        internal_experience = InscriptionProgrammeAnnuelFactory(
            programme_cycle__etudiant__person=self.admission.candidate,
            programme__root_group__education_group_type__name=TrainingType.MASTER_M1.name,
        )

        other_contexts = self.admission.other_candidate_trainings
        self.assertEqual(other_contexts[CONTEXT_CONTINUING], set())
        self.assertEqual(other_contexts[CONTEXT_GENERAL], {TrainingType.MASTER_M1.name})
        self.assertEqual(other_contexts[CONTEXT_DOCTORATE], set())

        delattr(self.admission, 'other_candidate_trainings')

        internal_experience.programme = None
        internal_experience.save(update_fields=['programme'])

        other_contexts = self.admission.other_candidate_trainings
        self.assertEqual(other_contexts[CONTEXT_CONTINUING], set())
        self.assertEqual(other_contexts[CONTEXT_GENERAL], set())
        self.assertEqual(other_contexts[CONTEXT_DOCTORATE], set())

    def test_right_context_by_training_type(self):
        internal_experience = InscriptionProgrammeAnnuelFactory(
            programme_cycle__etudiant__person=self.admission.candidate,
        )

        root_group = internal_experience.programme.root_group

        for training_type in AllTypes.get_names():
            root_group.education_group_type = EducationGroupTypeFactory(name=training_type)
            root_group.save(update_fields=['education_group_type'])

            other_contexts = self.admission.other_candidate_trainings

            if training_type in continuing_education_types_as_set:
                self.assertEqual(other_contexts[CONTEXT_CONTINUING], {training_type})
                self.assertEqual(other_contexts[CONTEXT_GENERAL], set())
                self.assertEqual(other_contexts[CONTEXT_DOCTORATE], set())
            elif training_type in doctorate_types_as_set:
                self.assertEqual(other_contexts[CONTEXT_DOCTORATE], {training_type})
                self.assertEqual(other_contexts[CONTEXT_GENERAL], set())
                self.assertEqual(other_contexts[CONTEXT_CONTINUING], set())
            else:
                self.assertEqual(other_contexts[CONTEXT_GENERAL], {training_type})
                self.assertEqual(other_contexts[CONTEXT_CONTINUING], set())
                self.assertEqual(other_contexts[CONTEXT_DOCTORATE], set())

            delattr(self.admission, 'other_candidate_trainings')
