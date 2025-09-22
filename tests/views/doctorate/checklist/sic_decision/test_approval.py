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
import datetime

import freezegun
from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import TestCase
from osis_history.models import HistoryEntry

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.shared_kernel.enums.type_demande import TypeDemande
from admission.models import DoctorateAdmission
from admission.models.checklist import AdditionalApprovalCondition
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from admission.tests.views.doctorate.checklist.sic_decision.base import SicPatchMixin
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.scholarship import DoctorateScholarshipFactory


@freezegun.freeze_time('2021-11-01')
class SicApprovalDecisionViewTestCase(SicPatchMixin, TestCase):
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
        cls.european_union_country = CountryFactory(european_union=True)

        AdditionalApprovalCondition.objects.all().delete()
        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
                country_of_citizenship=cls.european_union_country,
            ),
            submitted=True,
            status=ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name,
            determined_academic_year=cls.academic_years[0],
        )
        cls.experience_uuid = str(cls.admission.candidate.educationalexperience_set.first().uuid)
        cls.admission.checklist['current']['parcours_anterieur']['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        cls.admission.save()
        cls.url = resolve_url(
            'admission:doctorate:sic-decision-approval',
            uuid=cls.admission.uuid,
        )
        cls.enrolment_url = resolve_url(
            'admission:doctorate:sic-decision-enrolment-approval',
            uuid=cls.admission.uuid,
        )

    def setUp(self) -> None:
        super().setUp()

        self.admission.candidate.country_of_citizenship = self.european_union_country
        self.admission.candidate.save(update_fields=['country_of_citizenship'])

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
        self.admission.annual_program_contact_person_name = ''
        self.admission.annual_program_contact_person_email = ''
        self.admission.tuition_fees_amount = ''
        self.admission.tuition_fees_amount_other = None
        self.admission.tuition_fees_dispensation = ''
        self.admission.is_mobility = None
        self.admission.mobility_months_amount = ''
        self.admission.must_report_to_sic = None
        self.admission.communication_to_the_candidate = ''
        self.admission.must_provide_student_visa_d = False
        self.admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_approval_form']

        self.assertEqual(form.initial.get('with_prerequisite_courses'), None)
        self.assertEqual(form.initial.get('prerequisite_courses'), [])
        self.assertEqual(form.initial.get('prerequisite_courses_fac_comment'), '')
        self.assertEqual(form.initial.get('annual_program_contact_person_name'), '')
        self.assertEqual(form.initial.get('annual_program_contact_person_email'), '')
        self.assertEqual(form.initial.get('tuition_fees_amount'), '')
        self.assertEqual(form.initial.get('tuition_fees_amount_other'), None)
        self.assertEqual(form.initial.get('tuition_fees_dispensation'), 'NON_CONCERNE')
        self.assertEqual(form.initial.get('is_mobility'), None)
        self.assertEqual(form.initial.get('mobility_months_amount'), '')
        self.assertEqual(form.initial.get('must_report_to_sic'), False)
        self.assertEqual(form.initial.get('communication_to_the_candidate'), '')
        self.assertEqual(form.initial.get('must_provide_student_visa_d'), False)

        # By default, candidate who are not from UE+5 must not provide a student visa
        self.admission.must_provide_student_visa_d = None
        self.admission.save()
        self.admission.candidate.country_of_citizenship = CountryFactory(european_union=False, iso_code='ZB')
        self.admission.candidate.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_approval_form']
        self.assertEqual(form.initial.get('must_provide_student_visa_d'), False)

        self.admission.candidate.country_of_citizenship = CountryFactory(european_union=False, iso_code='CH')
        self.admission.candidate.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_approval_form']
        self.assertEqual(form.initial.get('must_provide_student_visa_d'), None)

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

        self.admission.international_scholarship = DoctorateScholarshipFactory()
        self.admission.save()

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
            'sic-decision-approval-annual_program_contact_person_name': 'John Doe',
            'sic-decision-approval-annual_program_contact_person_email': 'john.doe@example.be',
            'sic-decision-approval-join_program_fac_comment': 'Comment about the join program',
            'sic-decision-approval-tuition_fees_amount': 'NOUVEAUX_DROITS_MAJORES',
            'sic-decision-approval-tuition_fees_dispensation': 'DISPENSE_OFFRE',
            'sic-decision-approval-communication_to_the_candidate': 'Communication',
            'sic-decision-approval-must_provide_student_visa_d': 'on',
        }

        response = self.client.post(self.url, data=data, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get('HX-Refresh'))

        form = response.context['sic_decision_approval_form']

        self.assertTrue(form.is_valid(), form.errors)

        # Check that the admission has been updated
        self.admission.refresh_from_db()

        self.assertEqual(
            self.admission.status,
            ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION.name,
        )
        self.assertEqual(
            self.admission.checklist['current']['decision_sic']['statut'],
            ChoixStatutChecklist.GEST_EN_COURS.name,
        )
        self.assertEqual(
            self.admission.checklist['current']['decision_sic']['extra'],
            {'en_cours': 'approval'},
        )
        self.assertEqual(self.admission.with_prerequisite_courses, True)
        prerequisite_courses_form = self.admission.prerequisite_courses.all()
        self.assertEqual(len(prerequisite_courses), 1)
        self.assertEqual(prerequisite_courses[0], prerequisite_courses_form[0])
        self.assertEqual(
            self.admission.prerequisite_courses_fac_comment,
            'Comment about the additional trainings',
        )
        self.assertEqual(self.admission.annual_program_contact_person_name, 'John Doe')
        self.assertEqual(self.admission.annual_program_contact_person_email, 'john.doe@example.be')
        self.assertEqual(self.admission.tuition_fees_amount, 'NOUVEAUX_DROITS_MAJORES')
        self.assertIsNone(self.admission.tuition_fees_amount_other)
        self.assertEqual(self.admission.tuition_fees_dispensation, 'DISPENSE_OFFRE')
        self.assertEqual(self.admission.is_mobility, None)
        self.assertEqual(self.admission.mobility_months_amount, '')
        self.assertEqual(self.admission.must_report_to_sic, None)
        self.assertEqual(self.admission.communication_to_the_candidate, 'Communication')
        self.assertEqual(self.admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.admission.must_provide_student_visa_d, False)  # False for UE+5 candidates

        # Check that an history entry is created
        entries: QuerySet[HistoryEntry] = HistoryEntry.objects.filter(
            object_uuid=self.admission.uuid,
        )

        self.assertEqual(len(entries), 1)

        self.assertCountEqual(
            ['proposition', 'sic-decision', 'status-changed', 'specify-approval-info'],
            entries[0].tags,
        )

        self.assertEqual(
            entries[0].author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        # Check that no additional history entry is created
        response = self.client.post(self.url, data=data, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)

        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.admission.uuid).count(), 1)

    def test_approval_decision_form_has_is_mobility(self):
        self.client.force_login(user=self.sic_manager_user)
        self.admission.candidate.country_of_citizenship = CountryFactory(european_union=False)
        self.admission.candidate.save()
        response = self.client.get(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        form = response.context['sic_decision_approval_form']

        self.assertIn('is_mobility', form.fields)
        self.assertIn('mobility_months_amount', form.fields)

    def test_approval_decision_form_has_must_report_to_sic_and_must_provide_student_visa_d_for_an_admission(self):
        self.client.force_login(user=self.sic_manager_user)

        self.admission.type_demande = TypeDemande.INSCRIPTION.name
        self.admission.save()
        self.admission.candidate.country_of_citizenship = CountryFactory(european_union=True)
        self.admission.candidate.save()
        response = self.client.get(self.enrolment_url, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        form = response.context['sic_decision_approval_form']

        self.assertNotIn('must_report_to_sic', form.fields)
        self.assertNotIn('must_provide_student_visa_d', form.fields)

        self.admission.type_demande = TypeDemande.ADMISSION.name
        self.admission.save()
        response = self.client.get(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        form = response.context['sic_decision_approval_form']

        self.assertIn('must_report_to_sic', form.fields)
        self.assertNotIn('must_provide_student_visa_d', form.fields)

        # The must provide student visa D field is only available for H(UE+5) countries
        self.admission.candidate.country_of_citizenship = CountryFactory(european_union=False)
        self.admission.candidate.save()

        response = self.client.get(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        form = response.context['sic_decision_approval_form']

        self.assertIn('must_provide_student_visa_d', form.fields)

    def test_approval_decision_form_with_an_enrolment(self):
        self.client.force_login(user=self.sic_manager_user)

        admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
                country_of_citizenship__european_union=True,
            ),
            status=ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name,
            determined_academic_year=self.academic_years[0],
            type_demande=TypeDemande.INSCRIPTION.name,
        )

        admission.checklist['current']['parcours_anterieur']['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        admission.save()

        url = resolve_url('admission:doctorate:sic-decision-enrolment-approval', uuid=admission.uuid)

        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_approval_form']

        # Only a subset of the form fields should be displayed and no one is required
        enrolment_fields = [
            'prerequisite_courses',
            'prerequisite_courses_fac_comment',
            'annual_program_contact_person_name',
            'annual_program_contact_person_email',
            'with_prerequisite_courses',
        ]

        self.assertCountEqual(enrolment_fields, list(form.fields.keys()))

        for field in enrolment_fields:
            self.assertFalse(form.fields[field].required)

        response = self.client.post(
            url,
            data={'sic-decision-approval-with_prerequisite_courses': ''},
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        form = response.context['sic_decision_approval_form']

        self.assertTrue(form.is_valid())

        # Check the admission
        admission.refresh_from_db()

        self.assertEqual(admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(admission.with_prerequisite_courses, None)
        self.assertEqual(admission.annual_program_contact_person_email, '')
        self.assertEqual(admission.annual_program_contact_person_name, '')
        self.assertEqual(admission.prerequisite_courses_fac_comment, '')
        self.assertFalse(admission.prerequisite_courses.exists())
