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

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.contrib.models import DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import (
    ENTITY_CDE,
    ENTITY_CDSS,
    SIGLE_SCIENCES,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.domain.enums import TypeFormation
from admission.ddd.admission.enums import Onglets
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.form_item import AdmissionFormItemInstantiationFactory, TextAdmissionFormItemFactory
from admission.tests.factories.roles import (
    SicManagementRoleFactory,
    CandidateFactory,
    ProgramManagerRoleFactory,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.forms.utils.choice_field import BLANK_CHOICE_DISPLAY
from base.models.campus import Campus
from base.models.enums.entity_type import EntityType
from base.models.enums.organization_type import MAIN
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity_version import EntityVersionFactory
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2021-12-01')
class DoctorateTrainingChoiceFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')

        cls.first_campus = CampusFactory(name='Louvain-La-Neuve', organization__type=MAIN)
        cls.all_campuses = Campus.objects.filter(organization__type=MAIN)

        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
            title='Sector name',
        ).entity

        cls.other_commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.other_commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.cde_commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym=ENTITY_CDE,
        ).entity
        cls.cdss_commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym=ENTITY_CDSS,
        ).entity
        cls.science_commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDSC',
        ).entity

        cls.specific_questions = [
            AdmissionFormItemInstantiationFactory(
                form_item=TextAdmissionFormItemFactory(),
                tab=Onglets.CHOIX_FORMATION.name,
                academic_year=cls.academic_years[0],
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=TextAdmissionFormItemFactory(),
                tab=Onglets.CURRICULUM.name,
                academic_year=cls.academic_years[0],
            ),
        ]

        cls.specific_questions_uuids = [str(question.form_item.uuid) for question in cls.specific_questions]

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.sector).person.user

    def setUp(self):
        self.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=self.other_commission,
            training__academic_year=self.academic_years[0],
            determined_academic_year=self.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__id_photo=[],
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            comment='Comment about the admission',
            type=ChoixTypeAdmission.ADMISSION.name,
            specific_question_answers={
                self.specific_questions_uuids[0]: 'My answer 1',
                self.specific_questions_uuids[1]: 'My answer 2',
            },
        )

        root_group = self.doctorate_admission.training.educationgroupversion_set.first().root_group
        root_group.main_teaching_campus = self.first_campus
        root_group.save()

        self.doctorate_url = resolve_url(
            'admission:doctorate:update:training-choice',
            uuid=self.doctorate_admission.uuid,
        )
        self.doctorate_details_url = resolve_url(
            'admission:doctorate:training-choice',
            uuid=self.doctorate_admission.uuid,
        )

    def test_doctorate_training_choice_access(self):
        # If the user is not authenticated, they should be redirected to the login page
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + self.doctorate_url)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, they should be able to access the page
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.doctorate_admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.doctorate_admission.save()
        program_manager_user = ProgramManagerRoleFactory(
            education_group=self.doctorate_admission.training.education_group
        ).person.user
        self.client.force_login(program_manager_user)
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_training_choice_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['admission'].uuid, self.doctorate_admission.uuid)

        form = response.context['form']

        # Check form fields

        # Initial values
        self.assertEqual(form['training_type'].value(), TypeFormation.DOCTORAT.name)
        self.assertEqual(form['campus'].value(), self.first_campus.uuid)
        self.assertEqual(form['doctorate_training'].value(), self.doctorate_admission.training.acronym)
        self.assertEqual(form['admission_type'].value(), self.doctorate_admission.type)
        self.assertEqual(form['justification'].value(), self.doctorate_admission.comment)
        self.assertEqual(form['sector'].value(), 'SST')
        self.assertEqual(form['specific_question_answers'].value(), self.doctorate_admission.specific_question_answers)
        self.assertEqual(form['proximity_commission_cde'].value(), None)
        self.assertEqual(form['proximity_commission_cdss'].value(), None)
        self.assertEqual(form['science_sub_domain'].value(), None)

        # Choices
        self.assertCountEqual(form.fields['training_type'].choices, TypeFormation.choices())

        self.assertEqual(form.initial['campus'], self.first_campus.uuid)
        self.assertCountEqual(
            form.fields['campus'].choices,
            [
                ('', BLANK_CHOICE_DISPLAY),
                *[(campus.uuid, campus.name) for campus in self.all_campuses],
            ],
        )
        self.assertCountEqual(
            form.fields['doctorate_training'].choices,
            [
                [
                    self.doctorate_admission.training.acronym,
                    '{} ({}) <span class="training-acronym">{}</span>'.format(
                        self.doctorate_admission.training.title,
                        self.first_campus.name,
                        self.doctorate_admission.training.acronym,
                    ),
                ]
            ],
        )
        self.assertCountEqual(form.fields['sector'].choices, [['SST', 'Sector name']])

        # Disabled fields
        self.assertEqual(form.fields['training_type'].disabled, True)
        self.assertEqual(form.fields['training_type'].required, False)

        self.assertEqual(form.fields['campus'].disabled, True)
        self.assertEqual(form.fields['campus'].required, False)

        self.assertEqual(form.fields['doctorate_training'].disabled, True)

        # Check proximity commission values
        # CDE
        self.doctorate_admission.training.management_entity = self.cde_commission
        self.doctorate_admission.proximity_commission = ChoixCommissionProximiteCDEouCLSM.MANAGEMENT.name
        self.doctorate_admission.training.save(update_fields=['management_entity'])
        self.doctorate_admission.save(update_fields=['proximity_commission'])

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        form = response.context['form']

        self.assertEqual(form['proximity_commission_cde'].value(), ChoixCommissionProximiteCDEouCLSM.MANAGEMENT.name)
        self.assertEqual(form['proximity_commission_cdss'].value(), None)
        self.assertEqual(form['science_sub_domain'].value(), None)

        # CDSS
        self.doctorate_admission.training.management_entity = self.cdss_commission
        self.doctorate_admission.proximity_commission = ChoixCommissionProximiteCDSS.BCM.name
        self.doctorate_admission.training.save(update_fields=['management_entity'])
        self.doctorate_admission.save(update_fields=['proximity_commission'])

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        form = response.context['form']

        self.assertEqual(form['proximity_commission_cde'].value(), None)
        self.assertEqual(form['proximity_commission_cdss'].value(), ChoixCommissionProximiteCDSS.BCM.name)
        self.assertEqual(form['science_sub_domain'].value(), None)

        # Sciences
        self.doctorate_admission.training.management_entity = self.science_commission
        self.doctorate_admission.training.acronym = SIGLE_SCIENCES
        self.doctorate_admission.proximity_commission = ChoixSousDomaineSciences.MATHEMATICS.name
        self.doctorate_admission.training.save(update_fields=['management_entity', 'acronym'])
        self.doctorate_admission.save(update_fields=['proximity_commission'])

        response = self.client.get(self.doctorate_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        form = response.context['form']

        self.assertEqual(form['proximity_commission_cde'].value(), None)
        self.assertEqual(form['proximity_commission_cdss'].value(), None)
        self.assertEqual(form['science_sub_domain'].value(), ChoixSousDomaineSciences.MATHEMATICS.name)

    @freezegun.freeze_time('2021-12-01')
    def test_form_submit_with_valid_data(self):
        self.client.force_login(self.sic_manager_user)

        default_data = {
            'admission_type': ChoixTypeAdmission.ADMISSION.name,
            'justification': 'My justification',
            'proximity_commission_cde': ChoixCommissionProximiteCDEouCLSM.MANAGEMENT.name,
            'proximity_commission_cdss': ChoixCommissionProximiteCDSS.BCM.name,
            'science_sub_domain': ChoixSousDomaineSciences.MATHEMATICS.name,
            'specific_question_answers_0': 'My answer 1 updated',
            'specific_question_answers_2': 'My answer 2 updated',
        }

        # Pre-Admission
        response = self.client.post(
            self.doctorate_url,
            {
                **default_data,
                'admission_type': ChoixTypeAdmission.PRE_ADMISSION.name,
            },
        )

        self.assertRedirects(response=response, expected_url=self.doctorate_details_url, fetch_redirect_response=False)

        self.doctorate_admission.refresh_from_db()

        self.assertEqual(self.doctorate_admission.type, ChoixTypeAdmission.PRE_ADMISSION.name)
        self.assertEqual(self.doctorate_admission.comment, 'My justification')
        self.assertEqual(
            self.doctorate_admission.specific_question_answers,
            {
                self.specific_questions_uuids[0]: 'My answer 1 updated',
                self.specific_questions_uuids[1]: 'My answer 2',
            },
        )
        self.assertEqual(self.doctorate_admission.proximity_commission, '')
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)

        # Admission
        response = self.client.post(
            self.doctorate_url,
            {
                **default_data,
                'admission_type': ChoixTypeAdmission.ADMISSION.name,
            },
        )

        self.assertRedirects(response=response, expected_url=self.doctorate_details_url, fetch_redirect_response=False)

        self.doctorate_admission.refresh_from_db()

        self.assertEqual(self.doctorate_admission.type, ChoixTypeAdmission.ADMISSION.name)
        self.assertEqual(self.doctorate_admission.comment, '')

        # CDE proximity commission
        self.doctorate_admission.training.management_entity = self.cde_commission
        self.doctorate_admission.training.save(update_fields=['management_entity'])

        response = self.client.post(self.doctorate_url, default_data)

        self.assertRedirects(response=response, expected_url=self.doctorate_details_url, fetch_redirect_response=False)

        self.doctorate_admission.refresh_from_db()

        self.assertEqual(
            self.doctorate_admission.proximity_commission,
            ChoixCommissionProximiteCDEouCLSM.MANAGEMENT.name,
        )

        # CDSS proximity commission
        self.doctorate_admission.training.management_entity = self.cdss_commission
        self.doctorate_admission.training.save(update_fields=['management_entity'])

        response = self.client.post(self.doctorate_url, default_data)

        self.assertRedirects(response=response, expected_url=self.doctorate_details_url, fetch_redirect_response=False)

        self.doctorate_admission.refresh_from_db()

        self.assertEqual(
            self.doctorate_admission.proximity_commission,
            ChoixCommissionProximiteCDSS.BCM.name,
        )

        # Science proximity commission
        self.doctorate_admission.training.management_entity = self.science_commission
        self.doctorate_admission.training.acronym = SIGLE_SCIENCES
        self.doctorate_admission.training.save(update_fields=['management_entity', 'acronym'])

        response = self.client.post(self.doctorate_url, default_data)

        self.assertRedirects(response=response, expected_url=self.doctorate_details_url, fetch_redirect_response=False)

        self.doctorate_admission.refresh_from_db()

        self.assertEqual(
            self.doctorate_admission.proximity_commission,
            ChoixSousDomaineSciences.MATHEMATICS.name,
        )

    def test_form_submit_with_invalid_data(self):
        self.client.force_login(self.sic_manager_user)

        default_data = {
            'admission_type': ChoixTypeAdmission.ADMISSION.name,
            'justification': 'My justification',
            'proximity_commission_cde': ChoixCommissionProximiteCDEouCLSM.MANAGEMENT.name,
            'proximity_commission_cdss': ChoixCommissionProximiteCDSS.BCM.name,
            'science_sub_domain': ChoixSousDomaineSciences.MATHEMATICS.name,
            'specific_question_answers_0': 'My answer 1 updated',
            'specific_question_answers_2': 'My answer 2 updated',
        }

        # Without any data
        response = self.client.post(self.doctorate_url, {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('admission_type', []))

        # Without the justification about the pre-admission
        response = self.client.post(
            self.doctorate_url,
            {
                'admission_type': ChoixTypeAdmission.PRE_ADMISSION.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('justification', []))

        # Without the proximity commission

        # CDE proximity commission
        self.doctorate_admission.training.management_entity = self.cde_commission
        self.doctorate_admission.training.save(update_fields=['management_entity'])

        response = self.client.post(self.doctorate_url, {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('proximity_commission_cde', []))

        # CDSS proximity commission
        self.doctorate_admission.training.management_entity = self.cdss_commission
        self.doctorate_admission.training.save(update_fields=['management_entity'])

        response = self.client.post(self.doctorate_url, {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('proximity_commission_cdss', []))

        # Science proximity commission
        self.doctorate_admission.training.management_entity = self.science_commission
        self.doctorate_admission.training.acronym = SIGLE_SCIENCES
        self.doctorate_admission.training.save(update_fields=['management_entity', 'acronym'])

        response = self.client.post(self.doctorate_url, {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('science_sub_domain', []))
