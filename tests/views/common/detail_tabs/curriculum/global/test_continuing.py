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

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.contrib.models import ContinuingEducationAdmission
from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
)
from admission.tests.factories.curriculum import (
    ProfessionalExperienceFactory,
    AdmissionEducationalValuatedExperiencesFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
)
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.models.enums.education_group_types import TrainingType
from base.models.enums.teaching_type import TeachingTypeEnum
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from osis_profile import BE_ISO_CODE
from osis_profile.models import EducationalExperienceYear, EducationalExperience, ProfessionalExperience
from osis_profile.models.enums.curriculum import (
    EvaluationSystem,
    TranscriptType,
    Grade,
    Result,
    Reduction,
    ActivityType,
    ActivitySector,
)
from osis_profile.tests.factories.curriculum import EducationalExperienceFactory, EducationalExperienceYearFactory
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.diploma_title import DiplomaTitleFactory
from reference.tests.factories.language import LanguageFactory
from reference.tests.factories.superior_non_university import SuperiorNonUniversityFactory


@freezegun.freeze_time('2024-06-01')
class CurriculumGlobalDetailsViewForContinuingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]
        cls.entity = EntityVersionFactory().entity
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.entity).person.user
        cls.be_country = CountryFactory(iso_code=BE_ISO_CODE, name='Belgique', name_en='Belgium')
        cls.foreign_country = CountryFactory(iso_code=FR_ISO_CODE, name='France', name_en='France')
        cls.diploma = DiplomaTitleFactory()
        cls.other_diploma = DiplomaTitleFactory()
        cls.linguistic_regime = LanguageFactory(code=FR_ISO_CODE)
        cls.institute = SuperiorNonUniversityFactory(teaching_type=TeachingTypeEnum.SOCIAL_PROMOTION.name)

    def setUp(self):
        self.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=self.entity,
            training__academic_year=self.academic_years[1],
            training__education_group_type__name=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
        )

        self.fac_manager_user = ProgramManagerRoleFactory(
            education_group=self.continuing_admission.training.education_group,
        ).person.user

        self.url = resolve_url('admission:continuing-education:curriculum', uuid=self.continuing_admission.uuid)

    def test_get_curriculum_with_sic_manager_user(self):
        self.client.force_login(user=self.sic_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_curriculum_with_fac_manager_user(self):
        self.client.force_login(user=self.fac_manager_user)

        self.continuing_admission.training.specificiufcinformations.registration_required = False
        self.continuing_admission.training.specificiufcinformations.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        curriculum: CurriculumAdmissionDTO = response.context['curriculum']
        self.assertEqual(curriculum.experiences_academiques, [])
        self.assertEqual(curriculum.experiences_non_academiques, [])
        self.assertEqual(curriculum.annee_minimum_a_remplir, 2019)
        self.assertEqual(curriculum.annee_derniere_inscription_ucl, None)
        self.assertEqual(curriculum.annee_diplome_etudes_secondaires, None)

        self.assertFalse(response.context['display_curriculum'])
        self.assertFalse(response.context['display_equivalence'])

    def test_get_curriculum_with_displayed_attachments(self):
        self.client.force_login(user=self.sic_manager_user)

        # The curriculum is displayed if the registration is required for this training
        self.continuing_admission.training.specificiufcinformations.registration_required = True
        self.continuing_admission.training.specificiufcinformations.save()

        # The equivalence is displayed if the candidate has obtained a foreign diploma
        educational_experience = EducationalExperienceFactory(
            person=self.continuing_admission.candidate,
            obtained_diploma=True,
            country=self.foreign_country,
        )

        educational_experience_year = EducationalExperienceYearFactory(
            educational_experience=educational_experience,
            academic_year=self.academic_years[1],
        )

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.continuing_admission,
            educationalexperience=educational_experience,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context['display_curriculum'])
        self.assertTrue(response.context['display_equivalence'])

    def test_get_curriculum_with_academic_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        educational_experience: EducationalExperience = EducationalExperienceFactory(
            person=self.continuing_admission.candidate,
            country=self.foreign_country,
            institute=None,
            institute_address='My custom institute address',
            institute_name='My custom institute name',
            program=None,
            fwb_equivalent_program=None,
            education_name='My custom program name',
            study_system=TeachingTypeEnum.SOCIAL_PROMOTION.name,
            evaluation_type=EvaluationSystem.ECTS_CREDITS.name,
            linguistic_regime=None,
            transcript_type=TranscriptType.ONE_FOR_ALL_YEARS.name,
            obtained_diploma=True,
            obtained_grade=Grade.DISTINCTION.name,
            graduate_degree=[uuid.uuid4()],
            graduate_degree_translation=[uuid.uuid4()],
            transcript=[uuid.uuid4()],
            transcript_translation=[uuid.uuid4()],
            rank_in_diploma='50/100',
            expected_graduation_date=datetime.date(2024, 1, 1),
            dissertation_title='Dissertation title',
            dissertation_score='15/20',
            dissertation_summary=[uuid.uuid4()],
        )

        educational_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=educational_experience,
            academic_year=self.academic_years[1],
            registered_credit_number=20,
            acquired_credit_number=19,
            result=Result.SUCCESS.name,
            transcript=[uuid.uuid4()],
            transcript_translation=[uuid.uuid4()],
            with_block_1=True,
            with_complement=True,
            fwb_registered_credit_number=30,
            fwb_acquired_credit_number=29,
            reduction=Reduction.A150.name,
            is_102_change_of_course=True,
        )

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.continuing_admission,
            educationalexperience=educational_experience,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        curriculum: CurriculumAdmissionDTO = response.context['curriculum']
        self.assertEqual(len(curriculum.experiences_academiques), 1)

        experience = curriculum.experiences_academiques[0]

        self.assertEqual(experience.uuid, educational_experience.uuid)
        self.assertEqual(experience.pays, educational_experience.country.iso_code)
        self.assertEqual(experience.nom_pays, educational_experience.country.name)
        self.assertEqual(experience.nom_institut, 'My custom institute name')
        self.assertEqual(experience.adresse_institut, 'My custom institute address')
        self.assertEqual(experience.code_institut, '')
        self.assertEqual(experience.communaute_institut, '')
        self.assertEqual(experience.type_institut, '')
        self.assertEqual(experience.regime_linguistique, '')
        self.assertEqual(experience.nom_regime_linguistique, '')
        self.assertEqual(experience.type_releve_notes, TranscriptType.ONE_FOR_ALL_YEARS.name)
        self.assertEqual(experience.releve_notes, educational_experience.transcript)
        self.assertEqual(experience.traduction_releve_notes, educational_experience.transcript_translation)
        self.assertEqual(experience.a_obtenu_diplome, educational_experience.obtained_diploma)
        self.assertEqual(experience.diplome, educational_experience.graduate_degree)
        self.assertEqual(experience.traduction_diplome, educational_experience.graduate_degree_translation)
        self.assertEqual(experience.rang_diplome, educational_experience.rank_in_diploma)
        self.assertEqual(experience.date_prevue_delivrance_diplome, educational_experience.expected_graduation_date)
        self.assertEqual(experience.titre_memoire, educational_experience.dissertation_title)
        self.assertEqual(experience.note_memoire, educational_experience.dissertation_score)
        self.assertEqual(experience.resume_memoire, educational_experience.dissertation_summary)
        self.assertEqual(experience.grade_obtenu, educational_experience.obtained_grade)
        self.assertEqual(experience.systeme_evaluation, educational_experience.evaluation_type)
        self.assertEqual(experience.nom_formation, 'My custom program name')
        self.assertEqual(experience.nom_formation_equivalente_communaute_fr, '')
        self.assertEqual(experience.est_autre_formation, True)
        self.assertEqual(experience.cycle_formation, '')
        self.assertEqual(experience.type_enseignement, educational_experience.study_system)
        self.assertEqual(experience.injectee, False)
        self.assertEqual(experience.valorisee_par_admissions, [self.continuing_admission.uuid])
        self.assertEqual(experience.identifiant_externe, None)

        self.assertEqual(len(experience.annees), 1)
        annee = experience.annees[0]

        self.assertEqual(annee.uuid, educational_experience_year.uuid)
        self.assertEqual(annee.annee, educational_experience_year.academic_year.year)
        self.assertEqual(annee.resultat, educational_experience_year.result)
        self.assertEqual(annee.releve_notes, educational_experience_year.transcript)
        self.assertEqual(annee.traduction_releve_notes, educational_experience_year.transcript_translation)
        self.assertEqual(annee.credits_inscrits, educational_experience_year.registered_credit_number)
        self.assertEqual(annee.credits_acquis, educational_experience_year.acquired_credit_number)
        self.assertEqual(annee.avec_bloc_1, educational_experience_year.with_block_1)
        self.assertEqual(annee.avec_complement, educational_experience_year.with_complement)
        self.assertEqual(annee.credits_inscrits_communaute_fr, educational_experience_year.fwb_registered_credit_number)
        self.assertEqual(annee.credits_acquis_communaute_fr, educational_experience_year.fwb_acquired_credit_number)
        self.assertEqual(annee.allegement, educational_experience_year.reduction)
        self.assertEqual(annee.est_reorientation_102, educational_experience_year.is_102_change_of_course)

        # With linguistic regime
        educational_experience.linguistic_regime = self.linguistic_regime

        # With existing institute
        educational_experience.institute = self.institute
        educational_experience.institute_name = ('',)
        educational_experience.institute_address = ''

        # With existing program
        educational_experience.program = self.diploma
        educational_experience.education_name = ''

        # With existing fwb equivalent program
        educational_experience.fwb_equivalent_program = self.other_diploma

        educational_experience.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        curriculum = response.context['curriculum']

        self.assertEqual(len(curriculum.experiences_academiques), 1)

        experience = curriculum.experiences_academiques[0]

        self.assertEqual(experience.uuid, educational_experience.uuid)

        self.assertEqual(experience.regime_linguistique, self.linguistic_regime.code)
        self.assertEqual(experience.nom_regime_linguistique, self.linguistic_regime.name)

        self.assertEqual(experience.nom_institut, self.institute.name)
        self.assertEqual(experience.code_institut, self.institute.acronym)
        self.assertEqual(experience.communaute_institut, self.institute.community)
        self.assertEqual(experience.adresse_institut, '')
        self.assertEqual(experience.type_institut, self.institute.establishment_type)

        self.assertEqual(experience.nom_formation, self.diploma.title)
        self.assertEqual(experience.nom_formation_equivalente_communaute_fr, self.other_diploma.title)
        self.assertEqual(experience.cycle_formation, self.other_diploma.cycle)
        self.assertEqual(experience.est_autre_formation, False)

    def test_get_curriculum_with_non_academic_experience(self):
        self.client.force_login(user=self.sic_manager_user)

        non_academic_experience: ProfessionalExperience = ProfessionalExperienceFactory(
            person=self.continuing_admission.candidate,
            institute_name='My custom institute name',
            start_date=datetime.date(2000, 1, 1),
            end_date=datetime.date(2001, 1, 31),
            type=ActivityType.WORK.name,
            certificate=[uuid.uuid4()],
            role='Role',
            sector=ActivitySector.PUBLIC.name,
            activity='My custom activity',
        )

        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=self.continuing_admission,
            professionalexperience=non_academic_experience,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        curriculum: CurriculumAdmissionDTO = response.context['curriculum']
        self.assertEqual(len(curriculum.experiences_non_academiques), 1)

        experience = curriculum.experiences_non_academiques[0]

        self.assertEqual(experience.uuid, non_academic_experience.uuid)
        self.assertEqual(experience.employeur, non_academic_experience.institute_name)
        self.assertEqual(experience.date_debut, non_academic_experience.start_date)
        self.assertEqual(experience.date_fin, non_academic_experience.end_date)
        self.assertEqual(experience.type, non_academic_experience.type)
        self.assertEqual(experience.certificat, non_academic_experience.certificate)
        self.assertEqual(experience.fonction, non_academic_experience.role)
        self.assertEqual(experience.secteur, non_academic_experience.sector)
        self.assertEqual(experience.autre_activite, non_academic_experience.activity)
        self.assertEqual(experience.injectee, False)
        self.assertEqual(experience.valorisee_par_admissions, [self.continuing_admission.uuid])
        self.assertEqual(experience.identifiant_externe, None)
