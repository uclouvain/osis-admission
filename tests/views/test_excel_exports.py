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

import ast
import datetime
from unittest import mock

import freezegun
import mock
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.translation import gettext as _
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from osis_async.models import AsyncTask
from osis_async.models.enums import TaskState

from admission.ddd.admission.dtos.liste import DemandeRechercheDTO, VisualiseurAdmissionDTO
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests import QueriesAssertionsMixin
from admission.tests.factories.admission_viewer import AdmissionViewerFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory
from admission.tests.factories.scholarship import (
    InternationalScholarshipFactory,
    DoubleDegreeScholarshipFactory,
    ErasmusMundusScholarshipFactory,
)
from admission.views.excel_exports import AdmissionListExcelExportView
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from osis_export.models import Export
from osis_export.models.enums.types import ExportTypes
from program_management.models.education_group_version import EducationGroupVersion
from reference.tests.factories.country import CountryFactory


class UnfrozenDTO:
    # Trick to make this "unfrozen" just for tests
    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

    def __delattr__(self, item):
        object.__delattr__(self, item)


class _DemandeRechercheDTO(UnfrozenDTO, DemandeRechercheDTO):
    pass


@freezegun.freeze_time('2023-01-01')
class AdmissionListExcelExportViewTestCase(QueriesAssertionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        # Users
        cls.user = User.objects.create_user(
            username='john_doe',
            password='top_secret',
        )

        cls.sic_management_user = SicManagementRoleFactory().person.user
        cls.other_sic_manager = SicManagementRoleFactory().person

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
        cls.admission = GeneralEducationAdmissionFactory(
            candidate__country_of_citizenship=CountryFactory(european_union=True, name='Belgique'),
            candidate__first_name="John",
            candidate__last_name="Doe",
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            training__management_entity=cls.first_entity,
            training__acronym="ABCD0",
            last_update_author__user__username='user1',
            submitted_at=datetime.date(2023, 1, 2),
        )

        cls.admission.last_update_author = cls.admission.candidate
        cls.admission.save()

        admission_viewers = [
            AdmissionViewerFactory(person=cls.sic_management_user.person, admission=cls.admission),
            AdmissionViewerFactory(person=cls.other_sic_manager, admission=cls.admission),
        ]

        cls.lite_reference = '{:07,}'.format(cls.admission.reference).replace(',', '.')

        cls.student = StudentFactory(
            person=cls.admission.candidate,
            registration_id='01234567',
        )

        teaching_campus = (
            EducationGroupVersion.objects.filter(offer=cls.admission.training)
            .first()
            .root_group.main_teaching_campus.name
        )

        cls.result = _DemandeRechercheDTO(
            uuid=cls.admission.uuid,
            numero_demande=f'M-ABCDEF22-{cls.lite_reference}',
            nom_candidat=cls.admission.candidate.last_name,
            prenom_candidat=cls.admission.candidate.first_name,
            noma_candidat=cls.admission.candidate.last_registration_id,
            plusieurs_demandes=False,
            sigle_formation=cls.admission.training.acronym,
            code_formation=cls.admission.training.partial_acronym,
            intitule_formation=cls.admission.training.title,
            type_formation=cls.admission.training.education_group_type.name,
            lieu_formation=teaching_campus,
            nationalite_candidat=cls.admission.candidate.country_of_citizenship.name,
            nationalite_ue_candidat=cls.admission.candidate.country_of_citizenship.european_union,
            vip=any(
                scholarship
                for scholarship in [
                    cls.admission.erasmus_mundus_scholarship,
                    cls.admission.international_scholarship,
                    cls.admission.double_degree_scholarship,
                ]
            ),
            etat_demande=cls.admission.status,
            type_demande=cls.admission.type_demande,
            derniere_modification_le=cls.admission.modified_at,
            derniere_modification_par=cls.admission.last_update_author.user.username,
            derniere_modification_par_candidat=True,
            dernieres_vues_par=[
                VisualiseurAdmissionDTO(
                    nom=admission_viewers[1].person.last_name,
                    prenom=admission_viewers[1].person.first_name,
                    date=admission_viewers[1].viewed_at,
                ),
            ],
            date_confirmation=cls.admission.submitted_at,
        )

        cls.default_params = {
            'annee_academique': 2022,
            'taille_page': 10,
        }

        # Targeted url
        cls.url = reverse('admission:admission-list-excel-export')
        cls.list_url = reverse('admission:all-list')

    def test_export_user_without_person(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_export_candidate_user(self):
        self.client.force_login(user=self.admission.candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_export_sic_management_user(self):
        self.client.force_login(user=self.sic_management_user)

        response = self.client.get(self.url)
        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        response = self.client.get(
            self.url,
            **{"HTTP_HX-Request": 'true'},
        )

        self.assertEqual(response.status_code, 200)

    def test_export_with_sic_management_user_without_filters_doesnt_plan_the_export(self):
        self.client.force_login(user=self.sic_management_user)

        response = self.client.get(self.url)

        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        task = AsyncTask.objects.filter(person=self.sic_management_user.person).first()
        self.assertIsNone(task)

        export = Export.objects.filter(person=self.sic_management_user.person).first()
        self.assertIsNone(export)

    def test_export_with_sic_management_user_with_filters_plans_the_export(self):
        self.client.force_login(user=self.sic_management_user)

        response = self.client.get(self.url, data=self.default_params)

        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        task = AsyncTask.objects.filter(person=self.sic_management_user.person).first()
        self.assertIsNotNone(task)
        self.assertEqual(task.name, _('Admission applications export'))
        self.assertEqual(task.description, _('Excel export of admission applications'))
        self.assertEqual(task.state, TaskState.PENDING.name)

        export = Export.objects.filter(job_uuid=task.uuid).first()
        self.assertIsNotNone(export)
        self.assertEqual(export.called_from_class, 'admission.views.excel_exports.AdmissionListExcelExportView')
        self.assertEqual(export.file_name, 'export-des-demandes-dadmission')
        self.assertEqual(export.type, ExportTypes.EXCEL.name)

        filters = ast.literal_eval(export.filters)
        self.assertEqual(filters.get('annee_academique'), self.default_params.get('annee_academique'))

    def test_export_content(self):
        view = AdmissionListExcelExportView()
        header = view.get_header()
        row_data = view.get_row_data(self.result)
        self.assertEqual(len(header), len(row_data))

        self.assertEqual(row_data[0], self.result.numero_demande)
        self.assertEqual(row_data[1], self.result.nom_candidat)
        self.assertEqual(row_data[2], self.result.prenom_candidat)
        self.assertEqual(row_data[3], self.result.noma_candidat)
        self.assertEqual(row_data[4], 'non')
        self.assertEqual(row_data[5], self.result.sigle_formation)
        self.assertEqual(row_data[6], self.result.intitule_formation)
        self.assertEqual(row_data[7], self.result.nationalite_candidat)
        self.assertEqual(row_data[8], 'oui')
        self.assertEqual(row_data[9], ChoixStatutPropositionGenerale.CONFIRMEE.value)
        self.assertEqual(row_data[10], _('candidate'))
        self.assertEqual(row_data[11], '2023/01/01, 00:00:00')
        self.assertEqual(row_data[12], '2023/01/02, 00:00:00')

        with mock.patch.object(self.result, 'date_confirmation', None):
            row_data = view.get_row_data(self.result)
            self.assertEqual(row_data[12], '')

        with mock.patch.object(self.result, 'plusieurs_demandes', True):
            row_data = view.get_row_data(self.result)
            self.assertEqual(row_data[4], 'oui')

    def test_export_configuration(self):
        candidate = PersonFactory()
        campus = CampusFactory()
        international_scholarship = InternationalScholarshipFactory(short_name='ID1')
        double_degree_scholarship = DoubleDegreeScholarshipFactory(short_name="DD1")
        erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory(short_name="EM1")
        filters = str(
            {
                'annee_academique': 2022,
                'numero': 1,
                'noma': '00000001',
                'matricule_candidat': candidate.global_id,
                'etats': [ChoixStatutPropositionGenerale.CONFIRMEE.name],
                'type': TypeDemande.ADMISSION.name,
                'site_inscription': str(campus.uuid),
                'entites': 'ENT',
                'types_formation': [TrainingType.BACHELOR.name, TrainingType.PHD.name],
                'formation': 'Informatique',
                'bourse_internationale': str(international_scholarship.uuid),
                'bourse_erasmus_mundus': str(erasmus_mundus_scholarship.uuid),
                'bourse_double_diplomation': str(double_degree_scholarship.uuid),
            }
        )

        view = AdmissionListExcelExportView()
        workbook = Workbook()
        worksheet: Worksheet = workbook.create_sheet()

        view.customize_parameters_worksheet(
            worksheet=worksheet,
            person=self.sic_management_user.person,
            filters=filters,
        )

        names, values = list(worksheet.iter_cols(values_only=True))
        self.assertEqual(len(names), 16)
        self.assertEqual(len(values), 16)

        # Check the names of the parameters
        self.assertEqual(names[0], _('Creation date'))
        self.assertEqual(names[1], _('Created by'))
        self.assertEqual(names[2], _('Description'))
        self.assertEqual(names[3], _('Year'))
        self.assertEqual(names[4], _('Application numero'))
        self.assertEqual(names[5], _('Noma'))
        self.assertEqual(names[6], _('Last name / First name / E-mail'))
        self.assertEqual(names[7], _('Application status'))
        self.assertEqual(names[8], _('Application type'))
        self.assertEqual(names[9], _('Enrolment campus'))
        self.assertEqual(names[10], _('Entities'))
        self.assertEqual(names[11], _('Training type'))
        self.assertEqual(names[12], _('Training'))
        self.assertEqual(names[13], _('International scholarship'))
        self.assertEqual(names[14], _('Erasmus Mundus'))
        self.assertEqual(names[15], _('Double degree scholarship'))

        # Check the values of the parameters
        self.assertEqual(values[0], '1 Janvier 2023')
        self.assertEqual(values[1], self.sic_management_user.person.full_name)
        self.assertEqual(values[2], _('Export') + ' - Admissions')
        self.assertEqual(values[3], '2022')
        self.assertEqual(values[4], '1')
        self.assertEqual(values[5], '00000001')
        self.assertEqual(values[6], candidate.full_name)
        self.assertEqual(values[7], f"['{ChoixStatutPropositionGenerale.CONFIRMEE.value}']")
        self.assertEqual(values[8], TypeDemande.ADMISSION.value)
        self.assertEqual(values[9], campus.name)
        self.assertEqual(values[10], 'ENT')
        self.assertEqual(values[11], f"['{TrainingType.BACHELOR.value}', '{TrainingType.PHD.value}']")
        self.assertEqual(values[12], 'Informatique')
        self.assertEqual(values[13], international_scholarship.short_name)
        self.assertEqual(values[14], erasmus_mundus_scholarship.short_name)
        self.assertEqual(values[15], double_degree_scholarship.short_name)
