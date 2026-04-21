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

from admission.infrastructure.admission.shared_kernel.domain.service.profil_candidat import (
    ProfilCandidatTranslator,
)
from admission.tests.factories.curriculum import EducationalExperienceFactory, EducationalExperienceYearFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.secondary_studies import (
    BelgianHighSchoolDiplomaFactory,
    ForeignHighSchoolDiplomaFactory,
    HighSchoolDiplomaAlternativeFactory,
)
from base.tests.factories.person import PersonFactory
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience


class ValorisationEtudesSecondairesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        super().setUpTestData()

    def test_with_an_unknown_person(self):
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires('unknown')
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

    def test_with_a_person_without_admission_or_diploma(self):
        person = PersonFactory()
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(person.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

    def test_with_a_person_with_admission_but_no_diploma(self):
        admission = GeneralEducationAdmissionFactory()
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

        # Valuated by an admission
        admission = GeneralEducationAdmissionFactory(
            candidate=admission.candidate,
            valuated_secondary_studies_person=admission.candidate,
        )
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(
            valuation.types_formations_admissions_valorisees,
            [admission.training.education_group_type.name],
        )
        self.assertTrue(valuation.est_valorise)

    def test_with_a_person_with_admission_and_high_school_diploma_alternative(self):
        admission = GeneralEducationAdmissionFactory()
        diploma = HighSchoolDiplomaAlternativeFactory()
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

        diploma.person = admission.candidate
        diploma.save(update_fields=['person'])
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

        # Valuated by an admission
        admission = GeneralEducationAdmissionFactory(
            candidate=admission.candidate,
            valuated_secondary_studies_person=admission.candidate,
        )
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(
            valuation.types_formations_admissions_valorisees,
            [admission.training.education_group_type.name],
        )
        self.assertTrue(valuation.est_valorise)

    def test_with_a_person_with_high_school_diploma_alternative_but_no_admission(self):
        GeneralEducationAdmissionFactory(
            candidate=self.person,
            valuated_secondary_studies_person=self.person,
        )
        diploma = HighSchoolDiplomaAlternativeFactory()
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(diploma.person.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

    def test_with_a_person_with_admission_and_belgian_high_school_diploma(self):
        admission = GeneralEducationAdmissionFactory()
        diploma = BelgianHighSchoolDiplomaFactory()
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

        diploma.person = admission.candidate
        diploma.save(update_fields=['person'])
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

        # Valuated by an admission
        admission = GeneralEducationAdmissionFactory(
            candidate=admission.candidate,
            valuated_secondary_studies_person=admission.candidate,
        )
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(
            valuation.types_formations_admissions_valorisees,
            [admission.training.education_group_type.name],
        )
        self.assertTrue(valuation.est_valorise)

        # Valuated by an admission and EPC
        diploma.external_id = 'EPC-1'
        diploma.save(update_fields=['external_id'])
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertTrue(valuation.est_valorise_par_epc)
        self.assertEqual(
            valuation.types_formations_admissions_valorisees,
            [admission.training.education_group_type.name],
        )
        self.assertTrue(valuation.est_valorise)

        # Valuated by EPC
        admission.valuated_secondary_studies_person = None
        admission.save(update_fields=['valuated_secondary_studies_person'])
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertTrue(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertTrue(valuation.est_valorise)

    def test_with_a_person_with_belgian_high_school_diploma_but_no_admission(self):
        GeneralEducationAdmissionFactory(
            candidate=self.person,
            valuated_secondary_studies_person=self.person,
        )
        diploma = BelgianHighSchoolDiplomaFactory()
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(diploma.person.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

        BelgianHighSchoolDiplomaFactory(external_id='EPC-0')
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(diploma.person.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

        # Valuated by EPC
        diploma.external_id = 'EPC-1'
        diploma.save(update_fields=['external_id'])
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(diploma.person.global_id)
        self.assertTrue(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertTrue(valuation.est_valorise)

    def test_with_a_person_with_admission_and_foreign_high_school_diploma(self):
        admission = GeneralEducationAdmissionFactory()
        diploma = ForeignHighSchoolDiplomaFactory()
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

        diploma.person = admission.candidate
        diploma.save(update_fields=['person'])
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

        # Valuated by an admission
        admission = GeneralEducationAdmissionFactory(
            candidate=admission.candidate,
            valuated_secondary_studies_person=admission.candidate,
        )
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(
            valuation.types_formations_admissions_valorisees,
            [admission.training.education_group_type.name],
        )
        self.assertTrue(valuation.est_valorise)

        # Valuated by an admission and EPC
        diploma.external_id = 'EPC-1'
        diploma.save(update_fields=['external_id'])
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertTrue(valuation.est_valorise_par_epc)
        self.assertEqual(
            valuation.types_formations_admissions_valorisees,
            [admission.training.education_group_type.name],
        )
        self.assertTrue(valuation.est_valorise)

        # Valuated by EPC
        admission.valuated_secondary_studies_person = None
        admission.save(update_fields=['valuated_secondary_studies_person'])
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(admission.candidate.global_id)
        self.assertTrue(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertTrue(valuation.est_valorise)

    def test_with_a_person_with_foreign_high_school_diploma_but_no_admission(self):
        GeneralEducationAdmissionFactory(
            candidate=self.person,
            valuated_secondary_studies_person=self.person,
        )
        diploma = ForeignHighSchoolDiplomaFactory()
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(diploma.person.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

        ForeignHighSchoolDiplomaFactory(external_id='EPC-0')
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(diploma.person.global_id)
        self.assertFalse(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertFalse(valuation.est_valorise)

        # Valuated by EPC
        diploma.external_id = 'EPC-1'
        diploma.save(update_fields=['external_id'])
        valuation = ProfilCandidatTranslator.valorisation_etudes_secondaires(diploma.person.global_id)
        self.assertTrue(valuation.est_valorise_par_epc)
        self.assertEqual(valuation.types_formations_admissions_valorisees, [])
        self.assertTrue(valuation.est_valorise)


class GetAnneePremiereExperienceAcademiqueTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.first_person = PersonFactory()
        cls.second_person = PersonFactory()

    def test_with_no_experience(self):
        result = ProfilCandidatTranslator.get_annee_premiere_experience_academique(matricule='ABCDEF')
        self.assertIsNone(result)

    def test_with_one_experience(self):
        educational_experience = EducationalExperienceFactory(person=self.first_person)

        EducationalExperienceYearFactory(
            educational_experience=educational_experience,
            academic_year__year=2020,
        )

        EducationalExperienceYearFactory(
            educational_experience=educational_experience,
            academic_year__year=2021,
        )

        result = ProfilCandidatTranslator.get_annee_premiere_experience_academique(
            matricule=educational_experience.person.global_id,
        )

        self.assertEqual(result, 2020)

    def test_with_several_experiences(self):
        first_educational_experience = EducationalExperienceFactory(person=self.first_person)

        EducationalExperienceYearFactory(
            educational_experience=first_educational_experience,
            academic_year__year=2020,
        )

        EducationalExperienceYearFactory(
            educational_experience=first_educational_experience,
            academic_year__year=2021,
        )

        second_educational_experience = EducationalExperienceFactory(person=self.first_person)

        EducationalExperienceYearFactory(
            educational_experience=second_educational_experience,
            academic_year__year=2018,
        )

        EducationalExperienceYearFactory(
            educational_experience=second_educational_experience,
            academic_year__year=2022,
        )

        third_educational_experience = EducationalExperienceFactory(
            validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name,
            person=self.first_person,
        )

        EducationalExperienceYearFactory(
            educational_experience=third_educational_experience,
            academic_year__year=2015,
        )

        EducationalExperienceYearFactory(
            educational_experience=third_educational_experience,
            academic_year__year=2016,
        )

        other_person_educational_experience = EducationalExperienceFactory(person=self.second_person)

        EducationalExperienceYearFactory(
            educational_experience=other_person_educational_experience,
            academic_year__year=2014,
        )

        result = ProfilCandidatTranslator.get_annee_premiere_experience_academique(
            matricule=first_educational_experience.person.global_id,
        )

        self.assertEqual(result, 2018)
