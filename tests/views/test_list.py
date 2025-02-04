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
import uuid
from typing import List, Union
from unittest.mock import ANY

import freezegun
from django.contrib.auth.models import User
from django.core.cache import cache
from django.shortcuts import resolve_url
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO, VisualiseurAdmissionDTO
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.enums.liste import TardiveModificationReorientationFiltre
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    PoursuiteDeCycle,
    ChoixStatutChecklist,
    DecisionFacultaireEnum,
    BesoinDeDerogation,
    OngletsChecklist,
    DerogationFinancement,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.models import (
    ContinuingEducationAdmission,
    DoctorateAdmission,
    GeneralEducationAdmission,
)
from admission.tests.factories.admission_viewer import AdmissionViewerFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory, \
    ContinuingEducationTrainingFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory, \
    GeneralEducationTrainingFactory
from admission.tests.factories.roles import (
    CentralManagerRoleFactory,
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from admission.views.list import BaseAdmissionList
from base.models.academic_year import AcademicYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.entity_type import EntityType
from base.models.person_merge_proposal import PersonMergeProposal
from base.tests import QueriesAssertionsMixin
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory, MainEntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.user import UserFactory
from education_group.auth.scope import Scope
from program_management.models.education_group_version import EducationGroupVersion
from reference.tests.factories.country import CountryFactory


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
                candidate__country_of_citizenship=CountryFactory(
                    european_union=True,
                    name='Belgique',
                    name_en='Belgium',
                ),
                candidate__first_name="John",
                candidate__last_name="Doe",
                candidate__private_email="jdoe@example.be",
                status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
                training__management_entity=cls.first_entity,
                training__acronym="ABCD0",
                last_update_author__user__username='user1',
                submitted_at=datetime.datetime(2023, 1, 1),
                cycle_pursuit=PoursuiteDeCycle.YES.name,
            ),
        ]

        cls.admissions[0].last_update_author = cls.admissions[0].candidate
        cls.admissions[0].save()

        admission_viewers = [
            AdmissionViewerFactory(person=cls.sic_management_user.person, admission=cls.admissions[0]),
            AdmissionViewerFactory(person=cls.other_sic_management, admission=cls.admissions[0]),
        ]

        lite_reference = '{:08}'.format(cls.admissions[0].reference)
        cls.lite_reference = f'{lite_reference[:4]}.{lite_reference[4:]}'

        teaching_campus = (
            EducationGroupVersion.objects.filter(offer=cls.admissions[0].training)
            .first()
            .root_group.main_teaching_campus.name
        )

        cls.academic_calendar_2023 = AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=datetime.date(2022, 11, 1),
            end_date=datetime.date(2023, 10, 31),
            data_year=AcademicYear.objects.get(year=2023),
        )
        cls.academic_calendar_2024 = AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=datetime.date(2023, 11, 1),
            end_date=datetime.date(2024, 10, 31),
            data_year=AcademicYear.objects.get(year=2024),
        )

        cls.results = [
            DemandeRechercheDTO(
                uuid=cls.admissions[0].uuid,
                numero_demande=f'M-ABCDEF22-{cls.lite_reference}',
                nom_candidat=cls.admissions[0].candidate.last_name,
                prenom_candidat=cls.admissions[0].candidate.first_name,
                noma_candidat=ANY,
                plusieurs_demandes=False,
                sigle_formation=cls.admissions[0].training.acronym,
                code_formation=cls.admissions[0].training.partial_acronym,
                intitule_formation=cls.admissions[0].training.title,
                type_formation=cls.admissions[0].training.education_group_type.name,
                lieu_formation=teaching_campus,
                est_inscription_tardive=None,
                est_modification_inscription_externe=None,
                est_reorientation_inscription_externe=None,
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
                derniere_modification_par='{} {}'.format(
                    cls.admissions[0].last_update_author.first_name,
                    cls.admissions[0].last_update_author.last_name,
                ),
                derniere_modification_par_candidat=True,
                dernieres_vues_par=[
                    VisualiseurAdmissionDTO(
                        nom=admission_viewers[1].person.last_name,
                        prenom=admission_viewers[1].person.first_name,
                        date=admission_viewers[1].viewed_at,
                    ),
                ],
                date_confirmation=cls.admissions[0].submitted_at,
                est_premiere_annee=False,
                poursuite_de_cycle='',
                annee_formation=cls.admissions[0].training.academic_year.year,
                annee_calculee=cls.admissions[0].determined_academic_year.year
                if cls.admissions[0].determined_academic_year
                else None,
                adresse_email_candidat=cls.admissions[0].candidate.private_email,
                reponses_questions_specifiques={},
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
        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES + allowed_sql_surplus):
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

    @freezegun.freeze_time('2023-10-31')
    def test_list_initialization_just_before_academic_year_change(self):
        self.client.force_login(user=self.sic_management_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        form = response.context['filter_form']
        self.assertEqual(form['annee_academique'].initial, 2023)

    @freezegun.freeze_time('2023-11-01')
    def test_list_initialization_just_after_academic_year_change(self):
        self.client.force_login(user=self.sic_management_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        form = response.context['filter_form']
        self.assertEqual(form['annee_academique'].initial, 2024)

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
        self.client.force_login(user=ProgramManagerRoleFactory(
            education_group=GeneralEducationTrainingFactory().education_group,
        ).person.user)

        response = self._do_request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        program_manager = ProgramManagerRoleFactory(education_group=self.admissions[0].training.education_group)
        ProgramManagerRoleFactory.create_batch(10, person=program_manager.person)
        self.client.force_login(user=program_manager.person.user)

        response = self._do_request()
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(self.results[0].uuid, response.context['object_list'][0].uuid)

        self.client.force_login(user=ProgramManagerRoleFactory(
            education_group=DoctorateFactory().education_group,
        ).person.user)

        response = self._do_request()
        self.assertEqual(response.status_code, 403)

        self.client.force_login(user=ProgramManagerRoleFactory(
            education_group=ContinuingEducationTrainingFactory().education_group,
        ).person.user)

        response = self._do_request()
        self.assertEqual(response.status_code, 403)

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

        # Lite reference (e.g. 0000.1111)
        response = self._do_request(numero=self.lite_reference)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # Complete reference (e.g. L-ACRO23-0000.1111)
        response = self._do_request(numero=self.results[0].numero_demande)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_noma(self):
        self.client.force_login(user=self.sic_management_user)

        # Unknown noma -> No results
        response = self._do_request(noma='01234567', allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        # noma from the student model
        student = StudentFactory(
            person=self.admissions[0].candidate,
            registration_id='01234567',
        )

        response = self._do_request(noma=student.registration_id, allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])
        self.assertEqual(self.results[0].noma_candidat, student.registration_id)

        student.delete()

        # noma from the personmergeproposal model
        person_proposal = PersonMergeProposal(
            original_person=self.admissions[0].candidate,
            last_similarity_result_update=datetime.datetime.now(),
            registration_id_sent_to_digit='76543210',
        )

        person_proposal.save()

        response = self._do_request(noma=person_proposal.registration_id_sent_to_digit, allowed_sql_surplus=1)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])
        self.assertEqual(self.results[0].noma_candidat, person_proposal.registration_id_sent_to_digit)

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

        # With faculty
        response = self._do_request(entites='ABCDEF', allowed_sql_surplus=2)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

        # With school
        response = self._do_request(entites='GHIJK', allowed_sql_surplus=2)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

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

        response = self._do_request(etats=[self.admissions[0].status])
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_training_type(self):
        self.client.force_login(user=self.sic_management_user)

        response = self._do_request(types_formation=self.admissions[0].training.education_group_type.name)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.results[0], response.context['object_list'])

    def test_list_with_filter_by_late_enrollment_reorientation_or_course_change(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            training=self.admissions[0].training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # No late enrollment, reorientation or course change
        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.REORIENTATION.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.MODIFICATION_INSCRIPTION.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.INSCRIPTION_TARDIVE.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        # Late enrollment
        second_admission.late_enrollment = True
        second_admission.save()

        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.INSCRIPTION_TARDIVE.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.REORIENTATION.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.MODIFICATION_INSCRIPTION.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        second_admission.late_enrollment = None

        # Course change
        second_admission.is_external_modification = True
        second_admission.save()

        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.MODIFICATION_INSCRIPTION.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.REORIENTATION.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.INSCRIPTION_TARDIVE.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        second_admission.is_external_modification = None

        # Reorientation
        second_admission.is_external_reorientation = True
        second_admission.save()

        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.REORIENTATION.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.MODIFICATION_INSCRIPTION.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(
            tardif_modif_reorientation=TardiveModificationReorientationFiltre.INSCRIPTION_TARDIVE.name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

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

    def test_cached_sorted_list(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            training=self.admissions[0].training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        third_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            training=self.admissions[0].training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        response = self._do_request()

        self.assertEqual(response.status_code, 200)
        result = response.context['object_list']

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].uuid, self.admissions[0].uuid)
        self.assertEqual(result[1].uuid, second_admission.uuid)
        self.assertEqual(result[2].uuid, third_admission.uuid)

        cached_admissions = cache.get(BaseAdmissionList.cache_key_for_result(user_id=self.sic_management_user.id))

        self.assertIsNotNone(cached_admissions)

        self.assertEqual(len(cached_admissions), 3)
        self.assertEqual(
            cached_admissions,
            {
                result[0].uuid: {'previous': None, 'next': result[1].uuid},
                result[1].uuid: {'previous': result[0].uuid, 'next': result[2].uuid},
                result[2].uuid: {'previous': result[1].uuid, 'next': None},
            },
        )

        response = self.client.get(resolve_url('admission:general-education:person', uuid=result[0].uuid))

        self.assertEqual(response.status_code, 200)

        context = response.context
        self.assertEqual(context.get('previous_admission_url'), None)
        self.assertEqual(context.get('next_admission_url'), resolve_url('admission:base', uuid=result[1].uuid))

        response = self.client.get(resolve_url('admission:general-education:person', uuid=result[1].uuid))

        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context.get('previous_admission_url'), resolve_url('admission:base', uuid=result[0].uuid))
        self.assertEqual(context.get('next_admission_url'), resolve_url('admission:base', uuid=result[2].uuid))

        response = self.client.get(resolve_url('admission:general-education:person', uuid=result[2].uuid))

        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context.get('previous_admission_url'), resolve_url('admission:base', uuid=result[1].uuid))
        self.assertEqual(context.get('next_admission_url'), None)

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
            candidate__country_of_citizenship=CountryFactory(european_union=False, name='Andorre', name_en='Andorra'),
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

    def test_list_sort_by_identification_checklist_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
            'numero': str(second_admission),
        }

        current_checklist = second_admission.checklist['current'][OngletsChecklist.donnees_personnelles.name]
        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        current_checklist['extra'] = {}
        second_admission.save(update_fields=['checklist'])

        # To be processed
        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_0=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        current_checklist['extra'] = {}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_0=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # To be completed
        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_0=['A_COMPLETER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        current_checklist['extra'] = {'fraud': '0'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_0=['A_COMPLETER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # Fraudster
        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_0=['FRAUDEUR'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        current_checklist['extra'] = {'fraud': '1'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_0=['FRAUDEUR'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # Validated
        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_0=['VALIDEES'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        current_checklist['extra'] = {}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_0=['VALIDEES'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

    def test_list_filter_by_assimilation_checklist_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
            'numero': str(second_admission),
        }

        current_checklist = second_admission.checklist['current'][OngletsChecklist.assimilation.name]

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['NON_CONCERNE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['NON_CONCERNE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['DECLARE_ASSIMILE_OU_PAS'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['DECLARE_ASSIMILE_OU_PAS'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['A_COMPLETER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['A_COMPLETER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['AVIS_EXPERT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['AVIS_EXPERT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['A_COMPLETER_APRES_INSCRIPTION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE_ULTERIEUR.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['A_COMPLETER_APRES_INSCRIPTION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['VALIDEE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_1=['VALIDEE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

    def test_list_filter_by_application_fees_checklist_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
            'numero': str(second_admission),
        }

        current_checklist = second_admission.checklist['current'][OngletsChecklist.frais_dossier.name]

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_2=['NON_CONCERNE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_2=['NON_CONCERNE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_2=['DOIT_PAYER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_2=['DOIT_PAYER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_2=['DISPENSE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_2=['DISPENSE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_2=['PAYES'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.SYST_REUSSITE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_2=['PAYES'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

    def test_list_filter_by_past_experience_checklist_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
            'numero': str(second_admission),
        }

        current_checklist = second_admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_3=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_3=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_3=['TOILETTE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_3=['TOILETTE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_3=['INSUFFISANT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_3=['INSUFFISANT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_3=['SUFFISANT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_3=['SUFFISANT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

    def test_list_filter_by_past_experiences_checklist_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
            'numero': str(second_admission),
        }

        current_checklist = Checklist.initialiser_checklist_experience(experience_uuid=uuid.uuid4()).to_dict()
        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name

        second_admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]['enfants'].append(
            current_checklist
        )

        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['A_COMPLETER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['A_COMPLETER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['AUTHENTIFICATION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        current_checklist['extra'] = {'authentification': '1'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['AUTHENTIFICATION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['AVIS_EXPERT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        current_checklist['extra'] = {'authentification': '0'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['AVIS_EXPERT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['A_COMPLETER_APRES_INSCRIPTION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE_ULTERIEUR.name
        current_checklist['extra'] = {}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['A_COMPLETER_APRES_INSCRIPTION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['VALIDEE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        current_checklist['extra'] = {}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=['VALIDEE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # Hierarchical filter : experience authentification criteria
        current_authentication = 'AUTHENTIFICATION.' + EtatAuthentificationParcours.VRAI.name
        other_authentication = 'AUTHENTIFICATION.' + EtatAuthentificationParcours.FAUX.name

        # Filter by child criteria
        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=[current_authentication],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['extra'] = {
            'etat_authentification': EtatAuthentificationParcours.VRAI.name,
        }
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=[current_authentication],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        current_checklist['extra']['authentification'] = '1'
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=[current_authentication],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # Filter by parent and child criteria (logical conjunction)
        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=[current_authentication, 'AUTHENTIFICATION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_4=[other_authentication, 'AUTHENTIFICATION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_filter_by_financeability_checklist_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
            'numero': str(second_admission),
        }

        current_checklist = second_admission.checklist['current'][OngletsChecklist.financabilite.name]

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['NON_CONCERNE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['NON_CONCERNE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['AVIS_EXPERT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        current_checklist['extra'] = {'en_cours': 'expert'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['AVIS_EXPERT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['A_COMPLETER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        current_checklist['extra'] = {'to_be_completed': '1'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['A_COMPLETER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['NON_FINANCABLE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        current_checklist['extra'] = {'to_be_completed': '0'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['NON_FINANCABLE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['FINANCABLE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        current_checklist['extra'] = {'reussite': 'financable'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=['FINANCABLE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=[
                'BESOIN_DEROGATION',
                f'BESOIN_DEROGATION.{DerogationFinancement.ABANDON_DU_CANDIDAT.name}',
            ],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        second_admission.checklist['current'][OngletsChecklist.financabilite.name] = {
            'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
            'extra': {'en_cours': 'derogation'},
        }
        second_admission.financability_dispensation_status = DerogationFinancement.ABANDON_DU_CANDIDAT.name
        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        current_checklist['extra'] = {'en_cours': 'derogation'}
        second_admission.save(update_fields=['financability_dispensation_status', 'checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=[
                'BESOIN_DEROGATION',
                f'BESOIN_DEROGATION.{DerogationFinancement.ABANDON_DU_CANDIDAT.name}',
            ],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=[
                f'BESOIN_DEROGATION.{DerogationFinancement.ABANDON_DU_CANDIDAT.name}',
            ],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_5=[
                'AVIS_EXPERT',
                f'BESOIN_DEROGATION.{DerogationFinancement.ABANDON_DU_CANDIDAT.name}',
            ],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

    def test_list_filter_by_training_choice_checklist_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
            'numero': str(second_admission),
        }

        current_checklist = second_admission.checklist['current'][OngletsChecklist.choix_formation.name]
        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_6=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_6=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_6=['VALIDE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_6=['VALIDE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

    def test_list_filter_by_specificities_checklist_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
            'numero': str(second_admission),
        }

        current_checklist = second_admission.checklist['current'][OngletsChecklist.specificites_formation.name]

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_7=['NON_CONCERNE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_7=['NON_CONCERNE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_7=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_7=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_7=['INSUFFISANT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_7=['INSUFFISANT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_7=['SUFFISANT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_7=['SUFFISANT'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

    def test_list_filter_by_fac_decision_checklist_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
            'numero': str(second_admission),
        }

        current_checklist = second_admission.checklist['current'][OngletsChecklist.decision_facultaire.name]
        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_8=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_8=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_8=['PRIS_EN_CHARGE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_8=['PRIS_EN_CHARGE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_8=['A_COMPLETER_PAR_SIC'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        current_checklist['extra'] = {'decision': DecisionFacultaireEnum.HORS_DECISION.value}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_8=['A_COMPLETER_PAR_SIC'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_8=['REFUS'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        current_checklist['extra'] = {'decision': DecisionFacultaireEnum.EN_DECISION.value}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_8=['REFUS'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_8=['ACCORD'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        current_checklist['extra'] = {}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_8=['ACCORD'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

    def test_list_filter_by_sic_decision_checklist_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
            'numero': str(second_admission),
        }

        current_checklist = second_admission.checklist['current'][OngletsChecklist.decision_sic.name]
        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_NON_CONCERNE.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['A_TRAITER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['A_COMPLETER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        current_checklist['extra'] = {'blocage': 'to_be_completed'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['A_COMPLETER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['BESOIN_DEROGATION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        current_checklist['extra'] = {'en_cours': 'derogation'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['BESOIN_DEROGATION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['REFUS_A_VALIDER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        current_checklist['extra'] = {'en_cours': 'refusal'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['REFUS_A_VALIDER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['AUTORISATION_A_VALIDER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        current_checklist['extra'] = {'en_cours': 'approval'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['AUTORISATION_A_VALIDER'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['CLOTURE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        current_checklist['extra'] = {'blocage': 'closed'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['CLOTURE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['REFUSE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_BLOCAGE.name
        current_checklist['extra'] = {'blocage': 'refusal'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['REFUSE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['AUTORISE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        current_checklist['extra'] = {}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=['AUTORISE'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # Hierarchical filter : dispensation needed criteria
        dispensation_needed = f'BESOIN_DEROGATION.{BesoinDeDerogation.ACCORD_DIRECTION.name}'
        other_dispensation_needed = f'BESOIN_DEROGATION.{BesoinDeDerogation.REFUS_DIRECTION.name}'

        # Filter by child criteria
        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=[dispensation_needed],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        second_admission.dispensation_needed = BesoinDeDerogation.ACCORD_DIRECTION.name
        second_admission.save(update_fields=['dispensation_needed'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=[dispensation_needed],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)

        current_checklist['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        current_checklist['extra'] = {'en_cours': 'derogation'}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=[dispensation_needed],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # Filter by parent and child criteria (logical conjunction)
        # If a specific dispensation status is selected, the parent status (tab status) should be ignored to prevent
        # to select every admission whose the sic decision checklist tab status is the dispensation needed status
        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=[dispensation_needed, 'BESOIN_DEROGATION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=[other_dispensation_needed, 'BESOIN_DEROGATION'],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(
            **default_cmd_params,
            filtres_etats_checklist_9=[
                'BESOIN_DEROGATION',
                f'BESOIN_DEROGATION.{BesoinDeDerogation.REFUS_DIRECTION.name}',
            ],
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_filter_by_excluding_checklist_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.EXCLUSION.name,
            'numero': str(second_admission),
            'filtres_etats_checklist_0': ['FRAUDEUR'],
        }

        # The admission has the specific status and extra info so we exclude it
        second_admission.checklist['current'][OngletsChecklist.donnees_personnelles.name] = {
            'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
            'extra': {'fraud': '1'},
        }
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        # The admission has the specific status but not the right extra info so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.donnees_personnelles.name] = {
            'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
            'extra': {'fraud': '0'},
        }
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # The admission has the specific extra info but not the right status so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.donnees_personnelles.name] = {
            'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
            'extra': {'fraud': '1'},
        }
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # The admission has not any specified status for this tab so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.donnees_personnelles.name] = {
            'extra': {'fraud': '1'},
        }
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # The admission has not any specified extra info for this tab so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.donnees_personnelles.name] = {
            'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
        }

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # The admission has empty info for the specific tab so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.donnees_personnelles.name] = {}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # The admission has no info for the specific tab so we don't exclude it
        second_admission.checklist['current'].pop(OngletsChecklist.donnees_personnelles.name)
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # The admission has no initialized checklist so we don't exclude it
        second_admission.checklist = {}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

    def test_list_filter_by_excluding_with_dispensation_needed_criteria(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.EXCLUSION.name,
            'numero': str(second_admission),
            'filtres_etats_checklist_9': [f'BESOIN_DEROGATION.{BesoinDeDerogation.ACCORD_DIRECTION.name}'],
        }

        # The admission has the specific dispensation needed state and the specific checklist tab status so we exclude
        # it
        second_admission.dispensation_needed = BesoinDeDerogation.ACCORD_DIRECTION.name
        second_admission.checklist['current']['decision_sic']['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        second_admission.checklist['current']['decision_sic']['extra'] = {'en_cours': 'derogation'}
        second_admission.save(update_fields=['dispensation_needed', 'checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        # The admission hasn't got the dispensation needed field so we don't exclude it
        third_admission = ContinuingEducationAdmissionFactory(
            training__management_entity=self.first_entity,
        )

        response = self._do_request(
            numero=str(third_admission),
            filtres_etats_checklist_9=default_cmd_params['filtres_etats_checklist_9'],
            mode_filtres_etats_checklist=default_cmd_params['mode_filtres_etats_checklist'],
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(third_admission.uuid, response.context['object_list'][0].uuid)

        # The admission hasn't got the specific dispensation needed state so we don't exclude it
        second_admission.dispensation_needed = BesoinDeDerogation.NON_CONCERNE.name
        second_admission.save(update_fields=['dispensation_needed'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # The admission has the specific dispensation needed state so we exclude it
        second_admission.dispensation_needed = BesoinDeDerogation.ACCORD_DIRECTION.name
        second_admission.checklist['current']['decision_sic']['statut'] = ChoixStatutChecklist.INITIAL_CANDIDAT.name
        second_admission.save(update_fields=['dispensation_needed', 'checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        # The admission has the specific dispensation needed state but not the parent checklist tab status so we
        # don't exclude it
        params_with_parent_checklist = {
            **default_cmd_params,
            'filtres_etats_checklist_9': [
                'BESOIN_DEROGATION',
                f'BESOIN_DEROGATION.{BesoinDeDerogation.ACCORD_DIRECTION.name}',
            ],
        }
        response = self._do_request(**params_with_parent_checklist)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(second_admission.uuid, response.context['object_list'][0].uuid)

        # The admission has the specific dispensation needed state and the specific parent checklist tab status so we exclude it
        second_admission.dispensation_needed = BesoinDeDerogation.ACCORD_DIRECTION.name
        second_admission.checklist['current']['decision_sic']['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        second_admission.checklist['current']['decision_sic']['extra'] = {'en_cours': 'derogation'}
        second_admission.save(update_fields=['dispensation_needed', 'checklist'])

        response = self._do_request(**params_with_parent_checklist)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_filter_by_excluding_with_checklist_experience_status(self):
        self.client.force_login(user=self.sic_management_user)

        second_admission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        default_cmd_params = {
            'mode_filtres_etats_checklist': ModeFiltrageChecklist.EXCLUSION.name,
            'numero': str(second_admission),
            'filtres_etats_checklist_4': [f'AUTHENTIFICATION.{EtatAuthentificationParcours.VRAI.name}'],
        }

        second_admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
                'extra': {'authentification': '1', 'etat_authentification': EtatAuthentificationParcours.VRAI.name},
            }
        ]
        second_admission.save(update_fields=['checklist'])

        # The admission has the specific status and checklist info for one experience so we exclude it
        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        # The admission hasn't got the specific status for one experience so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
                'extra': {'authentification': '1'},
            }
        ]
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # The admission hasn't got the specific authentification state for one experience so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
                'extra': {'authentification': '1', 'etat_authentification': EtatAuthentificationParcours.FAUX.name},
            }
        ]
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # The admission hasn't got the specific extra info for one experience so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
                'extra': {'authentification': '0'},
            }
        ]
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # The experience hasn't got any specified status so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]['enfants'] = [
            {
                'extra': {'authentification': '0'},
            }
        ]
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # The experience has empty extra info so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
                'extra': {},
            }
        ]
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # The experience has no extra info so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
            }
        ]
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # The admission has no specified experiences so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.parcours_anterieur.name]['enfants'] = []
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # The admission checklist for the past experiences has no child attribute so we don't exclude it
        second_admission.checklist['current'][OngletsChecklist.parcours_anterieur.name].pop('enfants')
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # The admission has no checklist info for the past experiences tab so we don't exclude it
        second_admission.checklist['current'].pop(OngletsChecklist.parcours_anterieur.name)
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # The admission has no checklist current info so we don't exclude it
        second_admission.checklist = {}
        second_admission.save(update_fields=['checklist'])

        response = self._do_request(**default_cmd_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
