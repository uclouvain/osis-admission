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

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from osis_history.models import HistoryEntry

from admission.models import DoctorateAdmission
from admission.models.checklist import AdditionalApprovalCondition
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import ChoixStatutChecklist
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from admission.tests.views.doctorate.checklist.sic_decision.base import SicPatchMixin
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


@freezegun.freeze_time('2021-11-01')
class SicEnrolmentApprovalDecisionViewTestCase(SicPatchMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

        AdditionalApprovalCondition.objects.all().delete()
        HistoryEntry.objects.all().delete()
        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            type_demande=TypeDemande.INSCRIPTION.name,
            training=cls.training,
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
                country_of_citizenship__european_union=True,
            ),
            status=ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name,
            determined_academic_year=cls.academic_years[0],
        )
        cls.experience_uuid = str(cls.admission.candidate.educationalexperience_set.first().uuid)
        cls.admission.checklist['current']['parcours_anterieur']['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        cls.admission.save()
        cls.url = resolve_url(
            'admission:doctorate:sic-decision-enrolment-approval',
            uuid=cls.admission.uuid,
        )

    def test_submit_approval_decision_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_approval_decision_form_initialization(self):
        self.client.force_login(user=self.sic_manager_user)

        # No approval data
        self.admission.with_prerequisite_courses = None
        self.admission.prerequisite_courses.set([])
        self.admission.prerequisite_courses_fac_comment = ''
        self.admission.program_planned_years_number = None
        self.admission.annual_program_contact_person_name = ''
        self.admission.annual_program_contact_person_email = ''
        self.admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_approval_form']

        self.assertEqual(form.initial.get('with_prerequisite_courses'), None)
        self.assertEqual(form.initial.get('prerequisite_courses'), [])
        self.assertEqual(form.initial.get('prerequisite_courses_fac_comment'), '')
        self.assertEqual(form.initial.get('program_planned_years_number'), None)
        self.assertEqual(form.initial.get('annual_program_contact_person_name'), '')
        self.assertEqual(form.initial.get('annual_program_contact_person_email'), '')

        for field in [
            'tuition_fees_amount',
            'tuition_fees_amount_other',
            'tuition_fees_dispensation',
            'is_mobility',
            'mobility_months_amount',
            'must_report_to_sic',
            'communication_to_the_candidate',
            'must_provide_student_visa_d',
        ]:
            self.assertIsNone(form.fields.get(field))

        formset = response.context['sic_decision_free_approval_condition_formset']
        self.assertEqual(len(formset.forms), 0)

    def test_approval_decision_form_initialization_other_training(self):
        self.client.force_login(user=self.sic_manager_user)

        # Prerequisite courses
        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.admission.determined_academic_year),
            LearningUnitYearFactory(academic_year=self.admission.determined_academic_year),
        ]
        self.admission.prerequisite_courses.set(prerequisite_courses)
        self.admission.with_prerequisite_courses = True
        self.admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_approval_form']

        # Prerequisite courses
        self.assertEqual(form.initial.get('with_prerequisite_courses'), True)
        self.assertCountEqual(
            form.initial.get('prerequisite_courses'),
            [
                prerequisite_courses[0].acronym,
                prerequisite_courses[1].acronym,
            ],
        )
        self.assertCountEqual(
            form.fields['prerequisite_courses'].choices,
            [
                (
                    prerequisite_courses[0].acronym,
                    f'{prerequisite_courses[0].acronym} - {prerequisite_courses[0].complete_title_i18n}',
                ),
                (
                    prerequisite_courses[1].acronym,
                    f'{prerequisite_courses[1].acronym} - {prerequisite_courses[1].complete_title_i18n}',
                ),
            ],
        )

    def test_approval_decision_form_submitting_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)

        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.admission.determined_academic_year),
        ]

        response = self.client.post(
            self.url,
            data={
                "sic-decision-approval-prerequisite_courses": [prerequisite_courses[0].acronym, "UNKNOWN_ACRONYM"],
                'sic-decision-approval-with_prerequisite_courses': 'True',
                'sic-decision-approval-program_planned_years_number': '',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.headers.get('HX-Refresh'), True)

        form = response.context['sic_decision_approval_form']

        self.assertFalse(form.is_valid())

        # Prerequisite courses
        self.assertCountEqual(
            form.fields['prerequisite_courses'].choices,
            [
                (
                    prerequisite_courses[0].acronym,
                    f'{prerequisite_courses[0].acronym} - {prerequisite_courses[0].complete_title_i18n}',
                ),
            ],
        )
        self.assertIn(
            'Sélectionnez des choix valides. "UNKNOWN_ACRONYM" n’en fait pas partie.',
            form.errors.get('prerequisite_courses', []),
        )

    def test_approval_decision_form_submitting_with_valid_data(self):
        self.client.force_login(user=self.sic_manager_user)

        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.admission.determined_academic_year),
        ]

        data = {
            'sic-decision-approval-CURRICULUM.CURRICULUM': 'ULTERIEUREMENT_BLOQUANT',
            "sic-decision-approval-prerequisite_courses": [
                prerequisite_courses[0].acronym,
            ],
            'sic-decision-approval-with_prerequisite_courses': 'True',
            'sic-decision-approval-prerequisite_courses_fac_comment': 'Comment about the additional trainings',
            'sic-decision-approval-program_planned_years_number': 5,
            'sic-decision-approval-annual_program_contact_person_name': 'John Doe',
            'sic-decision-approval-annual_program_contact_person_email': 'john.doe@example.be',
            'sic-decision-approval-join_program_fac_comment': 'Comment about the join program',
        }

        response = self.client.post(self.url, data=data, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get('HX-Refresh'))

        form = response.context['sic_decision_approval_form']
        formset = response.context['sic_decision_free_approval_condition_formset']

        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(formset.is_valid())

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(
            self.admission.status,
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name,
        )
        self.assertEqual(self.admission.with_prerequisite_courses, True)
        prerequisite_courses_form = self.admission.prerequisite_courses.all()
        self.assertEqual(len(prerequisite_courses), 1)
        self.assertEqual(prerequisite_courses[0], prerequisite_courses_form[0])
        self.assertEqual(
            self.admission.prerequisite_courses_fac_comment,
            'Comment about the additional trainings',
        )
        self.assertEqual(self.admission.program_planned_years_number, 5)
        self.assertEqual(self.admission.annual_program_contact_person_name, 'John Doe')
        self.assertEqual(self.admission.annual_program_contact_person_email, 'john.doe@example.be')
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.today())
