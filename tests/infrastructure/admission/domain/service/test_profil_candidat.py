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
from django.test import TestCase

from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.secondary_studies import (
    HighSchoolDiplomaAlternativeFactory,
    BelgianHighSchoolDiplomaFactory,
    ForeignHighSchoolDiplomaFactory,
)
from base.tests.factories.person import PersonFactory


class EtudesSecondairesValoriseesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        super().setUpTestData()

    def test_with_an_unknown_person(self):
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees("unknown"))

    def test_with_a_person_without_admission_or_diploma(self):
        person = PersonFactory()
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(person.global_id))

    def test_with_a_person_with_admission_but_no_diploma(self):
        admission = GeneralEducationAdmissionFactory()
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

        # Valuated by an admission
        admission = GeneralEducationAdmissionFactory(
            candidate=admission.candidate,
            valuated_secondary_studies_person=admission.candidate,
        )
        self.assertTrue(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

    def test_with_a_person_with_admission_and_high_school_diploma_alternative(self):
        admission = GeneralEducationAdmissionFactory()
        diploma = HighSchoolDiplomaAlternativeFactory()
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

        diploma.person = admission.candidate
        diploma.save(update_fields=['person'])
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

        # Valuated by an admission
        admission = GeneralEducationAdmissionFactory(
            candidate=admission.candidate,
            valuated_secondary_studies_person=admission.candidate,
        )
        self.assertTrue(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

    def test_with_a_person_with_high_school_diploma_alternative_but_no_admission(self):
        admission = GeneralEducationAdmissionFactory(
            candidate=self.person,
            valuated_secondary_studies_person=self.person,
        )
        diploma = HighSchoolDiplomaAlternativeFactory()
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(diploma.person.global_id))

    def test_with_a_person_with_admission_and_belgian_high_school_diploma(self):
        admission = GeneralEducationAdmissionFactory()
        diploma = BelgianHighSchoolDiplomaFactory()
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

        diploma.person = admission.candidate
        diploma.save(update_fields=['person'])
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

        # Valuated by an admission
        admission = GeneralEducationAdmissionFactory(
            candidate=admission.candidate,
            valuated_secondary_studies_person=admission.candidate,
        )
        self.assertTrue(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

        # Valuated by an admission and EPC
        diploma.external_id = 'EPC-1'
        diploma.save(update_fields=['external_id'])
        self.assertTrue(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

        # Valuated by EPC
        admission.valuated_secondary_studies_person = None
        admission.save(update_fields=['valuated_secondary_studies_person'])
        self.assertTrue(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

    def test_with_a_person_with_belgian_high_school_diploma_but_no_admission(self):
        admission = GeneralEducationAdmissionFactory(
            candidate=self.person,
            valuated_secondary_studies_person=self.person,
        )
        diploma = BelgianHighSchoolDiplomaFactory()
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(diploma.person.global_id))

        other_diploma = BelgianHighSchoolDiplomaFactory(external_id='EPC-0')
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(diploma.person.global_id))

        # Valuated by EPC
        diploma.external_id = 'EPC-1'
        diploma.save(update_fields=['external_id'])
        self.assertTrue(ProfilCandidatTranslator.etudes_secondaires_valorisees(diploma.person.global_id))

    def test_with_a_person_with_admission_and_foreign_high_school_diploma(self):
        admission = GeneralEducationAdmissionFactory()
        diploma = ForeignHighSchoolDiplomaFactory()
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

        diploma.person = admission.candidate
        diploma.save(update_fields=['person'])
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

        # Valuated by an admission
        admission = GeneralEducationAdmissionFactory(
            candidate=admission.candidate,
            valuated_secondary_studies_person=admission.candidate,
        )
        self.assertTrue(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

        # Valuated by an admission and EPC
        diploma.external_id = 'EPC-1'
        diploma.save(update_fields=['external_id'])
        self.assertTrue(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

        # Valuated by EPC
        admission.valuated_secondary_studies_person = None
        admission.save(update_fields=['valuated_secondary_studies_person'])
        self.assertTrue(ProfilCandidatTranslator.etudes_secondaires_valorisees(admission.candidate.global_id))

    def test_with_a_person_with_foreign_high_school_diploma_but_no_admission(self):
        admission = GeneralEducationAdmissionFactory(
            candidate=self.person,
            valuated_secondary_studies_person=self.person,
        )
        diploma = ForeignHighSchoolDiplomaFactory()
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(diploma.person.global_id))

        other_diploma = ForeignHighSchoolDiplomaFactory(external_id='EPC-0')
        self.assertFalse(ProfilCandidatTranslator.etudes_secondaires_valorisees(diploma.person.global_id))

        # Valuated by EPC
        diploma.external_id = 'EPC-1'
        diploma.save(update_fields=['external_id'])
        self.assertTrue(ProfilCandidatTranslator.etudes_secondaires_valorisees(diploma.person.global_id))
