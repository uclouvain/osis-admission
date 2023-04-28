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
import datetime
from typing import List, Union

import freezegun
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import reverse

from admission.contrib.models import ContinuingEducationAdmission, DoctorateAdmission, GeneralEducationAdmission
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO, VisualiseurAdmissionDTO
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests import QueriesAssertionsMixin
from admission.tests.factories.admission_viewer import AdmissionViewerFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import (
    CentralManagerRoleFactory,
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from base.models.enums.entity_type import EntityType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory, MainEntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.user import UserFactory
from education_group.auth.scope import Scope
from program_management.models.education_group_version import EducationGroupVersion
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2023-01-01')
class AdmissionListTestCase(QueriesAssertionsMixin, TestCase):
    admissions = []
    NB_MAX_QUERIES = 24

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        root_entity = MainEntityVersionFactory(acronym="UCL", parent=None, entity_type="").entity

        # Users
        cls.user = User.objects.create_user(
            username='john_doe',
            password='top_secret',
        )

        cls.sic_management_user = SicManagementRoleFactory(entity=root_entity).person.user
        cls.other_sic_management = SicManagementRoleFactory().person

        # Academic years
        AcademicYearFactory.produce(base_year=2023, number_past=2, number_future=2)

        # Entities
        faculty_entity = EntityVersionFactory(
            acronym='ABCDEF',
            entity_type=EntityType.FACULTY.name,
            parent=root_entity,
        ).entity

        cls.first_entity = EntityVersionFactory(
            acronym='GHIJK',
            entity_type=EntityType.SCHOOL.name,
            parent=faculty_entity,
        ).entity

        # Admissions
        cls.admissions: List[Union[DoctorateAdmission, GeneralEducationAdmission, ContinuingEducationAdmission]] = [
            GeneralEducationAdmissionFactory(
                candidate__country_of_citizenship=CountryFactory(european_union=True, name='Belgique'),
                candidate__first_name="John",
                candidate__last_name="Doe",
                status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
                training__management_entity=cls.first_entity,
                training__acronym="ABCD0",
                last_update_author__user__username='user1',
                submitted_at=datetime.datetime(2023, 1, 1),
            ),
        ]

        cls.admissions[0].last_update_author = cls.admissions[0].candidate
        cls.admissions[0].save()

        admission_viewers = [
            AdmissionViewerFactory(person=cls.sic_management_user.person, admission=cls.admissions[0]),
            AdmissionViewerFactory(person=cls.other_sic_management, admission=cls.admissions[0]),
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
                code_formation=cls.admissions[0].training.partial_acronym,
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
                derniere_modification_par=cls.admissions[0].last_update_author.user.username,
                derniere_modification_par_candidat=True,
                dernieres_vues_par=[
                    VisualiseurAdmissionDTO(
                        nom=admission_viewers[1].person.last_name,
                        prenom=admission_viewers[1].person.first_name,
                        date=admission_viewers[1].viewed_at,
                    ),
                ],
                date_confirmation=cls.admissions[0].submitted_at,
            ),
        ]

        cls.default_params = {
            'annee_academique': 2022,
            'taille_page': 10,
        }

        # Targeted url
        cls.url = reverse('admission:all-list')

    def setUp(self) -> None:
        cache.clear()

    def _do_request(self, allowed_sql_surplus=0, **data):
        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES + allowed_sql_surplus, verbose=True):
            return self.client.get(self.url, data={**self.default_params, **data})

    def test_list_user_without_person(self):
        self.client.force_login(user=UserFactory())

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_list_user_no_role(self):
        self.client.force_login(user=PersonFactory().user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_list_initialization(self):
        self.client.force_login(user=self.sic_management_user)

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES):
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

    def test_list_central_manager_scoped_not_entity(self):
        manager = CentralManagerRoleFactory(scopes=[Scope.ALL.name])
        self.client.force_login(user=manager.person.user)

        response = self._do_request(allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_central_manager_scoped_on_entity(self):
        manager = CentralManagerRoleFactory(scopes=[Scope.ALL.name], entity=self.first_entity)
        self.client.force_login(user=manager.person.user)

        response = self._do_request(allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_list_central_manager_another_scope(self):
        manager = CentralManagerRoleFactory(scopes=[Scope.IUFC.name])
        self.client.force_login(user=manager.person.user)

        response = self._do_request()
        self.assertEqual(response.status_code, 403)

    def test_list_another_scope(self):
        self.client.force_login(user=SicManagementRoleFactory().person.user)

        response = self._do_request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_education_group_scopes(self):
        self.client.force_login(user=ProgramManagerRoleFactory().person.user)

        response = self._do_request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        program_manager = ProgramManagerRoleFactory(education_group=self.admissions[0].training.education_group)
        ProgramManagerRoleFactory.create_batch(10, person=program_manager.person)
        self.client.force_login(user=program_manager.person.user)

        response = self._do_request()
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(self.results[0].uuid, response.context['object_list'][0].uuid)

    def test_list_with_filter_by_academic_year(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(annee_academique=2022)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        response = self._do_request(annee_academique=2023)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_with_filter_by_numero(self):
        self.client.force_login(user=self.sic_management_user)

        # Lite reference (e.g. 000.111)
        response = self._do_request(numero=self.lite_reference)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # Complete reference (e.g. L-ACRO23-000.111)
        response = self._do_request(numero=self.results[0].numero_demande)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_noma(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(noma=self.student.registration_id)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_candidate_id(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(matricule_candidat=self.admissions[0].candidate.global_id, allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_type(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(type=self.admissions[0].type_demande)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_enrollment_campus(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(
            site_inscription=self.admissions[0].training.enrollment_campus.uuid,
            allowed_sql_surplus=1,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_entities(self):
        self.client.force_login(user=self.sic_management_user)

        # With school
        response = self._do_request(entites='ABCDEF', allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # With faculty
        response = self._do_request(entites='GHIJK', allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # Invalid entity
        response = self._do_request(entites='XYZ')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('entites' in response.context['filter_form'].errors)
        self.assertEqual(
            response.context['filter_form'].errors['entites'],
            ["Attention, l'entité suivante n'existe pas à l'UCLouvain : %(entities)s" % {'entities': 'XYZ'}],
        )

        # Invalid entities
        response = self._do_request(entites='XYZ1,XYZ2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('entites' in response.context['filter_form'].errors)
        self.assertEqual(
            response.context['filter_form'].errors['entites'],
            [
                "Attention, les entités suivantes n'existent pas à l'UCLouvain : %(entities)s"
                % {'entities': 'XYZ1, XYZ2'}
            ],
        )

    def test_list_with_filter_by_admission_statuses(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(etats=[self.admissions[0].status])
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_training_type(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(types_formation=self.admissions[0].training.education_group_type.name)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_training(self):
        self.client.force_login(user=self.sic_management_user)

        # Acronym
        response = self._do_request(formation=self.admissions[0].training.acronym)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # Title
        response = self._do_request(formation=self.admissions[0].training.title)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # Acronym but bad title
        response = self._do_request(formation=f'{self.admissions[0].training.acronym} Invalid-training')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_with_international_scholarship(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(bourse_internationale=self.admissions[0].international_scholarship.uuid)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_erasmus_mundus_scholarship(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(bourse_erasmus_mundus=self.admissions[0].erasmus_mundus_scholarship.uuid)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_double_degree_scholarship(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(bourse_double_diplomation=self.admissions[0].double_degree_scholarship.uuid)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_asc_sort_by_reference(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            training=self.admissions[0].training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        response = self._do_request(o='numero_demande')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[0].uuid)
        self.assertEqual(result[1].uuid, second_admission.uuid)

    def test_list_desc_sort_by_reference(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = (
            GeneralEducationAdmissionFactory(
                training__management_entity=self.first_entity,
                training=self.admissions[0].training,
                status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            ),
        )

        response = self._do_request(o='-numero_demande')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, second_admission[0].uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_candidate_name(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            candidate__first_name="Joe",
            candidate__last_name="Doe",
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        response = self._do_request(o='nom_candidat')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, second_admission.uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_training(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            training__acronym="AACD0",
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        response = self._do_request(o='formation')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, second_admission.uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_candidate_nationality(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            candidate__country_of_citizenship=CountryFactory(european_union=False, name='Andorre'),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        response = self._do_request(o='nationalite_candidat')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, second_admission.uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_vip(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            erasmus_mundus_scholarship=None,
            double_degree_scholarship=None,
            international_scholarship=None,
        )

        response = self._do_request(o='vip')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, second_admission.uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_admission_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
        )

        response = self._do_request(o='-type_demande')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, second_admission.uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    @freezegun.freeze_time('2022-12-31')
    def test_list_sort_by_modified_date(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        response = self._do_request(o='derniere_modification_le')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, second_admission.uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_modified_author(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            last_update_author__user__username='user0',
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        response = self._do_request(o='derniere_modification_par')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, second_admission.uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_confirmation_date(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            submitted_at=datetime.datetime(2022, 12, 31),
        )

        response = self._do_request(o='date_confirmation')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, second_admission.uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)
