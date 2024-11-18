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
from rest_framework import status

from admission.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import (
    ENTITY_CDE,
)
from admission.ddd.admission.domain.enums import TypeFormation
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.forms import EMPTY_CHOICE_AS_LIST
from admission.tests.factories.form_item import AdmissionFormItemInstantiationFactory, TextAdmissionFormItemFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import (
    SicManagementRoleFactory,
    CandidateFactory,
    ProgramManagerRoleFactory,
)
from admission.tests.factories.scholarship import (
    DoubleDegreeScholarshipFactory,
    InternationalScholarshipFactory,
    ErasmusMundusScholarshipFactory,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.forms.utils.choice_field import BLANK_CHOICE_DISPLAY
from base.models.campus import Campus
from base.models.enums.organization_type import MAIN
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group_year import Master120TrainingFactory, EducationGroupYearBachelorFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2021-12-01')
class GeneralTrainingChoiceFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')

        cls.first_campus = CampusFactory(name='Mons', organization__type=MAIN)
        cls.all_campuses = Campus.objects.filter(organization__type=MAIN)

        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.scholarships = [
            DoubleDegreeScholarshipFactory(short_name='dd1', long_name='Double Degree 1'),
            DoubleDegreeScholarshipFactory(short_name='cd1', long_name=''),
            InternationalScholarshipFactory(short_name='is1', long_name='International 1'),
            InternationalScholarshipFactory(short_name='is2', long_name='International 2'),
            ErasmusMundusScholarshipFactory(short_name='em1', long_name='Erasmus Mundus 1'),
            ErasmusMundusScholarshipFactory(short_name='em2', long_name='Erasmus Mundus 2'),
            ErasmusMundusScholarshipFactory(short_name='em3', long_name='Erasmus Mundus 3', disabled=True),
        ]

        cls.master_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=Master120TrainingFactory(
                management_entity=first_doctoral_commission,
                academic_year=academic_years[0],
            ),
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__id_photo=[],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            double_degree_scholarship=cls.scholarships[0],
            international_scholarship=cls.scholarships[3],
            erasmus_mundus_scholarship=cls.scholarships[4],
        )

        EducationGroupVersionFactory(
            root_group__main_teaching_campus=cls.first_campus,
            offer=cls.master_admission.training,
            version_name='',
        )

        cls.bachelor_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=EducationGroupYearBachelorFactory(
                management_entity=first_doctoral_commission,
                academic_year=academic_years[0],
            ),
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__id_photo=[],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            double_degree_scholarship=None,
            international_scholarship=None,
            erasmus_mundus_scholarship=None,
            determined_academic_year=cls.master_admission.determined_academic_year,
        )

        EducationGroupVersionFactory(
            root_group__main_teaching_campus=cls.first_campus,
            offer=cls.bachelor_admission.training,
            version_name='',
        )

        cls.specific_questions = [
            AdmissionFormItemInstantiationFactory(
                form_item=TextAdmissionFormItemFactory(),
                tab=Onglets.CHOIX_FORMATION.name,
                academic_year=cls.master_admission.determined_academic_year,
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=TextAdmissionFormItemFactory(),
                tab=Onglets.CURRICULUM.name,
                academic_year=cls.master_admission.determined_academic_year,
            ),
        ]

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.master_admission.training.education_group
        ).person.user

        cls.master_url = resolve_url(
            'admission:general-education:update:training-choice',
            uuid=cls.master_admission.uuid,
        )
        cls.master_detail_url = resolve_url(
            'admission:general-education:training-choice',
            uuid=cls.master_admission.uuid,
        )
        cls.bachelor_url = resolve_url(
            'admission:general-education:update:training-choice',
            uuid=cls.bachelor_admission.uuid,
        )
        cls.bachelor_detail_url = resolve_url(
            'admission:general-education:training-choice',
            uuid=cls.bachelor_admission.uuid,
        )

    def test_general_training_choice_access(self):
        # If the user is not authenticated, they should be redirected to the login page
        response = self.client.get(self.master_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + self.master_url)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(self.master_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.master_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, they should be able to access the page
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.master_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_training_choice_for_master_form_initialization(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.master_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['admission'].uuid, self.master_admission.uuid)

        form = response.context['form']

        # Check form fields
        self.assertEqual(form.initial['training_type'], TypeFormation.MASTER.name)
        self.assertCountEqual(form.fields['training_type'].choices, TypeFormation.choices())
        self.assertEqual(form.fields['training_type'].disabled, True)
        self.assertEqual(form.fields['training_type'].required, False)

        self.assertEqual(form.initial['campus'], self.first_campus.uuid)
        self.assertCountEqual(
            form.fields['campus'].choices,
            [
                ('', BLANK_CHOICE_DISPLAY),
                *[(campus.uuid, campus.name) for campus in self.all_campuses],
            ],
        )
        self.assertEqual(form.fields['campus'].disabled, True)
        self.assertEqual(form.fields['campus'].required, False)

        self.assertEqual(form.initial['general_education_training'], self.master_admission.training.acronym)
        self.assertEqual(
            form.fields['general_education_training'].choices,
            [
                [
                    self.master_admission.training.acronym,
                    '{} ({}) <span class="training-acronym">{}</span>'.format(
                        self.master_admission.training.title,
                        self.first_campus.name,
                        self.master_admission.training.acronym,
                    ),
                ]
            ],
        )
        self.assertEqual(form.fields['general_education_training'].disabled, True)
        self.assertEqual(form.fields['general_education_training'].required, False)

        self.assertEqual(form.initial['has_double_degree_scholarship'], True)
        self.assertEqual(form.initial['double_degree_scholarship'], str(self.scholarships[0].uuid))
        self.assertEqual(
            form.fields['double_degree_scholarship'].choices,
            [
                EMPTY_CHOICE_AS_LIST[0],
                [str(self.scholarships[1].uuid), self.scholarships[1].short_name],
                [str(self.scholarships[0].uuid), self.scholarships[0].long_name],
            ],
        )

        self.assertEqual(form.initial['has_international_scholarship'], True)
        self.assertEqual(form.initial['international_scholarship'], str(self.scholarships[3].uuid))
        self.assertEqual(
            form.fields['international_scholarship'].choices,
            [
                EMPTY_CHOICE_AS_LIST[0],
                [str(self.scholarships[2].uuid), self.scholarships[2].long_name],
                [str(self.scholarships[3].uuid), self.scholarships[3].long_name],
            ],
        )

        self.assertEqual(form.initial['has_erasmus_mundus_scholarship'], True)
        self.assertEqual(form.initial['erasmus_mundus_scholarship'], str(self.scholarships[4].uuid))
        self.assertEqual(
            form.fields['erasmus_mundus_scholarship'].choices,
            [
                EMPTY_CHOICE_AS_LIST[0],
                [str(self.scholarships[4].uuid), self.scholarships[4].long_name],
                [str(self.scholarships[5].uuid), self.scholarships[5].long_name],
            ],
        )

    @freezegun.freeze_time('2021-12-01')
    def test_form_submit_for_master_with_valid_data(self):
        self.client.force_login(self.sic_manager_user)

        # The user specifies that he has scholarships and selects them
        response = self.client.post(
            self.master_url,
            {
                'has_double_degree_scholarship': 'True',
                'double_degree_scholarship': self.scholarships[1].uuid,
                'has_international_scholarship': 'True',
                'international_scholarship': self.scholarships[2].uuid,
                'has_erasmus_mundus_scholarship': 'True',
                'erasmus_mundus_scholarship': self.scholarships[5].uuid,
                'specific_question_answers_0': 'Answer',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, self.master_detail_url)

        self.master_admission.refresh_from_db()

        self.assertEqual(self.master_admission.double_degree_scholarship, self.scholarships[1])
        self.assertEqual(self.master_admission.international_scholarship, self.scholarships[2])
        self.assertEqual(self.master_admission.erasmus_mundus_scholarship, self.scholarships[5])
        self.assertEqual(
            self.master_admission.specific_question_answers,
            {
                str(self.specific_questions[0].form_item.uuid): 'Answer',
            },
        )
        self.assertEqual(self.master_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.master_admission.last_update_author, self.sic_manager_user.person)
        self.assertNotIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            self.master_admission.requested_documents,
        )

        # The user specifies that he has no scholarships but selects them
        response = self.client.post(
            self.master_url,
            {
                'has_double_degree_scholarship': 'False',
                'double_degree_scholarship': self.scholarships[1].uuid,
                'has_international_scholarship': 'False',
                'international_scholarship': self.scholarships[2].uuid,
                'has_erasmus_mundus_scholarship': 'False',
                'erasmus_mundus_scholarship': self.scholarships[5].uuid,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, self.master_detail_url)

        self.master_admission.refresh_from_db()

        self.assertEqual(self.master_admission.double_degree_scholarship, None)
        self.assertEqual(self.master_admission.international_scholarship, None)
        self.assertEqual(self.master_admission.erasmus_mundus_scholarship, None)

    def test_form_submit_for_master_with_invalid_data(self):
        self.client.force_login(self.sic_manager_user)

        # The user specifies that he has scholarships but not selects which ones
        response = self.client.post(
            self.master_url,
            {
                'has_double_degree_scholarship': 'True',
                'double_degree_scholarship': '',
                'has_international_scholarship': 'True',
                'has_erasmus_mundus_scholarship': 'True',
                'erasmus_mundus_scholarship': '',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('double_degree_scholarship', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('international_scholarship', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('erasmus_mundus_scholarship', []))

        # The user doesn't specify if he has scholarships
        response = self.client.post(
            self.master_url,
            {
                'has_double_degree_scholarship': '',
                'double_degree_scholarship': '',
                'has_international_scholarship': '',
                'international_scholarship': '',
                'has_erasmus_mundus_scholarship': '',
                'erasmus_mundus_scholarship': '',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('has_double_degree_scholarship', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('has_international_scholarship', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('has_erasmus_mundus_scholarship', []))

    def test_training_choice_for_bachelor_form_initialization(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.bachelor_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['admission'].uuid, self.bachelor_admission.uuid)

        form = response.context['form']

        # Check form fields
        self.assertEqual(form.initial['training_type'], TypeFormation.BACHELIER.name)
        self.assertCountEqual(form.fields['training_type'].choices, TypeFormation.choices())
        self.assertEqual(form.fields['training_type'].disabled, True)
        self.assertEqual(form.fields['training_type'].required, False)

        self.assertEqual(form.initial['campus'], self.first_campus.uuid)
        self.assertCountEqual(
            form.fields['campus'].choices,
            [
                ('', BLANK_CHOICE_DISPLAY),
                *[(campus.uuid, campus.name) for campus in self.all_campuses],
            ],
        )
        self.assertEqual(form.fields['campus'].disabled, True)
        self.assertEqual(form.fields['campus'].required, False)

        self.assertEqual(form.initial['general_education_training'], self.bachelor_admission.training.acronym)
        self.assertEqual(
            form.fields['general_education_training'].choices,
            [
                [
                    self.bachelor_admission.training.acronym,
                    '{} ({}) <span class="training-acronym">{}</span>'.format(
                        self.bachelor_admission.training.title,
                        self.first_campus.name,
                        self.bachelor_admission.training.acronym,
                    ),
                ]
            ],
        )
        self.assertEqual(form.fields['general_education_training'].disabled, True)
        self.assertEqual(form.fields['general_education_training'].required, False)

        self.assertEqual(form.initial['has_double_degree_scholarship'], False)
        self.assertEqual(form.initial['double_degree_scholarship'], None)
        self.assertEqual(form.fields['double_degree_scholarship'].choices, EMPTY_CHOICE_AS_LIST)

        self.assertEqual(form.initial['has_international_scholarship'], False)
        self.assertEqual(form.initial['international_scholarship'], None)
        self.assertEqual(form.fields['international_scholarship'].choices, EMPTY_CHOICE_AS_LIST)

        self.assertEqual(form.initial['has_erasmus_mundus_scholarship'], False)
        self.assertEqual(form.initial['erasmus_mundus_scholarship'], None)
        self.assertEqual(form.fields['erasmus_mundus_scholarship'].choices, EMPTY_CHOICE_AS_LIST)

    def test_form_submit_for_bachelor_with_valid_data(self):
        self.client.force_login(self.sic_manager_user)

        # The user specifies that he has scholarships and selects them
        response = self.client.post(
            self.bachelor_url,
            {
                'has_double_degree_scholarship': 'True',
                'double_degree_scholarship': self.scholarships[1].uuid,
                'has_international_scholarship': 'True',
                'international_scholarship': self.scholarships[2].uuid,
                'has_erasmus_mundus_scholarship': 'True',
                'erasmus_mundus_scholarship': self.scholarships[5].uuid,
                'specific_question_answers_0': 'Answer',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, self.bachelor_detail_url)

        self.bachelor_admission.refresh_from_db()

        self.assertEqual(self.bachelor_admission.double_degree_scholarship, None)
        self.assertEqual(self.bachelor_admission.international_scholarship, None)
        self.assertEqual(self.bachelor_admission.erasmus_mundus_scholarship, None)
        self.assertEqual(
            self.bachelor_admission.specific_question_answers,
            {
                str(self.specific_questions[0].form_item.uuid): 'Answer',
            },
        )

        self.assertEqual(self.bachelor_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.bachelor_admission.last_update_author, self.sic_manager_user.person)
        self.assertNotIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            self.bachelor_admission.requested_documents,
        )
