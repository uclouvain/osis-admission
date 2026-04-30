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

from django.test import TestCase

from admission.api.serializers import (
    candidate_is_potentially_concerned_by_bama_15,
)
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories.curriculum import (
    AdmissionEducationalValuatedExperiencesFactory,
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.models.enums.community import CommunityEnum
from base.models.enums.education_group_types import TrainingType
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.organization import OrganizationFactory
from reference.models.enums.cycle import Cycle
from reference.tests.factories.diploma_title import DiplomaTitleFactory


class CandidateHasFirstCycleFwbExperienceWithNoDiplomaForTheEnrolmentTrainingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = {year: AcademicYearFactory(year=year) for year in [2020, 2021, 2022]}
        cls.first_cycle_program = DiplomaTitleFactory(cycle=Cycle.FIRST_CYCLE.name)
        cls.second_cycle_program = DiplomaTitleFactory(cycle=Cycle.SECOND_CYCLE.name)
        cls.french_speaking_institute = OrganizationFactory(community=CommunityEnum.FRENCH_SPEAKING.name)
        cls.german_speaking_institute = OrganizationFactory(community=CommunityEnum.GERMAN_SPEAKING.name)
        cls.ucl_institute = OrganizationFactory(
            acronym=UCLouvain_acronym,
            community=CommunityEnum.FRENCH_SPEAKING.name,
        )

    def test_with_in_draft_admission(self):
        admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            training__academic_year=self.academic_years[2021],
            determined_academic_year=None,
            training__education_group_type__name=TrainingType.MASTER_MA_120.name,
        )

        # No experience
        res = candidate_is_potentially_concerned_by_bama_15(admission)

        self.assertFalse(res)

        # Created experience with the valid criteria
        experience = EducationalExperienceFactory(
            person=admission.candidate,
            obtained_diploma=False,
            institute=self.french_speaking_institute,
            program=self.first_cycle_program,
        )

        experience_year = EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=self.academic_years[2020],
        )

        res = candidate_is_potentially_concerned_by_bama_15(admission)

        self.assertTrue(res)

        # Second cycle program
        experience.program = self.second_cycle_program
        experience.save()

        res = candidate_is_potentially_concerned_by_bama_15(admission)

        self.assertFalse(res)

        # German speaking institute
        experience.program = self.first_cycle_program
        experience.institute = self.german_speaking_institute
        experience.save()

        res = candidate_is_potentially_concerned_by_bama_15(admission)

        self.assertFalse(res)

        # Experience with diploma
        experience.institute = self.french_speaking_institute
        experience.obtained_diploma = True
        experience.save()

        res = candidate_is_potentially_concerned_by_bama_15(admission)

        self.assertFalse(res)

        # Other year
        experience.obtained_diploma = False
        experience.save()
        experience_year.academic_year = self.academic_years[2021]
        experience_year.save()

        res = candidate_is_potentially_concerned_by_bama_15(admission)

        self.assertFalse(res)

        admission.determined_academic_year = self.academic_years[2022]
        admission.save()

        res = candidate_is_potentially_concerned_by_bama_15(admission)

        self.assertTrue(res)

        # UCL experience
        experience.institute = self.ucl_institute
        experience.save()

        res = candidate_is_potentially_concerned_by_bama_15(admission)

        self.assertFalse(res)

    def test_with_submitted_admission(self):
        admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            training__academic_year=self.academic_years[2021],
            determined_academic_year=self.academic_years[2021],
            training__education_group_type__name=TrainingType.MASTER_MA_120.name,
        )

        # Created experience with the valid criteria
        experience = EducationalExperienceFactory(
            person=admission.candidate,
            obtained_diploma=False,
            institute=self.french_speaking_institute,
            program=self.first_cycle_program,
        )

        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=self.academic_years[2020],
        )

        experience_valuation = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=admission,
            educationalexperience=experience,
        )

        res = candidate_is_potentially_concerned_by_bama_15(admission)

        self.assertTrue(res)

        experience_valuation.delete()

        res = candidate_is_potentially_concerned_by_bama_15(admission)

        self.assertFalse(res)
