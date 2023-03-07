# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Union

import freezegun
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import reverse

from admission.contrib.models import DoctorateAdmission, GeneralEducationAdmission, ContinuingEducationAdmission
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests import QueriesAssertionsMixin
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagerRoleFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.student import StudentFactory
from program_management.models.education_group_version import EducationGroupVersion
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2023-01-01')
class AdmissionListTestCase(QueriesAssertionsMixin, TestCase):
    admissions = []
    NB_MAX_QUERIES = 22

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        # Users
        cls.user = User.objects.create_user(
            username='john_doe',
            password='top_secret',
        )

        cls.sic_manager_user = SicManagerRoleFactory().person.user

        # Academic years
        AcademicYearFactory.produce(base_year=2023, number_past=2, number_future=2)

        # Entities
        faculty_entity = EntityFactory()
        EntityVersionFactory(
            entity=faculty_entity,
            acronym='ABCDEF',
            entity_type=EntityType.FACULTY.name,
        )

        cls.first_entity = EntityFactory()
        EntityVersionFactory(
            entity=cls.first_entity,
            acronym='GHIJK',
            entity_type=EntityType.SCHOOL.name,
            parent=faculty_entity,
        )

        # Admissions
        cls.admissions: List[Union[DoctorateAdmission, GeneralEducationAdmission, ContinuingEducationAdmission]] = [
            GeneralEducationAdmissionFactory(
                candidate__country_of_citizenship=CountryFactory(european_union=True, name='Belgique'),
                status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
                training__management_entity=cls.first_entity,
            ),
        ]
        cls.lite_reference = '{:07,}'.format(cls.admissions[0].reference).replace(',', '.')

        cls.student = StudentFactory(
            person=cls.admissions[0].candidate,
            registration_id='01234567',
        )

        teaching_campus = (
            EducationGroupVersion.objects.filter(offer=cls.admissions[0].training)
            .first()
            .root_group.main_teaching_campus.name
        )

        cls.results = [
            DemandeRechercheDTO(
                uuid=cls.admissions[0].uuid,
                numero_demande=f'M-ABCDEF22-{cls.lite_reference}',
                nom_candidat=cls.admissions[0].candidate.last_name,
                prenom_candidat=cls.admissions[0].candidate.first_name,
                noma_candidat=cls.admissions[0].candidate.last_registration_id,
                plusieurs_demandes=False,
                sigle_formation=cls.admissions[0].training.acronym,
                sigle_partiel_formation=cls.admissions[0].training.partial_acronym,
                intitule_formation=cls.admissions[0].training.title,
                type_formation=cls.admissions[0].training.education_group_type.name,
                lieu_formation=teaching_campus,
                nationalite_candidat=cls.admissions[0].candidate.country_of_citizenship.name,
                nationalite_ue_candidat=cls.admissions[0].candidate.country_of_citizenship.european_union,
                vip=any(
                    scholarship
                    for scholarship in [
                        cls.admissions[0].erasmus_mundus_scholarship,
                        cls.admissions[0].international_scholarship,
                        cls.admissions[0].double_degree_scholarship,
                    ]
                ),
                etat_demande=cls.admissions[0].status,
                type_demande=cls.admissions[0].type_demande,
                derniere_modification_le=cls.admissions[0].modified_at,
                derniere_modification_par='',
                derniere_modification_par_candidat=False,
                derniere_vue_par='',
                date_confirmation=cls.admissions[0].submitted_at,
            ),
        ]

        cls.default_params = {
            'annee_academique': 2022,
            'page_size': 10,
        }

        # Targeted url
        cls.url = reverse('admission:all-list')

    def setUp(self) -> None:
        cache.clear()

    def test_list_user_without_person(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_list_candidate_user(self):
        self.client.force_login(user=self.admissions[0].candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_list_initialization(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'], [])

        form = response.context['filter_form']
        self.assertEqual(form['annee_academique'].initial, 2022)
        self.assertEqual(
            form['annee_academique'].field.choices,
            [
                (2025, '2025-26'),
                (2024, '2024-25'),
                (2023, '2023-24'),
                (2022, '2022-23'),
                (2021, '2021-22'),
            ],
        )

    def test_list_with_filter_by_academic_year(self):
        self.client.force_login(user=self.sic_manager_user)

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES):
            response = self.client.get(
                self.url,
                data={
                    **self.default_params,
                    'annee_academique': 2022,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        response = self.client.get(
            self.url,
            data={
                **self.default_params,
                'annee_academique': 2023,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_with_filter_by_numero(self):
        self.client.force_login(user=self.sic_manager_user)

        # Lite reference (e.g. 000.111)
        response = self.client.get(
            self.url,
            data={
                'numero': self.lite_reference,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # Complete reference (e.g. L-ACRO23-000.111)
        response = self.client.get(
            self.url,
            data={
                'numero': self.results[0].numero_demande,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_noma(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(
            self.url,
            data={
                'noma': self.student.registration_id,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_candidate_id(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(
            self.url,
            data={
                'matricule_candidat': self.admissions[0].candidate.global_id,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_type(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(
            self.url,
            data={
                'type': self.admissions[0].type_demande,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_enrollment_campus(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(
            self.url,
            data={
                'site_inscription': self.admissions[0].training.enrollment_campus.uuid,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_entities(self):
        self.client.force_login(user=self.sic_manager_user)

        # With school
        response = self.client.get(
            self.url,
            data={
                'entites': 'ABCDEF',
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # With faculty
        response = self.client.get(
            self.url,
            data={
                'entites': 'GHIJK',
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # Invalid entity
        response = self.client.get(
            self.url,
            data={
                'entites': 'XYZ',
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue('entites' in response.context['filter_form'].errors)
        self.assertEqual(
            response.context['filter_form'].errors['entites'],
            ["Attention, l'entité suivante n'existe pas à l'UCLouvain : %(entities)s" % {'entities': 'XYZ'}],
        )

        # Invalid entities
        response = self.client.get(
            self.url,
            data={
                'entites': 'XYZ1,XYZ2',
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue('entites' in response.context['filter_form'].errors)
        self.assertEqual(
            response.context['filter_form'].errors['entites'],
            [
                "Attention, les entités suivantes n'existent pas à l'UCLouvain : %(entities)s"
                % {'entities': 'XYZ1, XYZ2'}
            ],
        )

    def test_list_with_filter_by_training_type(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(
            self.url,
            data={
                'types_formation_0': self.admissions[0].training.education_group_type.name,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_training(self):
        self.client.force_login(user=self.sic_manager_user)

        # Acronym
        response = self.client.get(
            self.url,
            data={
                'formation': self.admissions[0].training.acronym,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # Title
        response = self.client.get(
            self.url,
            data={
                'formation': self.admissions[0].training.title,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # Acronym but bad title
        response = self.client.get(
            self.url,
            data={
                'formation': f'{self.admissions[0].training.acronym} Invalid-training',
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_with_international_scholarship(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(
            self.url,
            data={
                'bourse_internationale': self.admissions[0].international_scholarship.uuid,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_erasmus_mundus_scholarship(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(
            self.url,
            data={
                'bourse_erasmus_mundus': self.admissions[0].erasmus_mundus_scholarship.uuid,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_double_degree_scholarship(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(
            self.url,
            data={
                'bourse_double_diplomation': self.admissions[0].double_degree_scholarship.uuid,
                **self.default_params,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])
