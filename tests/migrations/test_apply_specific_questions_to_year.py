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

from django.test import TestCase

from admission.migrations.utils.apply_specific_questions_to_year import (
    apply_specific_questions_to_year,
)
from admission.models import AdmissionFormItem, AdmissionFormItemInstantiation
from admission.tests.factories.form_item import (
    AdmissionFormItemInstantiationFactory,
    MessageAdmissionFormItemFactory,
)
from base.models.academic_year import AcademicYear
from base.tests.factories.academic_year import AcademicYearFactory


class ApplySpecificQuestionsToYearTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = {
            academic_year.year: academic_year for academic_year in AcademicYearFactory.produce(2024, number_future=2)
        }

    def setUp(self):
        AdmissionFormItemInstantiation.objects.all().delete()
        AdmissionFormItem.objects.all().delete()
        self.messages = [MessageAdmissionFormItemFactory(internal_label=f'message_{i}') for i in range(0, 3)]

    def _apply_specific_questions_to_year(self, **kwargs):
        apply_specific_questions_to_year(
            form_item_instantiation_model=AdmissionFormItemInstantiation,
            academic_year_model=AcademicYear,
            **kwargs,
        )

    def test_apply_if_there_is_no_target_year(self):
        self._apply_specific_questions_to_year(
            form_item_internal_labels=['a'],
            from_year=2024,
            to_year=1800,
        )

        self.assertEqual(AdmissionFormItemInstantiation.objects.count(), 0)

    def test_apply_if_there_no_passed_label(self):
        self._apply_specific_questions_to_year(
            form_item_internal_labels=[],
            from_year=2024,
            to_year=2025,
        )

        self.assertEqual(AdmissionFormItemInstantiation.objects.count(), 0)

    def test_apply_with_existing_questions(self):
        first_message_2023 = AdmissionFormItemInstantiationFactory(
            academic_year__year=2023,
            form_item=self.messages[0],
        )
        first_message_2024 = AdmissionFormItemInstantiationFactory(
            academic_year__year=2024,
            form_item=self.messages[0],
        )
        second_message_2023 = AdmissionFormItemInstantiationFactory(
            academic_year__year=2023,
            form_item=self.messages[1],
        )
        third_message_2025 = AdmissionFormItemInstantiationFactory(
            academic_year__year=2025,
            form_item=self.messages[2],
        )

        self._apply_specific_questions_to_year(
            form_item_internal_labels=[
                self.messages[0].internal_label,
                self.messages[1].internal_label,
                self.messages[2].internal_label,
            ],
            from_year=2022,
            to_year=2025,
        )
        self.assertEqual(self.messages[0].admissionformiteminstantiation_set.count(), 2)
        self.assertEqual(self.messages[1].admissionformiteminstantiation_set.count(), 1)
        self.assertEqual(self.messages[2].admissionformiteminstantiation_set.count(), 1)

        self._apply_specific_questions_to_year(
            form_item_internal_labels=[
                self.messages[0].internal_label,
                self.messages[1].internal_label,
                self.messages[2].internal_label,
            ],
            from_year=2023,
            to_year=2025,
        )

        first_message_instantiations = (
            self.messages[0].admissionformiteminstantiation_set.all().order_by('academic_year__year')
        )
        second_message_instantiations = (
            self.messages[1].admissionformiteminstantiation_set.all().order_by('academic_year__year')
        )
        third_message_instantiations = (
            self.messages[2].admissionformiteminstantiation_set.all().order_by('academic_year__year')
        )

        self.assertEqual(len(first_message_instantiations), 3)
        self.assertEqual(len(second_message_instantiations), 2)
        self.assertEqual(len(third_message_instantiations), 1)

        first_message_2025 = first_message_instantiations[2]
        self.assertEqual(first_message_2025.form_item, first_message_2023.form_item)
        self.assertEqual(first_message_2025.academic_year, self.academic_years[2025])
        self.assertEqual(first_message_2025.weight, first_message_2023.weight)
        self.assertEqual(first_message_2025.required, first_message_2023.required)
        self.assertEqual(first_message_2025.display_according_education, first_message_2023.display_according_education)
        self.assertEqual(first_message_2025.education_group_type, first_message_2023.education_group_type)
        self.assertEqual(first_message_2025.education_group, first_message_2023.education_group)
        self.assertEqual(first_message_2025.admission, first_message_2023.admission)
        self.assertEqual(first_message_2025.candidate_nationality, first_message_2023.candidate_nationality)
        self.assertEqual(first_message_2025.diploma_nationality, first_message_2023.diploma_nationality)
        self.assertEqual(first_message_2025.study_language, first_message_2023.study_language)
        self.assertEqual(first_message_2025.vip_candidate, first_message_2023.vip_candidate)
        self.assertEqual(first_message_2025.tab, first_message_2023.tab)

        second_message_2025 = second_message_instantiations[1]
        self.assertEqual(second_message_2025.form_item, second_message_2023.form_item)
        self.assertEqual(second_message_2025.academic_year, self.academic_years[2025])
        self.assertEqual(second_message_2025.weight, second_message_2023.weight)
        self.assertEqual(second_message_2025.required, second_message_2023.required)
        self.assertEqual(
            second_message_2025.display_according_education, second_message_2023.display_according_education
        )
        self.assertEqual(second_message_2025.education_group_type, second_message_2023.education_group_type)
        self.assertEqual(second_message_2025.education_group, second_message_2023.education_group)
        self.assertEqual(second_message_2025.admission, second_message_2023.admission)
        self.assertEqual(second_message_2025.candidate_nationality, second_message_2023.candidate_nationality)
        self.assertEqual(second_message_2025.diploma_nationality, second_message_2023.diploma_nationality)
        self.assertEqual(second_message_2025.study_language, second_message_2023.study_language)
        self.assertEqual(second_message_2025.vip_candidate, second_message_2023.vip_candidate)
        self.assertEqual(second_message_2025.tab, second_message_2023.tab)

        self._apply_specific_questions_to_year(
            form_item_internal_labels=[
                self.messages[2].internal_label,
            ],
            from_year=2025,
            to_year=2026,
        )

        first_message_instantiations = (
            self.messages[0].admissionformiteminstantiation_set.all().order_by('academic_year__year')
        )
        second_message_instantiations = (
            self.messages[1].admissionformiteminstantiation_set.all().order_by('academic_year__year')
        )
        third_message_instantiations = (
            self.messages[2].admissionformiteminstantiation_set.all().order_by('academic_year__year')
        )

        self.assertEqual(len(first_message_instantiations), 3)
        self.assertEqual(len(second_message_instantiations), 2)
        self.assertEqual(len(third_message_instantiations), 2)

        third_message_2026 = third_message_instantiations[1]
        self.assertEqual(third_message_2026.form_item, third_message_2025.form_item)
        self.assertEqual(third_message_2026.academic_year, self.academic_years[2026])
        self.assertEqual(third_message_2026.weight, third_message_2025.weight)
        self.assertEqual(third_message_2026.required, third_message_2025.required)
        self.assertEqual(third_message_2026.display_according_education, third_message_2025.display_according_education)
        self.assertEqual(third_message_2026.education_group_type, third_message_2025.education_group_type)
        self.assertEqual(third_message_2026.education_group, third_message_2025.education_group)
        self.assertEqual(third_message_2026.admission, third_message_2025.admission)
        self.assertEqual(third_message_2026.candidate_nationality, third_message_2025.candidate_nationality)
        self.assertEqual(third_message_2026.diploma_nationality, third_message_2025.diploma_nationality)
        self.assertEqual(third_message_2026.study_language, third_message_2025.study_language)
        self.assertEqual(third_message_2026.vip_candidate, third_message_2025.vip_candidate)
        self.assertEqual(third_message_2026.tab, third_message_2025.tab)
