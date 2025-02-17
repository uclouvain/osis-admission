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

import ast
import datetime
from typing import List
from unittest import mock

import freezegun
import mock
from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import pgettext
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from osis_async.models import AsyncTask
from osis_async.models.enums import TaskState
from osis_export.models import Export
from osis_export.models.enums.types import ExportTypes

from admission.ddd.admission.doctorat.preparation.commands import (
    ListerDemandesQuery as ListerDemandesDoctoralesQuery,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDSS,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.dtos.liste import (
    DemandeRechercheDTO as DemandeDoctoraleRechercheDTO,
)
from admission.ddd.admission.dtos.liste import (
    DemandeRechercheDTO,
    VisualiseurAdmissionDTO,
)
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.enums.liste import TardiveModificationReorientationFiltre
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_continue.commands import (
    ListerDemandesQuery as ListerDemandesContinuesQuery,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixEdition,
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    OngletsChecklist as OngletsChecklistContinue,
)
from admission.ddd.admission.formation_continue.dtos.liste import (
    DemandeRechercheDTO as DemandeContinueRechercheDTO,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    OngletsChecklist as OngletsChecklistGenerale,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.admission_viewer import AdmissionViewerFactory
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
)
from admission.tests.factories.form_item import (
    AdmissionFormItemInstantiationFactory,
    CheckboxSelectionAdmissionFormItemFactory,
    DocumentAdmissionFormItemFactory,
    MessageAdmissionFormItemFactory,
    RadioButtonSelectionAdmissionFormItemFactory,
    TextAdmissionFormItemFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory
from admission.tests.factories.supervision import PromoterFactory
from admission.views.excel_exports import (
    SPECIFIC_QUESTION_SEPARATOR,
    SPECIFIC_QUESTION_SEPARATOR_REPLACEMENT,
    AdmissionListExcelExportView,
    ContinuingAdmissionListExcelExportView,
    DoctorateAdmissionListExcelExportView,
)
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
from reference.tests.factories.scholarship import (
    DoctorateScholarshipFactory,
    DoubleDegreeScholarshipFactory,
    ErasmusMundusScholarshipFactory,
    InternationalScholarshipFactory,
)


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

        cls.message_form_item = AdmissionFormItemInstantiationFactory(
            form_item=MessageAdmissionFormItemFactory(
                internal_label='Q1',
            ),
            academic_year=cls.admission.determined_academic_year,
        ).form_item
        cls.message_form_item_uuid = str(cls.message_form_item.uuid)

        cls.text_form_item = AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                internal_label='Q2',
            ),
            academic_year=cls.admission.determined_academic_year,
        ).form_item
        cls.text_form_item_uuid = str(cls.text_form_item.uuid)

        cls.inactive_text_form_item = AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                internal_label='Q3',
                active=False,
            ),
            academic_year=cls.admission.determined_academic_year,
        ).form_item
        cls.inactive_text_form_item_uuid = str(cls.inactive_text_form_item.uuid)

        cls.document_form_item = AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                internal_label='Q4',
            ),
            academic_year=cls.admission.determined_academic_year,
        ).form_item
        cls.document_form_item_uuid = str(cls.document_form_item.uuid)

        cls.checkbox_form_item = AdmissionFormItemInstantiationFactory(
            form_item=CheckboxSelectionAdmissionFormItemFactory(
                internal_label='Q5',
            ),
            academic_year=cls.admission.determined_academic_year,
        ).form_item
        cls.checkbox_form_item_uuid = str(cls.checkbox_form_item.uuid)

        cls.radio_button_form_item = AdmissionFormItemInstantiationFactory(
            form_item=RadioButtonSelectionAdmissionFormItemFactory(
                internal_label='Q6',
                values=[
                    {
                        'key': '1',
                        'en': f'One{SPECIFIC_QUESTION_SEPARATOR}A',
                        'fr-be': f'Un{SPECIFIC_QUESTION_SEPARATOR}A',
                    },
                    {'key': '2', 'en': 'Two', 'fr-be': 'Deux'},
                    {'key': '3', 'en': 'Three', 'fr-be': 'Trois'},
                ],
            ),
            academic_year=cls.admission.determined_academic_year,
        ).form_item
        cls.radio_button_form_item_uuid = str(cls.radio_button_form_item.uuid)

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
            est_inscription_tardive=None,
            est_modification_inscription_externe=None,
            est_reorientation_inscription_externe=None,
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
            annee_calculee=(
                cls.admission.determined_academic_year.year if cls.admission.determined_academic_year else None
            ),
            adresse_email_candidat=cls.admission.candidate.private_email,
            reponses_questions_specifiques={
                cls.text_form_item_uuid: 'Answer 1',
                cls.inactive_text_form_item_uuid: 'Answer 2',
                cls.checkbox_form_item_uuid: ['1', '2'],
                cls.radio_button_form_item_uuid: '3',
            },
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
        view.initialize_specific_questions()
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
        self.assertEqual(row_data[13], self.result.adresse_email_candidat)
        answers_to_specific_questions = row_data[14].split(SPECIFIC_QUESTION_SEPARATOR)
        self.assertCountEqual(
            answers_to_specific_questions,
            ['Q2 : Answer 1', 'Q5 : Un,Deux', 'Q6 : Trois'],
        )

        with mock.patch.object(self.result, 'date_confirmation', None):
            row_data = view.get_row_data(self.result)
            self.assertEqual(row_data[12], '')

        with mock.patch.object(self.result, 'plusieurs_demandes', True):
            row_data = view.get_row_data(self.result)
            self.assertEqual(row_data[4], 'oui')

    def test_export_content_with_invalid_specific_select_question_answer(self):
        view = AdmissionListExcelExportView()
        view.initialize_specific_questions()
        view.language = settings.LANGUAGE_CODE_FR

        with mock.patch.object(
            self.result,
            'reponses_questions_specifiques',
            {
                self.checkbox_form_item_uuid: ['1', '8'],
                self.radio_button_form_item_uuid: '8',
            },
        ):
            row_data = view.get_row_data(self.result)
            answers_to_specific_questions = row_data[14].split(SPECIFIC_QUESTION_SEPARATOR)
            self.assertCountEqual(
                answers_to_specific_questions,
                ['Q5 : Un', 'Q6 : '],
            )

    def test_export_content_with_specific_questions_answers_containing_the_separator(self):
        view = AdmissionListExcelExportView()
        view.initialize_specific_questions()
        view.language = settings.LANGUAGE_CODE_EN

        with mock.patch.object(
            self.result,
            'reponses_questions_specifiques',
            {
                self.text_form_item_uuid: f'A{SPECIFIC_QUESTION_SEPARATOR}B',
                self.radio_button_form_item_uuid: '1',
            },
        ):
            row_data = view.get_row_data(self.result)
            answers_to_specific_questions = row_data[14].split(SPECIFIC_QUESTION_SEPARATOR)
            self.assertCountEqual(
                answers_to_specific_questions,
                [
                    f'Q2 : A{SPECIFIC_QUESTION_SEPARATOR_REPLACEMENT}B',
                    f'Q6 : One{SPECIFIC_QUESTION_SEPARATOR_REPLACEMENT}A',
                ],
            )

    def test_export_configuration(self):
        candidate = PersonFactory()
        campus = CampusFactory()
        international_scholarship = InternationalScholarshipFactory(short_name='ID1')
        double_degree_scholarship = DoubleDegreeScholarshipFactory(short_name="DD1")
        erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory(short_name="EM1")
        filters = {
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
                OngletsChecklistGenerale.donnees_personnelles.name: ['A_TRAITER'],
                OngletsChecklistGenerale.frais_dossier.name: ['PAYES'],
            },
            'quarantaine': 'True',
            'tardif_modif_reorientation': TardiveModificationReorientationFiltre.INSCRIPTION_TARDIVE.name,
        }

        view = AdmissionListExcelExportView()
        workbook = Workbook()
        worksheet: Worksheet = workbook.create_sheet()

        view.customize_parameters_worksheet(
            worksheet=worksheet,
            person=self.sic_management_user.person,
            filters=str(filters),
        )

        names, values = list(worksheet.iter_cols(values_only=True))
        self.assertEqual(len(names), 20)
        self.assertEqual(len(values), 20)

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
        self.assertEqual(names[18], _('Quarantine'))
        self.assertEqual(names[19], _('Late/Modif./Reor.'))

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
                    OngletsChecklistGenerale.donnees_personnelles.value: [_('To be processed')],
                    OngletsChecklistGenerale.frais_dossier.value: [_('Payed')],
                }
            ),
        )
        self.assertEqual(values[18], 'Oui')
        self.assertEqual(values[19], 'Inscription tardive')

        filters['quarantaine'] = False

        worksheet: Worksheet = workbook.create_sheet()

        view.customize_parameters_worksheet(
            worksheet=worksheet,
            person=self.sic_management_user.person,
            filters=str(filters),
        )

        names, values = list(worksheet.iter_cols(values_only=True))
        self.assertEqual(len(names), 20)
        self.assertEqual(len(values), 20)

        self.assertEqual(values[18], 'Non')

        filters['quarantaine'] = None

        worksheet: Worksheet = workbook.create_sheet()

        view.customize_parameters_worksheet(
            worksheet=worksheet,
            person=self.sic_management_user.person,
            filters=str(filters),
        )

        names, values = list(worksheet.iter_cols(values_only=True))
        self.assertEqual(len(names), 20)
        self.assertEqual(len(values), 20)

        self.assertEqual(values[18], 'Tous')


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
            ListerDemandesContinuesQuery(numero=self.admission.reference)
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
        self.assertEqual(row_data[9], 'non')
        self.assertEqual(row_data[10], 'non')
        self.assertEqual(row_data[11], 'non')
        self.assertEqual(row_data[12], 'non')
        self.assertEqual(row_data[13], 'non')
        self.assertEqual(row_data[14], 'non')
        self.assertEqual(row_data[15], 'non')
        self.assertEqual(row_data[16], 'non')
        self.assertEqual(row_data[17], 'non')
        self.assertEqual(row_data[18], ChoixStatutPropositionContinue.CONFIRMEE.value)
        self.assertEqual(row_data[19], '')
        self.assertEqual(row_data[20], '2023/01/01, 00:00:00')
        self.assertEqual(row_data[21], '2023/01/03, 00:00:00')
        self.assertEqual(row_data[22], 'Candidat')

        # Check the export when some specific fields are empty or have a specific value
        self.admission.edition = ''
        self.admission.in_payement_order = False
        self.admission.submitted_at = None
        self.admission.save()

        results: List[DemandeContinueRechercheDTO] = message_bus_instance.invoke(
            ListerDemandesContinuesQuery(numero=self.admission.reference)
        )

        self.assertEqual(len(results), 1)

        result = results[0]

        row_data = view.get_row_data(result)

        self.assertEqual(row_data[6], '')
        self.assertEqual(row_data[8], 'non')
        self.assertEqual(row_data[20], '')

        self.admission.in_payement_order = None
        self.admission.save()

        results: List[DemandeContinueRechercheDTO] = message_bus_instance.invoke(
            ListerDemandesContinuesQuery(numero=self.admission.reference)
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
                'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
                'filtres_etats_checklist': {
                    OngletsChecklistContinue.decision.name: ['A_TRAITER', 'A_VALIDER'],
                },
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
        self.assertEqual(len(names), 16)
        self.assertEqual(len(values), 16)

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
        self.assertEqual(names[14], _('Include or exclude the checklist filters'))
        self.assertEqual(names[15], _('Checklist filters'))

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
            f"['{TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.value}', "
            f"'{TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.value}']",
        )
        self.assertEqual(values[10], f"['{self.admission.training.acronym}']")
        self.assertEqual(values[11], 'oui')
        self.assertEqual(values[12], 'non')
        self.assertEqual(values[13], 'oui')
        self.assertEqual(values[14], ModeFiltrageChecklist.INCLUSION.value)
        self.assertEqual(
            values[15],
            str(
                {
                    OngletsChecklistContinue.decision.value: [
                        _('To be processed'),
                        _('To validate IUFC'),
                    ],
                }
            ),
        )


