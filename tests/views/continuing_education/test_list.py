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
from typing import List

import freezegun
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from admission.contrib.models import ContinuingEducationAdmission
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue, ChoixEdition
from admission.ddd.admission.formation_continue.dtos.liste import DemandeRechercheDTO
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.roles import (
    CentralManagerRoleFactory,
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from base.models.academic_year import AcademicYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.tests import QueriesAssertionsMixin
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory, MainEntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.user import UserFactory
from education_group.auth.scope import Scope


@freezegun.freeze_time('2023-01-01')
@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class AdmissionListTestCase(QueriesAssertionsMixin, TestCase):
    admissions = []
    NB_MAX_QUERIES = 50  # TODO fix to be more granular

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
        academic_years = AcademicYearFactory.produce(base_year=2023, number_past=2, number_future=2)

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
            end_date=datetime.date(2024, 1, 1),
        ).entity

        cls.second_faculty = EntityVersionFactory(
            acronym='AAAAA',
            entity_type=EntityType.FACULTY.name,
            parent=root_entity,
            end_date=datetime.date(2024, 1, 1),
        ).entity

        # Admissions
        cls.admissions: List[ContinuingEducationAdmission] = [
            ContinuingEducationAdmissionFactory(
                candidate__first_name="John",
                candidate__last_name="Doe",
                candidate__email='john.doe@example.be',
                status=ChoixStatutPropositionContinue.CONFIRMEE.name,
                training__management_entity=cls.first_entity,
                training__acronym="ZEBU0",
                training__education_group_type__name=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
                submitted_at=datetime.datetime(2023, 1, 2),
                training__academic_year=academic_years[1],
                determined_academic_year=academic_years[2],
                edition=ChoixEdition.DEUX.name,
                in_payement_order=True,
                modified_at=datetime.datetime(2023, 1, 2),
                last_update_author=PersonFactory(first_name='Robin'),
            ),
            ContinuingEducationAdmissionFactory(
                candidate__first_name="Jim",
                candidate__last_name="Arnold",
                candidate__email='jim.arnold@example.be',
                status=ChoixStatutPropositionContinue.EN_BROUILLON.name,
                training__management_entity=cls.first_entity,
                training__acronym="ABCD0",
                training__education_group_type__name=TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name,
                submitted_at=datetime.datetime(2023, 1, 1),
                training__academic_year=academic_years[1],
                determined_academic_year=academic_years[2],
                edition=ChoixEdition.UN.name,
                in_payement_order=False,
                modified_at=datetime.datetime(2023, 1, 1),
                last_update_author=PersonFactory(first_name='John'),
                interested_mark=True,
            ),
            ContinuingEducationAdmissionFactory(
                candidate__first_name="Jane",
                candidate__last_name="Foe",
                status=ChoixStatutPropositionContinue.CONFIRMEE.name,
                training__management_entity=cls.first_entity,
                training__acronym="ZEBU0",
                submitted_at=datetime.datetime(2024, 1, 1),
                training__academic_year=academic_years[3],
                determined_academic_year=academic_years[3],
            ),
            ContinuingEducationAdmissionFactory(
                candidate__first_name="Jack",
                candidate__last_name="Poe",
                status=ChoixStatutPropositionContinue.CONFIRMEE.name,
                training__acronym="DEFG0",
                submitted_at=datetime.datetime(2023, 5, 1),
                training__academic_year=academic_years[2],
                determined_academic_year=academic_years[2],
            ),
        ]
        cls.admissions[1].training.specificiufcinformations.registration_required = False
        cls.admissions[1].training.specificiufcinformations.save(update_fields=['registration_required'])

        cls.students = [
            StudentFactory(person=admission.candidate, registration_id=f'0123456{index}')
            for index, admission in enumerate(cls.admissions)
        ]

        cls.academic_calendar_2023 = AcademicCalendarFactory(
            reference=AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name,
            start_date=datetime.date(2022, 7, 15),
            end_date=datetime.date(2023, 7, 14),
            data_year=AcademicYear.objects.get(year=2023),
        )
        cls.academic_calendar_2024 = AcademicCalendarFactory(
            reference=AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name,
            start_date=datetime.date(2023, 7, 15),
            end_date=datetime.date(2024, 7, 14),
            data_year=AcademicYear.objects.get(year=2024),
        )

        cls.default_params = {
            'annee_academique': 2023,
            'taille_page': 10,
        }

        # Targeted url
        cls.url = reverse('admission:continuing-education:list')

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

    def test_list_sic_manager_on_entity(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request()
        self.assertEqual(response.status_code, 200)

        object_list: List[DemandeRechercheDTO] = response.context['object_list']
        self.assertEqual(len(object_list), 2)
        self.assertEqual(object_list[0].uuid, self.admissions[0].uuid)
        self.assertEqual(object_list[1].uuid, self.admissions[1].uuid)

    def test_list_sic_manager_another_entity(self):
        self.client.force_login(user=SicManagementRoleFactory().person.user)

        response = self._do_request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_central_manager_scoped_iufc_not_entity(self):
        manager = CentralManagerRoleFactory(scopes=[Scope.IUFC.name])
        self.client.force_login(user=manager.person.user)

        response = self._do_request(allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_central_manager_scoped_all_not_entity(self):
        manager = CentralManagerRoleFactory(scopes=[Scope.ALL.name])
        self.client.force_login(user=manager.person.user)

        response = self._do_request(allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 403)

    def test_list_central_manager_scoped_doctorate_not_entity(self):
        manager = CentralManagerRoleFactory(scopes=[Scope.DOCTORAT.name])
        self.client.force_login(user=manager.person.user)

        response = self._do_request(allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 403)

    def test_list_central_manager_scoped_all_on_entity(self):
        manager = CentralManagerRoleFactory(scopes=[Scope.ALL.name], entity=self.first_entity)
        self.client.force_login(user=manager.person.user)

        response = self._do_request(allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 403)

    def test_list_central_manager_scoped_iufc_on_entity(self):
        manager = CentralManagerRoleFactory(scopes=[Scope.IUFC.name], entity=self.first_entity)
        self.client.force_login(user=manager.person.user)

        response = self._do_request(allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 200)

        object_list: List[DemandeRechercheDTO] = response.context['object_list']
        self.assertEqual(len(object_list), 2)
        self.assertEqual(object_list[0].uuid, self.admissions[0].uuid)
        self.assertEqual(object_list[1].uuid, self.admissions[1].uuid)

    def test_list_education_group_scopes(self):
        self.client.force_login(user=ProgramManagerRoleFactory().person.user)

        response = self._do_request()
        self.assertEqual(response.status_code, 403)

        program_manager = ProgramManagerRoleFactory(education_group=self.admissions[0].training.education_group)
        self.client.force_login(user=program_manager.person.user)

        response = self._do_request()
        self.assertEqual(response.status_code, 200)

        object_list: List[DemandeRechercheDTO] = response.context['object_list']
        self.assertEqual(len(object_list), 1)
        self.assertEqual(object_list[0].uuid, self.admissions[0].uuid)

    def test_list_initialization(self):
        self.client.force_login(user=self.sic_management_user)

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'], [])

        form = response.context['filter_form']
        self.assertEqual(form['annee_academique'].initial, 2023)
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

        self.assertEqual(form['etats'].initial, ChoixStatutPropositionContinue.get_names())

    @freezegun.freeze_time('2023-07-14')
    def test_list_initialization_just_before_academic_year_change(self):
        self.client.force_login(user=self.sic_management_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        form = response.context['filter_form']
        self.assertEqual(form['annee_academique'].initial, 2023)

    @freezegun.freeze_time('2023-07-15')
    def test_list_initialization_just_after_academic_year_change(self):
        self.client.force_login(user=self.sic_management_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        form = response.context['filter_form']
        self.assertEqual(form['annee_academique'].initial, 2024)

    def test_built_dto(self):
        self.client.force_login(user=self.sic_management_user)

        current_admission: ContinuingEducationAdmission = (
            ContinuingEducationAdmission.objects.with_training_management_and_reference()
            .select_related(
                'candidate',
                'training__specificiufcinformations',
                'last_update_author',
            )
            .get(uuid=self.admissions[0].uuid)
        )

        response = self._do_request(numero=current_admission.reference_str)

        self.assertEqual(response.status_code, 200)

        object_list: List[DemandeRechercheDTO] = response.context['object_list']

        self.assertEqual(len(object_list), 1)

        self.assertEqual(object_list[0].uuid, current_admission.uuid)
        self.assertEqual(object_list[0].numero_demande, current_admission.formatted_reference)
        self.assertEqual(object_list[0].nom_candidat, current_admission.candidate.last_name)
        self.assertEqual(object_list[0].prenom_candidat, current_admission.candidate.first_name)
        self.assertEqual(object_list[0].noma_candidat, self.students[0].registration_id)
        self.assertEqual(object_list[0].courriel_candidat, current_admission.candidate.email)
        self.assertEqual(object_list[0].sigle_formation, current_admission.training.acronym)
        self.assertEqual(object_list[0].code_formation, current_admission.training.partial_acronym)
        self.assertEqual(object_list[0].intitule_formation, current_admission.training.title)
        self.assertEqual(
            object_list[0].inscription_au_role_obligatoire,
            current_admission.training.specificiufcinformations.registration_required,
        )
        self.assertEqual(object_list[0].edition, current_admission.edition)
        self.assertEqual(object_list[0].sigle_faculte, current_admission.training_management_faculty)
        self.assertEqual(object_list[0].paye, current_admission.in_payement_order)
        self.assertEqual(object_list[0].etat_demande, current_admission.status)
        self.assertEqual(object_list[0].etat_epc, '')
        self.assertEqual(object_list[0].date_confirmation, current_admission.submitted_at)
        self.assertEqual(object_list[0].derniere_modification_le, current_admission.modified_at)
        self.assertEqual(
            object_list[0].derniere_modification_par,
            f'{current_admission.last_update_author.first_name} {current_admission.last_update_author.last_name}',
        )

        admission_without_facultative_foreign_data = ContinuingEducationAdmissionFactory(
            determined_academic_year=self.admissions[0].determined_academic_year,
            candidate=self.admissions[0].candidate,
            training__management_entity=self.admissions[0].training.management_entity,
        )
        admission_without_facultative_foreign_data.training.specificiufcinformations.delete()

        response = self._do_request(numero=admission_without_facultative_foreign_data.reference_str)

        self.assertEqual(response.status_code, 200)

        object_list: List[DemandeRechercheDTO] = response.context['object_list']

        self.assertEqual(len(object_list), 1)

        self.assertEqual(object_list[0].uuid, admission_without_facultative_foreign_data.uuid)
        self.assertEqual(object_list[0].derniere_modification_par, '')
        self.assertEqual(object_list[0].inscription_au_role_obligatoire, None)

    def test_list_with_filter_by_academic_year(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(annee_academique=self.admissions[2].training.academic_year.year)
        self.assertEqual(response.status_code, 200)

        object_list: List[DemandeRechercheDTO] = response.context['object_list']
        self.assertEqual(len(object_list), 1)
        self.assertEqual(object_list[0].uuid, self.admissions[2].uuid)

    def test_list_with_filter_by_numero(self):
        self.client.force_login(user=self.sic_management_user)

        # Lite reference (e.g. 0000.1111)
        response = self._do_request(numero=self.admissions[0].reference_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].uuid, self.admissions[0].uuid)

        # Complete reference (e.g. L-ACRO23-0000.1111)
        admission = ContinuingEducationAdmission.objects.with_training_management_and_reference().get(
            uuid=self.admissions[0].uuid
        )
        response = self._do_request(numero=admission.formatted_reference)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].uuid, self.admissions[0].uuid)

    def test_list_with_filter_by_candidate_id(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(matricule_candidat=self.admissions[0].candidate.global_id, allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].uuid, self.admissions[0].uuid)

    def test_list_with_filter_by_entities(self):
        self.client.force_login(user=self.sic_management_user)

        # With faculty
        response = self._do_request(entites='ABCDEF', allowed_sql_surplus=3)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)

        # With school
        response = self._do_request(entites='GHIJK', allowed_sql_surplus=3)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)

        # Invalid entity
        response = self._do_request(entites='XYZ')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('entites' in response.context['filter_form'].errors)
        self.assertEqual(
            response.context['filter_form'].errors['entites'],
            ["Attention, l'entité suivante n'existe pas à l'UCLouvain : %(entities)s" % {'entities': 'XYZ'}],
        )

        # Invalid entities
        response = self._do_request(entites='XYZ1,XYZ2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('entites' in response.context['filter_form'].errors)
        self.assertEqual(
            response.context['filter_form'].errors['entites'],
            [
                "Attention, les entités suivantes n'existent pas à l'UCLouvain : %(entities)s"
                % {'entities': 'XYZ1, XYZ2'}
            ],
        )

    def test_list_with_filter_by_admission_statuses(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(etats=[ChoixStatutPropositionContinue.EN_BROUILLON.name])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].uuid, self.admissions[1].uuid)

    def test_list_with_filter_by_training_type(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(types_formation=[TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].uuid, self.admissions[1].uuid)

    def test_list_with_filter_by_training(self):
        self.client.force_login(user=self.sic_management_user)

        # Acronym
        response = self._do_request(allowed_sql_surplus=3, sigles_formations=[self.admissions[0].training.acronym])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].uuid, self.admissions[0].uuid)

        # Bad acronym
        response = self._do_request(sigles_formations=['UNKNOWN'])
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue('sigles_formations' in form.errors)

    def test_list_with_filter_by_edition(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(edition=[ChoixEdition.UN.name])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].uuid, self.admissions[1].uuid)

    def test_list_with_filter_by_required_enrolment(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(inscription_requise=False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].uuid, self.admissions[1].uuid)

    def test_list_with_filter_by_payement_order(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(paye=False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].uuid, self.admissions[1].uuid)

    def test_list_with_filter_by_interested_mark(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(marque_d_interet='on')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].uuid, self.admissions[1].uuid)

    def test_list_sort_by_reference(self):
        self.client.force_login(user=self.sic_management_user)

        # Ascending order
        response = self._do_request(o='numero_demande')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[0].uuid)
        self.assertEqual(result[1].uuid, self.admissions[1].uuid)

        # Descending order
        response = self._do_request(o='-numero_demande')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[1].uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_candidate_name(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(o='nom_candidat')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[1].uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_candidate_email_address(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(o='courriel_candidat')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[1].uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_training(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(o='formation')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[1].uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_edition(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(o='edition')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[1].uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_faculty(self):
        self.client.force_login(user=self.sic_management_user)

        new_admission = ContinuingEducationAdmissionFactory(
            candidate__first_name="Jack",
            candidate__last_name="Poe",
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            training__acronym="DEFG0",
            training__management_entity=self.second_faculty,
            submitted_at=datetime.datetime(2023, 5, 1),
            determined_academic_year=self.admissions[0].determined_academic_year,
        )

        response = self._do_request(o='faculte')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].uuid, new_admission.uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)
        self.assertEqual(result[2].uuid, self.admissions[1].uuid)

    def test_list_sort_by_in_payement_order(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(o='paye')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[1].uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_status(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(o='etat_demande')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[1].uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_confirmation_date(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(o='date_confirmation')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[1].uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_last_modification_date(self):
        self.client.force_login(user=self.sic_management_user)

        with freezegun.freeze_time('2023-05-01'):
            self.admissions[0].save()

        with freezegun.freeze_time('2023-02-01'):
            self.admissions[1].save()

        response = self._do_request(o='derniere_modification_le')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[1].uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)

    def test_list_sort_by_last_modification_author(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(o='derniere_modification_par')
        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].uuid, self.admissions[1].uuid)
        self.assertEqual(result[1].uuid, self.admissions[0].uuid)
