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

import ast
import datetime
from typing import List
from unittest import mock

import freezegun
import mock
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _, pgettext
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from osis_async.models import AsyncTask
from osis_async.models.enums import TaskState
from osis_export.models import Export
from osis_export.models.enums.types import ExportTypes

from admission.ddd.admission.dtos.liste import DemandeRechercheDTO, VisualiseurAdmissionDTO
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_continue.commands import ListerDemandesQuery
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue, ChoixEdition
from admission.ddd.admission.formation_continue.dtos.liste import DemandeRechercheDTO as DemandeContinueRechercheDTO
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    OngletsChecklist,
)
from admission.tests.factories.admission_viewer import AdmissionViewerFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory
from admission.tests.factories.scholarship import (
    InternationalScholarshipFactory,
    DoubleDegreeScholarshipFactory,
    ErasmusMundusScholarshipFactory,
)
from admission.views.excel_exports import AdmissionListExcelExportView, ContinuingAdmissionListExcelExportView
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.tests import QueriesAssertionsMixin
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from infrastructure.messages_bus import message_bus_instance
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
@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
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
            candidate__private_email="jdoe@example.be",
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
            est_premiere_annee=False,
            poursuite_de_cycle=cls.admission.cycle_pursuit,
            annee_formation=cls.admission.training.academic_year.year,
            annee_calculee=cls.admission.determined_academic_year.year
            if cls.admission.determined_academic_year
            else None,
            adresse_email_candidat=cls.admission.candidate.private_email,
        )

        cls.default_params = {
            'annee_academique': 2022,
            'taille_page': 10,
            'demandeur': str(cls.sic_management_user.person.uuid),
        }

        # Targeted url
        cls.url = reverse('admission:excel-exports:all-admissions-list')
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
        self.assertEqual(filters.get('demandeur'), self.default_params.get('demandeur'))

    def test_export_with_sic_management_user_with_filters_and_asc_ordering(self):
        self.client.force_login(user=self.sic_management_user)

        # With asc ordering
        response = self.client.get(self.url, data={**self.default_params, 'o': 'numero_demande'})

        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        task = AsyncTask.objects.filter(person=self.sic_management_user.person).first()
        self.assertIsNotNone(task)

        export = Export.objects.filter(job_uuid=task.uuid).first()
        self.assertIsNotNone(export)

        filters = ast.literal_eval(export.filters)
        self.assertEqual(filters.get('annee_academique'), self.default_params.get('annee_academique'))
        self.assertEqual(filters.get('demandeur'), self.default_params.get('demandeur'))
        self.assertEqual(filters.get('tri_inverse'), False)
        self.assertEqual(filters.get('champ_tri'), 'numero_demande')

    def test_export_with_sic_management_user_with_filters_and_desc_ordering(self):
        self.client.force_login(user=self.sic_management_user)

        # With asc ordering
        response = self.client.get(self.url, data={**self.default_params, 'o': '-numero_demande'})

        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        task = AsyncTask.objects.filter(person=self.sic_management_user.person).first()
        self.assertIsNotNone(task)

        export = Export.objects.filter(job_uuid=task.uuid).first()
        self.assertIsNotNone(export)

        filters = ast.literal_eval(export.filters)
        self.assertEqual(filters.get('annee_academique'), self.default_params.get('annee_academique'))
        self.assertEqual(filters.get('demandeur'), self.default_params.get('demandeur'))
        self.assertEqual(filters.get('tri_inverse'), True)
        self.assertEqual(filters.get('champ_tri'), 'numero_demande')

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
                'demandeur': str(self.sic_management_user.person.uuid),
                'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
                'filtres_etats_checklist': {
                    OngletsChecklist.donnees_personnelles.name: ['A_TRAITER'],
                    OngletsChecklist.frais_dossier.name: ['PAYES'],
                },
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
        self.assertEqual(len(names), 18)
        self.assertEqual(len(values), 18)

        # Check the names of the parameters
        self.assertEqual(names[0], _('Creation date'))
        self.assertEqual(names[1], pgettext('masculine', 'Created by'))
        self.assertEqual(names[2], _('Description'))
        self.assertEqual(names[3], _('Year'))
        self.assertEqual(names[4], _('Application numero'))
        self.assertEqual(names[5], _('Noma'))
        self.assertEqual(names[6], _('Last name / First name / Email'))
        self.assertEqual(names[7], _('Application status'))
        self.assertEqual(names[8], _('Application type'))
        self.assertEqual(names[9], _('Enrolment campus'))
        self.assertEqual(names[10], pgettext('admission', 'Entities'))
        self.assertEqual(names[11], _('Course type'))
        self.assertEqual(names[12], pgettext('admission', 'Course'))
        self.assertEqual(names[13], _('International scholarship'))
        self.assertEqual(names[14], _('Erasmus Mundus'))
        self.assertEqual(names[15], _('Dual degree scholarship'))
        self.assertEqual(names[16], _('Include or exclude the checklist filters'))
        self.assertEqual(names[17], _('Checklist filters'))

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
        self.assertEqual(values[16], ModeFiltrageChecklist.INCLUSION.value)
        self.assertEqual(
            values[17],
            str(
                {
                    OngletsChecklist.donnees_personnelles.value: [_('To be processed')],
                    OngletsChecklist.frais_dossier.value: [_('Payed')],
                }
            ),
        )