@freezegun.freeze_time('2023-01-03')
@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class DoctorateAdmissionListExcelExportViewTestCase(QueriesAssertionsMixin, TestCase):
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
        cls.academic_years = AcademicYearFactory.produce(base_year=2023, number_past=2, number_future=2)

        # Entities
        faculty_entity = EntityFactory()
        EntityVersionFactory(
            entity=faculty_entity,
            acronym='ABCDEF',
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        )

        cls.first_entity = EntityFactory()
        EntityVersionFactory(
            entity=cls.first_entity,
            acronym='GHIJK',
            entity_type=EntityType.SCHOOL.name,
            parent=faculty_entity,
        )

        cls.candidate = PersonFactory(
            first_name="John",
            last_name="Doe",
            email='john.doe@example.be',
        )
        cls.student = StudentFactory(
            person=cls.candidate,
            registration_id='01234567',
        )

        cls.default_params = {
            'annee_academique': 2022,
            'taille_page': 10,
            'demandeur': str(cls.sic_management_user.person.uuid),
        }

        # Targeted url
        cls.url = reverse('admission:excel-exports:doctorate-admissions-list')
        cls.list_url = reverse('admission:doctorate:cdd:list')

    def test_export_user_without_person(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_export_candidate_user(self):
        self.client.force_login(user=self.candidate.user)

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
            'admission.views.excel_exports.DoctorateAdmissionListExcelExportView',
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
        view = DoctorateAdmissionListExcelExportView()
        header = view.get_header()

        admission = DoctorateAdmissionFactory(
            candidate=self.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            training__management_entity=self.first_entity,
            training__acronym="ZEBU0",
            training__education_group_type__name=TrainingType.PHD.name,
            submitted_at=datetime.datetime(2023, 1, 1),
            training__academic_year=self.academic_years[1],
            determined_academic_year=self.academic_years[2],
            modified_at=datetime.datetime(2023, 1, 3),
            last_update_author=self.candidate,
            cotutelle=None,
            type=ChoixTypeAdmission.ADMISSION.name,
            checklist={
                'initial': {},
                'current': {
                    'decision_sic': {'statut': 'INITIAL_CANDIDAT'},
                    'decision_cdd': {'statut': 'GEST_EN_COURS'},
                },
            },
        )

        results: List[DemandeDoctoraleRechercheDTO] = message_bus_instance.invoke(
            ListerDemandesDoctoralesQuery(numero=admission.reference)
        )

        self.assertEqual(len(results), 1)

        result = results[0]

        row_data = view.get_row_data(result)

        self.assertEqual(len(header), len(row_data))

        self.assertEqual(row_data[0], result.numero_demande)
        self.assertEqual(row_data[1], f'{result.nom_candidat}, {result.prenom_candidat}')
        self.assertEqual(row_data[2], result.nom_pays_nationalite_candidat)
        self.assertEqual(row_data[3], result.code_bourse)
        self.assertEqual(row_data[4], f'{result.sigle_formation} - {result.intitule_formation}')
        self.assertEqual(row_data[5], ChoixStatutPropositionDoctorale.CONFIRMEE.value)
        self.assertEqual(row_data[6], _('Taken in charge'))
        self.assertEqual(row_data[7], _('To be processed'))
        self.assertEqual(row_data[8], '2023/01/01')
        self.assertEqual(row_data[9], '2023/01/03')
        self.assertEqual(
            row_data[10],
            f'{result.nom_auteur_derniere_modification}, {result.prenom_auteur_derniere_modification[:1]}',
        )
        self.assertEqual(row_data[11], 'non')
        self.assertEqual(row_data[12], '')

        # Check specific values
        admission.submitted_at = None
        admission.type = ChoixTypeAdmission.PRE_ADMISSION.name
        admission.cotutelle = True
        admission.save(update_fields=['submitted_at', 'type', 'cotutelle'])

        results: List[DemandeDoctoraleRechercheDTO] = message_bus_instance.invoke(
            ListerDemandesDoctoralesQuery(numero=admission.reference)
        )

        self.assertEqual(len(results), 1)

        result = results[0]

        row_data = view.get_row_data(result)

        self.assertEqual(len(header), len(row_data))

        self.assertEqual(row_data[8], '')
        self.assertEqual(row_data[11], 'oui')
        self.assertEqual(row_data[12], 'oui')

        admission.cotutelle = False
        admission.save(update_fields=['cotutelle'])

        results: List[DemandeDoctoraleRechercheDTO] = message_bus_instance.invoke(
            ListerDemandesDoctoralesQuery(numero=admission.reference)
        )

        self.assertEqual(len(results), 1)

        result = results[0]

        row_data = view.get_row_data(result)

        self.assertEqual(len(header), len(row_data))

        self.assertEqual(row_data[12], 'non')

    def test_export_configuration(self):
        country = CountryFactory()
        promoter = PromoterFactory()
        scholarship = DoctorateScholarshipFactory()
        admission = DoctorateAdmissionFactory(
            candidate=self.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            training__management_entity=self.first_entity,
            training__acronym="ZEBU0",
            training__education_group_type__name=TrainingType.PHD.name,
            submitted_at=datetime.datetime(2023, 1, 1),
            training__academic_year=self.academic_years[1],
            determined_academic_year=self.academic_years[2],
            modified_at=datetime.datetime(2023, 1, 3),
            last_update_author=self.candidate,
            cotutelle=None,
            type=ChoixTypeAdmission.ADMISSION.name,
        )

        filters = str(
            {
                'annee_academique': 2022,
                'numero': admission.reference,
                'matricule_candidat': admission.candidate.global_id,
                'nationalite': country.iso_code,
                'etats': [
                    ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
                    ChoixStatutPropositionDoctorale.CONFIRMEE.name,
                ],
                'type': ChoixTypeAdmission.ADMISSION.name,
                'cdds': 'GHIJK',
                'commission_proximite': ChoixCommissionProximiteCDSS.BCM.name,
                'sigles_formations': ['ZEBU0'],
                'matricule_promoteur': promoter.person.global_id,
                'type_financement': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
                'bourse_recherche': str(scholarship.uuid),
                'cotutelle': True,
                'fnrs_fria_fresh': True,
                'date_soumission_debut': '2020-01-01',
                'date_soumission_fin': '2020-01-02',
                'mode_filtres_etats_checklist': ModeFiltrageChecklist.INCLUSION.name,
                'filtres_etats_checklist': {},
                'demandeur': str(self.sic_management_user.person.uuid),
            }
        )

        view = DoctorateAdmissionListExcelExportView()
        workbook = Workbook()
        worksheet: Worksheet = workbook.create_sheet()

        view.customize_parameters_worksheet(
            worksheet=worksheet,
            person=self.sic_management_user.person,
            filters=filters,
        )

        names, values = list(worksheet.iter_cols(values_only=True))

        self.assertEqual(len(names), 21)
        self.assertEqual(len(values), 21)

        # Check the names of the parameters
        self.assertEqual(names[0], _('Creation date'))
        self.assertEqual(names[1], pgettext('masculine', 'Created by'))
        self.assertEqual(names[2], _('Description'))
        self.assertEqual(names[3], _('Year'))
        self.assertEqual(names[4], _('Application numero'))
        self.assertEqual(names[5], _('Last name / First name / Email / NOMA'))
        self.assertEqual(names[6], _('Nationality'))
        self.assertEqual(names[7], _('Application status'))
        self.assertEqual(names[8], pgettext('doctorate-filter', 'Admission type'))
        self.assertEqual(names[9], _('Doctoral commissions'))
        self.assertEqual(names[10], _('Proximity commission'))
        self.assertEqual(names[11], pgettext('admission', 'Courses'))
        self.assertEqual(names[12], pgettext('gender', 'Supervisor'))
        self.assertEqual(names[13], _('Funding type'))
        self.assertEqual(names[14], _('Research scholarship'))
        self.assertEqual(names[15], _('Cotutelle'))
        self.assertEqual(names[16], _('FNRS, FRIA, FRESH'))
        self.assertEqual(names[17], _('Submitted from'))
        self.assertEqual(names[18], _('Submitted until'))
        self.assertEqual(names[19], _('Include or exclude the checklist filters'))
        self.assertEqual(names[20], _('Checklist filters'))

        # Check the values of the parameters
        self.assertEqual(values[0], '3 Janvier 2023')
        self.assertEqual(values[1], self.sic_management_user.person.full_name)
        self.assertEqual(values[2], _('Export') + ' - Admissions')
        self.assertEqual(values[3], '2022')
        self.assertEqual(values[4], str(admission.reference))
        self.assertEqual(values[5], admission.candidate.full_name)
        self.assertEqual(values[6], country.name)
        self.assertEqual(
            values[7],
            f"['{ChoixStatutPropositionDoctorale.EN_BROUILLON.value}', "
            f"'{ChoixStatutPropositionDoctorale.CONFIRMEE.value}']",
        )
        self.assertEqual(values[8], ChoixTypeAdmission.ADMISSION.value)
        self.assertEqual(values[9], 'GHIJK')
        self.assertEqual(values[10], ChoixCommissionProximiteCDSS.BCM.value)
        self.assertEqual(values[11], "['ZEBU0']")
        self.assertEqual(values[12], promoter.person.full_name)
        self.assertEqual(values[13], ChoixTypeFinancement.SEARCH_SCHOLARSHIP.value)
        self.assertEqual(values[14], scholarship.short_name)
        self.assertEqual(values[15], 'oui')
        self.assertEqual(values[16], 'oui')
        self.assertEqual(values[17], '2020-01-01')
        self.assertEqual(values[18], '2020-01-02')
        self.assertEqual(values[19], ModeFiltrageChecklist.INCLUSION.value)
        self.assertEqual(values[20], '{}')

        filters = str(
            {
                'annee_academique': 2022,
                'numero': '',
                'matricule_candidat': '',
                'nationalite': '',
                'etats': [],
                'type': '',
                'cdds': '',
                'commission_proximite': '',
                'sigles_formations': [],
                'matricule_promoteur': '',
                'type_financement': '',
                'bourse_recherche': '',
                'cotutelle': None,
                'fnrs_fria_fresh': None,
                'date_soumission_debut': '',
                'date_soumission_fin': '',
                'mode_filtres_etats_checklist': '',
                'filtres_etats_checklist': {},
                'demandeur': str(self.sic_management_user.person.uuid),
            }
        )

        view = DoctorateAdmissionListExcelExportView()
        workbook = Workbook()
        worksheet: Worksheet = workbook.create_sheet()

        view.customize_parameters_worksheet(
            worksheet=worksheet,
            person=self.sic_management_user.person,
            filters=filters,
        )

        names, values = list(worksheet.iter_cols(values_only=True))

        self.assertEqual(len(names), 21)
        self.assertEqual(len(values), 21)

        # Check the values of the parameters
        self.assertEqual(values[0], '3 Janvier 2023')
        self.assertEqual(values[1], self.sic_management_user.person.full_name)
        self.assertEqual(values[2], _('Export') + ' - Admissions')
        self.assertEqual(values[3], '2022')
        self.assertEqual(values[4], '')
        self.assertEqual(values[5], '')
        self.assertEqual(values[6], '')
        self.assertEqual(values[7], '[]')
        self.assertEqual(values[8], '')
        self.assertEqual(values[9], '')
        self.assertEqual(values[10], '')
        self.assertEqual(values[11], '[]')
        self.assertEqual(values[12], '')
        self.assertEqual(values[13], '')
        self.assertEqual(values[14], '')
        self.assertEqual(values[15], '')
        self.assertEqual(values[16], '')
        self.assertEqual(values[17], '')
        self.assertEqual(values[18], '')
        self.assertEqual(values[19], '')
        self.assertEqual(values[20], '{}')
