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
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext
from osis_history.models import HistoryEntry

from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.checklist import AdditionalApprovalCondition, FreeAdditionalApprovalCondition
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.tests.factories.faculty_decision import (
    AdditionalApprovalConditionFactory,
    FreeAdditionalApprovalConditionFactory,
)
from admission.tests.factories.general_education import (
    GeneralEducationTrainingFactory,
    GeneralEducationAdmissionFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from admission.tests.factories.scholarship import ErasmusMundusScholarshipFactory
from admission.tests.views.general_education.checklist.sic_decision.base import SicPatchMixin
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2021-11-01')
class SicApprovalDecisionViewTestCase(SicPatchMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}

        AdditionalApprovalCondition.objects.all().delete()
        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(
                language=settings.LANGUAGE_CODE_FR,
                country_of_citizenship__european_union=True,
            ),
            status=ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name,
            determined_academic_year=cls.academic_years[0],
        )
        cls.experience_uuid = str(cls.general_admission.candidate.educationalexperience_set.first().uuid)
        cls.general_admission.checklist['current']['parcours_anterieur'][
            'statut'
        ] = ChoixStatutChecklist.GEST_REUSSITE.name
        cls.general_admission.save()
        cls.url = resolve_url(
            'admission:general-education:sic-decision-approval',
            uuid=cls.general_admission.uuid,
        )

    def test_submit_approval_decision_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_approval_decision_form_initialization(self):
        self.client.force_login(user=self.sic_manager_user)

        # No approval data
        self.general_admission.with_additional_approval_conditions = None
        self.general_admission.additional_approval_conditions.set([])
        self.general_admission.freeadditionalapprovalcondition_set.all().delete()
        self.general_admission.with_prerequisite_courses = None
        self.general_admission.prerequisite_courses.set([])
        self.general_admission.prerequisite_courses_fac_comment = ''
        self.general_admission.program_planned_years_number = None
        self.general_admission.annual_program_contact_person_name = ''
        self.general_admission.annual_program_contact_person_email = ''
        self.general_admission.tuition_fees_amount = ''
        self.general_admission.tuition_fees_amount_other = None
        self.general_admission.tuition_fees_dispensation = ''
        self.general_admission.particular_cost = ''
        self.general_admission.rebilling_or_third_party_payer = ''
        self.general_admission.first_year_inscription_and_status = ''
        self.general_admission.is_mobility = None
        self.general_admission.mobility_months_amount = ''
        self.general_admission.must_report_to_sic = None
        self.general_admission.communication_to_the_candidate = ''
        self.general_admission.must_provide_student_visa_d = False
        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_approval_form']

        self.assertEqual(form.initial.get('with_prerequisite_courses'), None)
        self.assertEqual(form.initial.get('prerequisite_courses'), [])
        self.assertEqual(form.initial.get('prerequisite_courses_fac_comment'), '')
        self.assertEqual(form.initial.get('program_planned_years_number'), None)
        self.assertEqual(form.initial.get('annual_program_contact_person_name'), '')
        self.assertEqual(form.initial.get('annual_program_contact_person_email'), '')
        self.assertEqual(form.initial.get('with_additional_approval_conditions'), None)
        self.assertEqual(form.initial.get('all_additional_approval_conditions'), [])
        self.assertEqual(form.initial.get('tuition_fees_amount'), '')
        self.assertEqual(form.initial.get('tuition_fees_amount_other'), None)
        self.assertEqual(form.initial.get('tuition_fees_dispensation'), 'NON_CONCERNE')
        self.assertEqual(form.initial.get('particular_cost'), '')
        self.assertEqual(form.initial.get('rebilling_or_third_party_payer'), '')
        self.assertEqual(form.initial.get('first_year_inscription_and_status'), '')
        self.assertEqual(form.initial.get('is_mobility'), None)
        self.assertEqual(form.initial.get('mobility_months_amount'), '')
        self.assertEqual(form.initial.get('must_report_to_sic'), False)
        self.assertEqual(form.initial.get('communication_to_the_candidate'), '')
        self.assertEqual(form.initial.get('must_provide_student_visa_d'), False)

        formset = response.context['sic_decision_free_approval_condition_formset']
        self.assertEqual(len(formset.forms), 0)

        # By default, candidate who are not from UE+5 must provide a student visa
        self.general_admission.candidate.country_of_citizenship = CountryFactory(european_union=False, iso_code='ZB')
        self.general_admission.candidate.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_approval_form']
        self.assertEqual(form.initial.get('must_provide_student_visa_d'), True)

        self.general_admission.candidate.country_of_citizenship = CountryFactory(european_union=False, iso_code='CH')
        self.general_admission.candidate.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_approval_form']
        self.assertEqual(form.initial.get('must_provide_student_visa_d'), False)

    def test_approval_decision_form_initialization_other_training(self):
        self.client.force_login(user=self.sic_manager_user)

        # Prerequisite courses
        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.general_admission.determined_academic_year),
            LearningUnitYearFactory(academic_year=self.general_admission.determined_academic_year),
        ]
        self.general_admission.prerequisite_courses.set(prerequisite_courses)
        self.general_admission.with_prerequisite_courses = True

        # Additional approval conditions
        approval_conditions = [
            AdditionalApprovalConditionFactory(),
            AdditionalApprovalConditionFactory(),
        ]
        self.general_admission.additional_approval_conditions.set(approval_conditions)
        self.general_admission.with_additional_approval_conditions = True

        free_approval_conditions = [
            FreeAdditionalApprovalConditionFactory(
                name_fr='Première condition libre',
                name_en='First free condition',
                admission=self.general_admission,
            ),
            FreeAdditionalApprovalConditionFactory(
                name_fr='Deuxième condition libre',
                name_en='Second free condition',
                admission=self.general_admission,
                related_experience=self.general_admission.candidate.educationalexperience_set.first(),
            ),
        ]

        self.general_admission.save()

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

        # Additional approval conditions
        self.assertEqual(form.initial.get('with_additional_approval_conditions'), True)
        self.assertCountEqual(
            form.initial.get('all_additional_approval_conditions'),
            [
                approval_conditions[0].uuid,
                approval_conditions[1].uuid,
                free_approval_conditions[1].related_experience_id,
            ],
        )
        self.assertCountEqual(
            form.fields['all_additional_approval_conditions'].choices,
            [
                (
                    str(free_approval_conditions[1].related_experience_id),
                    gettext('Graduation of {program_name}').format(program_name='Computer science'),
                ),
                (
                    approval_conditions[0].uuid,
                    approval_conditions[0].name_fr,
                ),
                (
                    approval_conditions[1].uuid,
                    approval_conditions[1].name_fr,
                ),
            ],
        )

        formset = response.context['sic_decision_free_approval_condition_formset']
        self.assertEqual(len(formset.forms), 1)
        self.assertEqual(
            formset.forms[0].initial,
            {
                'name_fr': free_approval_conditions[0].name_fr,
                'name_en': free_approval_conditions[0].name_en,
            },
        )

    def test_approval_decision_form_submitting_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)

        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.general_admission.determined_academic_year),
        ]

        approval_conditions = [
            AdditionalApprovalConditionFactory(),
        ]

        response = self.client.post(
            self.url,
            data={
                "sic-decision-approval-prerequisite_courses": [prerequisite_courses[0].acronym, "UNKNOWN_ACRONYM"],
                'sic-decision-approval-with_prerequisite_courses': 'True',
                'sic-decision-approval-with_additional_approval_conditions': 'True',
                'sic-decision-approval-all_additional_approval_conditions': [
                    approval_conditions[0].uuid,
                    'Free condition',
                ],
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

        # Additional approval conditions
        self.assertCountEqual(
            form.fields['all_additional_approval_conditions'].choices,
            [
                (approval_conditions[0].uuid, approval_conditions[0].name_fr),
                (
                    self.experience_uuid,
                    gettext('Graduation of {program_name}').format(program_name='Computer science'),
                ),
            ],
        )

    def test_approval_decision_form_submitting_with_valid_data(self):
        self.client.force_login(user=self.sic_manager_user)

        prerequisite_courses = [
            LearningUnitYearFactory(academic_year=self.general_admission.determined_academic_year),
        ]

        approval_conditions = [
            AdditionalApprovalConditionFactory(),
        ]

        data = {
            'sic-decision-approval-CURRICULUM.CURRICULUM': 'ULTERIEUREMENT_BLOQUANT',
            "sic-decision-approval-prerequisite_courses": [
                prerequisite_courses[0].acronym,
            ],
            'sic-decision-approval-with_prerequisite_courses': 'True',
            'sic-decision-approval-with_additional_approval_conditions': 'True',
            'sic-decision-approval-all_additional_approval_conditions': [
                approval_conditions[0].uuid,
                self.experience_uuid,
            ],
            'sic-decision-approval-prerequisite_courses_fac_comment': 'Comment about the additional trainings',
            'sic-decision-approval-program_planned_years_number': 5,
            'sic-decision-approval-annual_program_contact_person_name': 'John Doe',
            'sic-decision-approval-annual_program_contact_person_email': 'john.doe@example.be',
            'sic-decision-approval-join_program_fac_comment': 'Comment about the join program',
            'sic-decision-approval-tuition_fees_amount': 'NOUVEAUX_DROITS_MAJORES',
            'sic-decision-approval-tuition_fees_dispensation': 'DISPENSE_OFFRE',
            'sic-decision-approval-particular_cost': 'particular_cost',
            'sic-decision-approval-rebilling_or_third_party_payer': 'rebilling_or_third_party_payer',
            'sic-decision-approval-first_year_inscription_and_status': 'first_year_inscription_and_status',
            'sic-decision-approval-communication_to_the_candidate': 'Communication',
            'sic-decision-approval-must_provide_student_visa_d': 'on',
            'sic-decision-TOTAL_FORMS': '2',
            'sic-decision-INITIAL_FORMS': '0',
            'sic-decision-MIN_NUM_FORMS': '0',
            'sic-decision-MAX_NUM_FORMS': '1000',
            'sic-decision-0-name_fr': 'Ma première condition',
            'sic-decision-0-name_en': '',
            'sic-decision-1-name_fr': 'Ma seconde condition',
            'sic-decision-1-name_en': 'My second condition',
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
        self.general_admission.refresh_from_db()

        self.assertEqual(
            self.general_admission.status,
            ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['statut'],
            ChoixStatutChecklist.GEST_EN_COURS.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['extra'],
            {'en_cours': 'approval'},
        )
        self.assertEqual(self.general_admission.with_additional_approval_conditions, True)
        approval_conditions_form = self.general_admission.additional_approval_conditions.all()
        self.assertEqual(len(approval_conditions), 1)
        self.assertEqual(approval_conditions[0], approval_conditions_form[0])
        self.assertEqual(self.general_admission.with_prerequisite_courses, True)
        prerequisite_courses_form = self.general_admission.prerequisite_courses.all()
        self.assertEqual(len(prerequisite_courses), 1)
        self.assertEqual(prerequisite_courses[0], prerequisite_courses_form[0])
        self.assertEqual(
            self.general_admission.prerequisite_courses_fac_comment,
            'Comment about the additional trainings',
        )
        self.assertEqual(self.general_admission.program_planned_years_number, 5)
        self.assertEqual(self.general_admission.annual_program_contact_person_name, 'John Doe')
        self.assertEqual(self.general_admission.annual_program_contact_person_email, 'john.doe@example.be')
        self.assertEqual(self.general_admission.tuition_fees_amount, 'NOUVEAUX_DROITS_MAJORES')
        self.assertIsNone(self.general_admission.tuition_fees_amount_other)
        self.assertEqual(self.general_admission.tuition_fees_dispensation, 'DISPENSE_OFFRE')
        self.assertEqual(self.general_admission.particular_cost, 'particular_cost')
        self.assertEqual(self.general_admission.rebilling_or_third_party_payer, 'rebilling_or_third_party_payer')
        self.assertEqual(self.general_admission.first_year_inscription_and_status, 'first_year_inscription_and_status')
        self.assertEqual(self.general_admission.is_mobility, None)
        self.assertEqual(self.general_admission.mobility_months_amount, '')
        self.assertEqual(self.general_admission.must_report_to_sic, None)
        self.assertEqual(self.general_admission.communication_to_the_candidate, 'Communication')
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.today())
        self.assertEqual(self.general_admission.must_provide_student_visa_d, False)  # False for UE+5 candidates

        # Check the creation of the free additional conditions
        conditions: QuerySet[FreeAdditionalApprovalCondition] = FreeAdditionalApprovalCondition.objects.filter(
            admission=self.general_admission
        ).order_by('name_fr')
        self.assertEqual(len(conditions), 3)
        self.assertEqual(conditions[0].name_fr, 'L\'obtention de votre diplôme de Computer science')
        self.assertEqual(conditions[0].name_en, 'Graduation of Computer science')
        self.assertEqual(str(conditions[0].related_experience_id), self.experience_uuid)
        self.assertEqual(conditions[1].name_fr, 'Ma première condition')
        self.assertEqual(conditions[1].name_en, '')
        self.assertIsNone(conditions[1].related_experience)
        self.assertEqual(conditions[2].name_fr, 'Ma seconde condition')
        self.assertEqual(conditions[2].name_en, 'My second condition')
        self.assertIsNone(conditions[2].related_experience)

        # Check that an history entry is created
        entries: QuerySet[HistoryEntry] = HistoryEntry.objects.filter(
            object_uuid=self.general_admission.uuid,
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

        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid).count(), 1)

    def test_approval_decision_form_has_is_mobility(self):
        self.client.force_login(user=self.sic_manager_user)
        self.general_admission.candidate.country_of_citizenship = CountryFactory(european_union=False)
        self.general_admission.candidate.save()
        response = self.client.get(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        form = response.context['sic_decision_approval_form']

        self.assertIn('is_mobility', form.fields)
        self.assertIn('mobility_months_amount', form.fields)

    def test_approval_decision_form_has_must_report_to_sic_and_must_provide_student_visa_d_for_an_admission(self):
        self.client.force_login(user=self.sic_manager_user)

        self.general_admission.type_demande = TypeDemande.INSCRIPTION.name
        self.general_admission.save()
        self.general_admission.candidate.country_of_citizenship = CountryFactory(european_union=True)
        self.general_admission.candidate.save()
        response = self.client.get(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        form = response.context['sic_decision_approval_form']

        self.assertNotIn('must_report_to_sic', form.fields)
        self.assertNotIn('must_provide_student_visa_d', form.fields)

        self.general_admission.type_demande = TypeDemande.ADMISSION.name
        self.general_admission.save()
        response = self.client.get(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        form = response.context['sic_decision_approval_form']

        self.assertIn('must_report_to_sic', form.fields)
        self.assertNotIn('must_provide_student_visa_d', form.fields)

        # The must provide student visa D field is only available for H(UE+5) countries
        self.general_admission.candidate.country_of_citizenship = CountryFactory(european_union=False)
        self.general_admission.candidate.save()

        response = self.client.get(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        form = response.context['sic_decision_approval_form']

        self.assertIn('must_provide_student_visa_d', form.fields)

    def test_approval_decision_form_has_vip_fields(self):
        self.client.force_login(user=self.sic_manager_user)
        self.general_admission.erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory()
        self.general_admission.save()
        response = self.client.get(self.url, **self.default_headers)
        self.assertEqual(response.status_code, 200)
        form = response.context['sic_decision_approval_form']

        self.assertIn('particular_cost', form.fields)
        self.assertIn('rebilling_or_third_party_payer', form.fields)
        self.assertIn('first_year_inscription_and_status', form.fields)