@freezegun.freeze_time('2023-01-03')
@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class ContinuingAdmissionListExcelExportViewTestCase(QueriesAssertionsMixin, TestCase):
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
        academic_years = AcademicYearFactory.produce(base_year=2023, number_past=2, number_future=2)

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
        candidate = PersonFactory(
            first_name="John",
            last_name="Doe",
            email='john.doe@example.be',
        )
        cls.admission = ContinuingEducationAdmissionFactory(
            candidate=candidate,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            training__management_entity=cls.first_entity,
            training__acronym="ZEBU0",
            training__education_group_type__name=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
            submitted_at=datetime.datetime(2023, 1, 1),
            training__academic_year=academic_years[1],
            determined_academic_year=academic_years[2],
            edition=ChoixEdition.DEUX.name,
            in_payement_order=True,
            modified_at=datetime.datetime(2023, 1, 3),
            last_update_author=candidate,
        )

        cls.student = StudentFactory(
            person=candidate,
            registration_id='01234567',
        )

        cls.default_params = {
            'annee_academique': 2022,
            'taille_page': 10,
            'demandeur': str(cls.sic_management_user.person.uuid),
        }

        # Targeted url
        cls.url = reverse('admission:excel-exports:continuing-admissions-list')
        cls.list_url = reverse('admission:continuing-education:list')

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
        self.assertEqual(
            export.called_from_class,
            'admission.views.excel_exports.ContinuingAdmissionListExcelExportView',
        )
        self.assertEqual(export.file_name, 'export-des-demandes-dadmission')
        self.assertEqual(export.type, ExportTypes.EXCEL.name)

        filters = ast.literal_eval(export.filters)
        self.assertEqual(filters.get('annee_academique'), self.default_params.get('annee_academique'))
        self.assertEqual(filters.get('demandeur'), self.default_params.get('demandeur'))

    def test_export_with_sic_management_user_with_filters_and_asc_ordering(self):
        self.client.force_login(user=self.sic_management_user)

        # With asc ordering
        response = self.client.get(self.url, data={**self.default_params, 'o': 'numero_demande'})

        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        task = AsyncTask.objects.filter(person=self.sic_management_user.person).first()
        self.assertIsNotNone(task)

        export = Export.objects.filter(job_uuid=task.uuid).first()
        self.assertIsNotNone(export)

        filters = ast.literal_eval(export.filters)
        self.assertEqual(filters.get('annee_academique'), self.default_params.get('annee_academique'))
        self.assertEqual(filters.get('demandeur'), self.default_params.get('demandeur'))
        self.assertEqual(filters.get('tri_inverse'), False)
        self.assertEqual(filters.get('champ_tri'), 'numero_demande')

    def test_export_with_sic_management_user_with_filters_and_desc_ordering(self):
        self.client.force_login(user=self.sic_management_user)

        # With asc ordering
        response = self.client.get(self.url, data={**self.default_params, 'o': '-numero_demande'})

        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        task = AsyncTask.objects.filter(person=self.sic_management_user.person).first()
        self.assertIsNotNone(task)

        export = Export.objects.filter(job_uuid=task.uuid).first()
        self.assertIsNotNone(export)

        filters = ast.literal_eval(export.filters)
        self.assertEqual(filters.get('annee_academique'), self.default_params.get('annee_academique'))
        self.assertEqual(filters.get('demandeur'), self.default_params.get('demandeur'))
        self.assertEqual(filters.get('tri_inverse'), True)
        self.assertEqual(filters.get('champ_tri'), 'numero_demande')

    def test_export_content(self):
        view = ContinuingAdmissionListExcelExportView()
        header = view.get_header()

        results: List[DemandeContinueRechercheDTO] = message_bus_instance.invoke(
            ListerDemandesQuery(numero=self.admission.reference)
        )

        self.assertEqual(len(results), 1)

        result = results[0]

        row_data = view.get_row_data(result)

        self.assertEqual(len(header), len(row_data))

        self.assertEqual(row_data[0], result.numero_demande)
        self.assertEqual(row_data[1], result.nom_candidat)
        self.assertEqual(row_data[2], result.prenom_candidat)
        self.assertEqual(row_data[3], result.noma_candidat)
        self.assertEqual(row_data[4], result.courriel_candidat)
        self.assertEqual(row_data[5], f'{result.sigle_formation} - {result.intitule_formation}')
        self.assertEqual(row_data[6], '2')
        self.assertEqual(row_data[7], result.sigle_faculte)
        self.assertEqual(row_data[8], 'oui')
        self.assertEqual(row_data[9], ChoixStatutPropositionContinue.CONFIRMEE.value)
        self.assertEqual(row_data[10], '')
        self.assertEqual(row_data[11], '2023/01/01, 00:00:00')
        self.assertEqual(row_data[12], '2023/01/03, 00:00:00')
        self.assertEqual(row_data[13], 'Candidat')

        # Check the export when some specific fields are empty or have a specific value
        self.admission.edition = ''
        self.admission.in_payement_order = False
        self.admission.submitted_at = None
        self.admission.save()

        results: List[DemandeContinueRechercheDTO] = message_bus_instance.invoke(
            ListerDemandesQuery(numero=self.admission.reference)
        )

        self.assertEqual(len(results), 1)

        result = results[0]

        row_data = view.get_row_data(result)

        self.assertEqual(row_data[6], '')
        self.assertEqual(row_data[8], 'non')
        self.assertEqual(row_data[11], '')

        self.admission.in_payement_order = None
        self.admission.save()

        results: List[DemandeContinueRechercheDTO] = message_bus_instance.invoke(
            ListerDemandesQuery(numero=self.admission.reference)
        )

        self.assertEqual(len(results), 1)

        result = results[0]

        row_data = view.get_row_data(result)

        self.assertEqual(row_data[8], 'non')

    def test_export_configuration(self):
        candidate = PersonFactory()
        campus = CampusFactory()
        filters = str(
            {
                'annee_academique': 2022,
                'edition': [ChoixEdition.DEUX.name, ChoixEdition.TROIS.name],
                'numero': self.admission.reference,
                'matricule_candidat': self.admission.candidate.global_id,
                'etats': [ChoixStatutPropositionContinue.EN_BROUILLON.name],
                'facultes': 'ENT',
                'types_formation': [
                    TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name,
                    TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
                ],
                'sigles_formations': [self.admission.training.acronym],
                'inscription_requise': True,
                'paye': False,
                'marque_d_interet': True,
                'demandeur': str(self.sic_management_user.person.uuid),
            }
        )

        view = ContinuingAdmissionListExcelExportView()
        workbook = Workbook()
        worksheet: Worksheet = workbook.create_sheet()

        view.customize_parameters_worksheet(
            worksheet=worksheet,
            person=self.sic_management_user.person,
            filters=filters,
        )

        names, values = list(worksheet.iter_cols(values_only=True))
        self.assertEqual(len(names), 14)
        self.assertEqual(len(values), 14)

        # Check the names of the parameters
        self.assertEqual(names[0], _('Creation date'))
        self.assertEqual(names[1], pgettext('masculine', 'Created by'))
        self.assertEqual(names[2], _('Description'))
        self.assertEqual(names[3], _('Year'))
        self.assertEqual(names[4], _('Edition'))
        self.assertEqual(names[5], _('Application numero'))
        self.assertEqual(names[6], _('Last name / First name / Email / NOMA'))
        self.assertEqual(names[7], _('Application status'))
        self.assertEqual(names[8], _('Faculty'))
        self.assertEqual(names[9], _('Course type'))
        self.assertEqual(names[10], pgettext('admission', 'Course'))
        self.assertEqual(names[11], _('Registration required'))
        self.assertEqual(names[12], _('Paid'))
        self.assertEqual(names[13], _('Interested mark'))

        # Check the values of the parameters
        self.assertEqual(values[0], '3 Janvier 2023')
        self.assertEqual(values[1], self.sic_management_user.person.full_name)
        self.assertEqual(values[2], _('Export') + ' - Admissions')
        self.assertEqual(values[3], '2022')
        self.assertEqual(values[4], "['2', '3']")
        self.assertEqual(values[5], str(self.admission.reference))
        self.assertEqual(values[6], self.admission.candidate.full_name)
        self.assertEqual(values[7], f"['{ChoixStatutPropositionContinue.EN_BROUILLON.value}']")
        self.assertEqual(values[8], 'ENT')
        self.assertEqual(
            values[9],
            f"['{TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.value}', '{TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.value}']",
        )
        self.assertEqual(values[10], f"['{self.admission.training.acronym}']")
        self.assertEqual(values[11], 'oui')
        self.assertEqual(values[12], 'non')
        self.assertEqual(values[13], 'oui')
