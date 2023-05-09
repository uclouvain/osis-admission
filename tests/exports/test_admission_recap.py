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
from io import BytesIO
from typing import Dict, List
from unittest.mock import MagicMock

import attr
import freezegun
import mock
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.translation import gettext as _, ngettext
from rest_framework import status

from admission.calendar.admission_calendar import (
    AdmissionPoolExternalEnrollmentChangeCalendar,
    AdmissionPoolExternalReorientationCalendar,
)
from admission.contrib.models import AdmissionTask
from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutSignatureGroupeDeSupervision,
    ChoixTypeFinancement,
    ChoixEtatSignature,
)
from admission.ddd.admission.doctorat.preparation.dtos import (
    AnneeExperienceAcademiqueDTO,
    ConnaissanceLangueDTO,
    CotutelleDTO,
    CurriculumDTO,
    DetailSignatureMembreCADTO,
    DetailSignaturePromoteurDTO,
    DoctoratDTO,
    ExperienceAcademiqueDTO,
    GroupeDeSupervisionDTO,
    MembreCADTO,
    PromoteurDTO,
    PropositionDTO as PropositionFormationDoctoraleDTO,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceNonAcademiqueDTO
from admission.ddd.admission.dtos import AdressePersonnelleDTO, CoordonneesDTO, EtudesSecondairesDTO, IdentificationDTO
from admission.ddd.admission.dtos.etudes_secondaires import (
    AlternativeSecondairesDTO,
    DiplomeBelgeEtudesSecondairesDTO,
    DiplomeEtrangerEtudesSecondairesDTO,
)
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums import (
    ChoixAffiliationSport,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixTypeCompteBancaire,
    LienParente,
    Onglets,
    TypeItemFormulaire,
    TypeSituationAssimilation,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixInscriptionATitre,
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_continue.dtos import PropositionDTO as PropositionFormationContinueDTO
from admission.ddd.admission.formation_generale.dtos import (
    ComptabiliteDTO,
    PropositionDTO as PropositionFormationGeneraleDTO,
)
from admission.exports.admission_recap.attachments import (
    Attachment,
)
from admission.constants import PDF_MIME_TYPE, JPEG_MIME_TYPE, PNG_MIME_TYPE
from admission.exports.admission_recap.constants import ACCOUNTING_LABEL, CURRICULUM_ACTIVITY_LABEL
from admission.exports.admission_recap.section import (
    get_accounting_section,
    get_cotutelle_section,
    get_curriculum_section,
    get_educational_experience_section,
    get_identification_section,
    get_languages_section,
    get_non_educational_experience_section,
    get_research_project_section,
    get_secondary_studies_section,
    get_specific_questions_section,
    get_supervision_section,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import UnfrozenDTO
from admission.tests import QueriesAssertionsMixin, TestCase
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.form_item import (
    AdmissionFormItemInstantiationFactory,
    DocumentAdmissionFormItemFactory,
    TextAdmissionFormItemFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.person import CompletePersonForIUFCFactory
from admission.tests.factories.roles import ProgramManagerRoleFactory
from base.models.enums.civil_state import CivilState
from base.models.enums.community import CommunityEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from base.models.enums.teaching_type import TeachingTypeEnum
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from osis_async.models import AsyncTask
from osis_profile.models.enums.curriculum import (
    ActivitySector,
    ActivityType,
    EvaluationSystem,
    Grade,
    Result,
    TranscriptType,
)
from osis_profile.models.enums.education import (
    BelgianCommunitiesOfEducation,
    DiplomaResults,
    EducationalType,
    Equivalence,
    ForeignDiplomaTypes,
)
from reference.tests.factories.country import CountryFactory


@attr.dataclass
class _IdentificationDTO(UnfrozenDTO, IdentificationDTO):
    pass


@attr.dataclass
class _EtudesSecondairesDTO(UnfrozenDTO, EtudesSecondairesDTO):
    pass


@attr.dataclass
class _ResumePropositionDTO(UnfrozenDTO, ResumePropositionDTO):
    pass


@attr.dataclass
class _CoordonneesDTO(UnfrozenDTO, CoordonneesDTO):
    pass


@attr.dataclass
class _AdressePersonnelleDTO(UnfrozenDTO, AdressePersonnelleDTO):
    pass


@attr.dataclass
class _CurriculumDTO(UnfrozenDTO, CurriculumDTO):
    pass


@attr.dataclass
class _EtudesSecondairesDTO(UnfrozenDTO, EtudesSecondairesDTO):
    pass


@attr.dataclass
class _PropositionFormationContinueDTO(UnfrozenDTO, PropositionFormationContinueDTO):
    pass


@attr.dataclass
class _PropositionFormationGeneraleDTO(UnfrozenDTO, PropositionFormationGeneraleDTO):
    pass


@attr.dataclass
class _PropositionFormationDoctoraleDTO(UnfrozenDTO, PropositionFormationDoctoraleDTO):
    pass


@attr.dataclass
class _FormationDTO(UnfrozenDTO, FormationDTO):
    pass


@attr.dataclass
class _DiplomeEtrangerEtudesSecondairesDTO(UnfrozenDTO, DiplomeEtrangerEtudesSecondairesDTO):
    pass


@attr.dataclass
class _ExperienceAcademiqueDTO(UnfrozenDTO, ExperienceAcademiqueDTO):
    pass


@attr.dataclass
class _ExperienceNonAcademiqueDTO(UnfrozenDTO, ExperienceNonAcademiqueDTO):
    pass


@attr.dataclass
class _AnneeExperienceAcademiqueDTO(UnfrozenDTO, AnneeExperienceAcademiqueDTO):
    pass


@attr.dataclass
class _ComptabiliteDTO(UnfrozenDTO, ComptabiliteDTO):
    pass


@attr.dataclass
class _CotutelleDTO(UnfrozenDTO, CotutelleDTO):
    pass


@attr.dataclass
class _GroupeDeSupervisionDTO(UnfrozenDTO, GroupeDeSupervisionDTO):
    pass


@freezegun.freeze_time('2023-01-01')
class AdmissionRecapTestCase(TestCase, QueriesAssertionsMixin):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.specific_questions = {
            tab.name: [
                AdmissionFormItemInstantiationFactory(
                    form_item=TextAdmissionFormItemFactory(),
                    academic_year=cls.academic_year,
                    tab=tab.name,
                ),
                AdmissionFormItemInstantiationFactory(
                    form_item=DocumentAdmissionFormItemFactory(),
                    academic_year=cls.academic_year,
                    tab=tab.name,
                ),
            ]
            for tab in Onglets
        }

    def setUp(self):
        # Mock weasyprint
        patcher = mock.patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

        self.bytes_io_default_content = BytesIO(b'some content')

        # Mock osis-document
        patcher = mock.patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)

        patcher = mock.patch('admission.exports.admission_recap.admission_recap.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = mock.patch('admission.exports.admission_recap.admission_recap.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {
            token: {
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
            }
            for token in tokens
        }
        self.addCleanup(patcher.stop)

        patcher = mock.patch('admission.exports.admission_recap.attachments.get_raw_content_remotely')
        self.get_raw_content_mock = patcher.start()
        self.get_raw_content_mock.return_value = b'some content'
        self.addCleanup(patcher.stop)

        patcher = mock.patch('admission.exports.admission_recap.admission_recap.save_raw_content_remotely')
        self.save_raw_content_mock = patcher.start()
        self.save_raw_content_mock.return_value = 'pdf-token'
        self.addCleanup(patcher.stop)

        # Mock img2pdf
        patcher = mock.patch('admission.exports.admission_recap.attachments.img2pdf.convert')
        self.convert_img_mock = patcher.start()
        self.convert_img_mock.return_value = b'some content'
        self.addCleanup(patcher.stop)

        # Mock pikepdf
        patcher = mock.patch('admission.exports.admission_recap.admission_recap.Pdf')
        patched = patcher.start()
        patched.new.return_value = mock.MagicMock(pdf_version=1)
        self.outline_root = patched.new.return_value.open_outline.return_value.__enter__.return_value.root = MagicMock()
        patched.open.return_value.__enter__.return_value = mock.Mock(pdf_version=1, pages=[None])
        self.addCleanup(patcher.stop)

    def test_get_raw_with_pdf_attachment(self):
        pdf_attachment = Attachment(label='PDF', uuids=[''])
        pdf_attachment.get_raw(
            token='token',
            metadata={
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
            },
            default_content=self.bytes_io_default_content,
        )
        self.get_raw_content_mock.assert_called_once_with('token')

    def test_convert_and_get_raw_with_jpeg_attachment(self):
        image_attachment = Attachment(label='JPEG', uuids=[''])
        image_attachment.get_raw(
            token='token',
            metadata={
                'name': 'myfile',
                'mimetype': JPEG_MIME_TYPE,
            },
            default_content=self.bytes_io_default_content,
        )
        self.get_raw_content_mock.assert_called_once_with('token')
        self.convert_img_mock.assert_called_once_with(self.get_raw_content_mock.return_value)

    def test_convert_and_get_raw_with_png_attachment(self):
        image_attachment = Attachment(label='PNG', uuids=[''])
        image_attachment.get_raw(
            token='token',
            metadata={
                'name': 'myfile',
                'mimetype': PNG_MIME_TYPE,
            },
            default_content=self.bytes_io_default_content,
        )
        self.get_raw_content_mock.assert_called_once_with('token')
        self.convert_img_mock.assert_called_once_with(self.get_raw_content_mock.return_value)

    def test_get_default_content_if_mimetype_is_not_supported(self):
        unknown_attachment = Attachment(label='Unknown', uuids=[''])
        raw = unknown_attachment.get_raw(
            token='token',
            metadata={
                'name': 'myfile',
                'mimetype': 'application/octet-stream',
            },
            default_content=self.bytes_io_default_content,
        )
        self.get_raw_content_mock.assert_not_called()
        self.assertEqual(raw, self.bytes_io_default_content)

    def test_get_default_content_if_no_retrieved_content(self):
        self.get_raw_content_mock.return_value = None
        pdf_attachment = Attachment(label='PDF', uuids=[''])
        raw = pdf_attachment.get_raw(
            token='token',
            metadata={
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
            },
            default_content=self.bytes_io_default_content,
        )
        self.get_raw_content_mock.assert_called_once_with('token')
        self.assertEqual(raw, self.bytes_io_default_content)

    def test_generation_with_continuing_education(self):
        candidate = CompletePersonForIUFCFactory(country_of_citizenship=CountryFactory(european_union=False))
        admission = ContinuingEducationAdmissionFactory(
            candidate=candidate,
            residence_permit=['file-uuid'],
        )

        from admission.exports.admission_recap.admission_recap import admission_pdf_recap

        pdf_token = admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        call_args = self.outline_root.append.call_args_list

        call_args_by_tab = {
            tab: call_args[index][0][0]
            for index, tab in enumerate(
                [
                    'identification',
                    'coordinates',
                    'training_choice',
                    'education',
                    'curriculum',
                    'curriculum_academic_experience',
                    'curriculum_non_academic_experience',
                    'specific_question',
                    'confirmation',
                ]
            )
        }

        # Check that all pdf sections have been added
        self.assertEqual(call_args_by_tab['identification'].title, 'Identification')
        self.assertEqual(call_args_by_tab['coordinates'].title, 'Coordonnées')
        self.assertEqual(call_args_by_tab['training_choice'].title, 'Choix de formation')
        self.assertEqual(call_args_by_tab['education'].title, 'Études secondaires')
        self.assertEqual(call_args_by_tab['curriculum'].title, 'Curriculum')
        self.assertEqual(call_args_by_tab['curriculum_academic_experience'].title, 'Curriculum > Computer science')
        self.assertEqual(call_args_by_tab['curriculum_non_academic_experience'].title, 'Curriculum > Travail')
        self.assertEqual(call_args_by_tab['specific_question'].title, 'Questions spécifiques')
        self.assertEqual(len(call_args_by_tab['specific_question'].children), 1)
        self.assertEqual(
            call_args_by_tab['specific_question'].children[0].title,
            'Copie du titre de séjour qui couvre la totalité de la formation, épreuve d’évaluation comprise (sauf '
            'pour les formations organisées en ligne)',
        )
        self.assertEqual(call_args_by_tab['confirmation'].title, 'Finalisation')

        self.assertEqual(pdf_token, 'pdf-token')

    def test_generation_with_general_education(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.BACHELOR.name)

        from admission.exports.admission_recap.admission_recap import admission_pdf_recap

        admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        call_args = self.outline_root.append.call_args_list

        call_args_by_tab = {
            tab: call_args[index][0][0]
            for index, tab in enumerate(
                [
                    'identification',
                    'coordinates',
                    'training_choice',
                    'education',
                    'curriculum',
                    'specific_question',
                    'accounting',
                    'confirmation',
                ]
            )
        }

        # Check that all pdf sections have been added
        self.assertEqual(call_args_by_tab['identification'].title, 'Identification')
        self.assertEqual(call_args_by_tab['coordinates'].title, 'Coordonnées')
        self.assertEqual(call_args_by_tab['training_choice'].title, 'Choix de formation')
        self.assertEqual(call_args_by_tab['education'].title, 'Études secondaires')
        self.assertEqual(call_args_by_tab['curriculum'].title, 'Curriculum')
        self.assertEqual(call_args_by_tab['specific_question'].title, 'Questions spécifiques')
        self.assertEqual(call_args_by_tab['accounting'].title, 'Comptabilité')
        self.assertEqual(call_args_by_tab['confirmation'].title, 'Finalisation')

    def test_generation_with_doctorate_education(self):
        admission = DoctorateAdmissionFactory()

        from admission.exports.admission_recap.admission_recap import admission_pdf_recap

        admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        call_args = self.outline_root.append.call_args_list

        call_args_by_tab = {
            tab: call_args[index][0][0]
            for index, tab in enumerate(
                [
                    'identification',
                    'coordinates',
                    'training_choice',
                    'languages',
                    'curriculum',
                    'accounting',
                    'project',
                    'cotutelle',
                    'supervision',
                    'confirmation',
                ]
            )
        }

        # Check that all pdf sections have been added
        self.assertEqual(call_args_by_tab['identification'].title, 'Identification')
        self.assertEqual(call_args_by_tab['coordinates'].title, 'Coordonnées')
        self.assertEqual(call_args_by_tab['training_choice'].title, 'Choix de formation')
        self.assertEqual(call_args_by_tab['languages'].title, 'Connaissance des langues')
        self.assertEqual(call_args_by_tab['curriculum'].title, 'Curriculum')
        self.assertEqual(call_args_by_tab['accounting'].title, 'Comptabilité')
        self.assertEqual(call_args_by_tab['project'].title, 'Projet de recherche doctoral')
        self.assertEqual(call_args_by_tab['cotutelle'].title, 'Cotutelle')
        self.assertEqual(call_args_by_tab['supervision'].title, 'Groupe de supervision')
        self.assertEqual(call_args_by_tab['confirmation'].title, 'Finalisation')

    def test_async_generation_with_continuing_education(self):
        admission = ContinuingEducationAdmissionFactory()
        async_task = AsyncTask.objects.create(
            person=admission.candidate,
        )
        AdmissionTask.objects.create(
            type=AdmissionTask.TaskType.CONTINUING_RECAP.name,
            task=async_task,
            admission=admission,
        )

        self.assertEqual(len(admission.pdf_recap), 0)

        with self.assertNumQueriesLessThan(11):
            from admission.exports.admission_recap.admission_async_recap import (
                continuing_education_admission_pdf_recap_from_task,
            )

            continuing_education_admission_pdf_recap_from_task(str(async_task.uuid))

        admission.refresh_from_db()
        self.assertEqual(len(admission.pdf_recap), 1)

    def test_async_generation_with_general_education(self):
        admission = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.MASTER_MC.name,
        )
        async_task = AsyncTask.objects.create(
            person=admission.candidate,
        )
        AdmissionTask.objects.create(
            type=AdmissionTask.TaskType.GENERAL_RECAP.name,
            task=async_task,
            admission=admission,
        )

        self.assertEqual(len(admission.pdf_recap), 0)

        with self.assertNumQueriesLessThan(12):
            from admission.exports.admission_recap.admission_async_recap import (
                general_education_admission_pdf_recap_from_task,
            )

            general_education_admission_pdf_recap_from_task(str(async_task.uuid))

        admission.refresh_from_db()
        self.assertEqual(len(admission.pdf_recap), 1)

    def test_async_generation_with_doctorate_education(self):
        admission = DoctorateAdmissionFactory()
        async_task = AsyncTask.objects.create(
            person=admission.candidate,
        )
        AdmissionTask.objects.create(
            type=AdmissionTask.TaskType.DOCTORATE_RECAP.name,
            task=async_task,
            admission=admission,
        )

        with self.assertNumQueriesLessThan(16):
            self.assertEqual(len(admission.pdf_recap), 0)

        from admission.exports.admission_recap.admission_async_recap import (
            doctorate_education_admission_pdf_recap_from_task,
        )

        doctorate_education_admission_pdf_recap_from_task(str(async_task.uuid))

        admission.refresh_from_db()
        self.assertEqual(len(admission.pdf_recap), 1)

    @override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
    def test_pdf_recap_export_doctorate(self):
        admission = DoctorateAdmissionFactory(admitted=True)
        url = resolve_url("admission:doctorate:pdf-recap", uuid=admission.uuid)

        manager = ProgramManagerRoleFactory(education_group=admission.training.education_group).person
        other_program_manager = ProgramManagerRoleFactory().person

        self.client.force_login(user=other_program_manager.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(user=manager.user)
        response = self.client.get(url)
        self.assertRedirects(response, 'http://dummyurl/file/pdf-token', fetch_redirect_response=False)


@freezegun.freeze_time('2023-01-01')
class SectionsAttachmentsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        AcademicCalendarFactory(
            reference=AdmissionPoolExternalReorientationCalendar.event_reference,
            data_year=cls.academic_year,
            start_date=datetime.date(2022, 12, 1),
            end_date=datetime.date(2023, 9, 30),
        )
        AcademicCalendarFactory(
            reference=AdmissionPoolExternalEnrollmentChangeCalendar.event_reference,
            data_year=cls.academic_year,
            start_date=datetime.date(2022, 12, 1),
            end_date=datetime.date(2023, 9, 30),
        )

        cls.specific_questions: Dict[str, List[AdmissionFormItemInstantiationFactory]] = {
            tab.name: [
                AdmissionFormItemInstantiationFactory(
                    form_item=TextAdmissionFormItemFactory(),
                    academic_year=cls.academic_year,
                    tab=tab.name,
                ),
                AdmissionFormItemInstantiationFactory(
                    form_item=DocumentAdmissionFormItemFactory(),
                    academic_year=cls.academic_year,
                    tab=tab.name,
                ),
            ]
            for tab in Onglets
        }
        cls.empty_questions = {tab.name: [] for tab in Onglets}
        cls.answers_to_specific_questions = {
            str(question.form_item.uuid): f'answer-{index}'
            if question.form_item.type == TypeItemFormulaire.TEXTE.name
            else [f'uuid-file-{index}']
            for index, tab_questions in enumerate(cls.specific_questions.values())
            for question in tab_questions
        }

        identification_dto = _IdentificationDTO(
            matricule='MAT1',
            nom='Doe',
            prenom='John',
            prenom_d_usage='Jim',
            autres_prenoms='Jack',
            date_naissance=datetime.date(1990, 1, 1),
            annee_naissance=None,
            pays_nationalite='BE',
            pays_nationalite_europeen=True,
            nom_pays_nationalite='Belgique',
            sexe='M',
            genre='M',
            photo_identite=['uuid-photo-identite'],
            pays_naissance='BE',
            nom_pays_naissance='Belgique',
            lieu_naissance='Bruxelles',
            etat_civil=CivilState.LEGAL_COHABITANT.name,
            pays_residence='BE',
            carte_identite=['uuid-carte-identite'],
            passeport=['uuid-passeport'],
            numero_registre_national_belge='0123456',
            numero_carte_identite='0123456',
            numero_passeport='0123456',
            langue_contact='FR-BE',
            nom_langue_contact='Français',
            email='johndoe@example.com',
            annee_derniere_inscription_ucl=2020,
            noma_derniere_inscription_ucl='0123456789',
        )
        coordinates_dto = _CoordonneesDTO(
            domicile_legal=_AdressePersonnelleDTO(
                rue='Rue du pin',
                code_postal='1048',
                ville='Louvain-La-Neuve',
                pays='BE',
                nom_pays='Belgique',
                lieu_dit='Depice',
                numero_rue='1',
                boite_postale='BB8',
            ),
            adresse_correspondance=None,
            numero_mobile='0123456789',
            adresse_email_privee='johndoe@example.com',
        )
        curriculum_dto = _CurriculumDTO(
            experiences_non_academiques=[
                _ExperienceNonAcademiqueDTO(
                    uuid='uuid-1',
                    employeur='UCL',
                    date_debut=datetime.date(2023, 1, 1),
                    date_fin=datetime.date(2023, 3, 31),
                    type=ActivityType.WORK.name,
                    certificat=['uuid-certificat'],
                    fonction='Librarian',
                    secteur=ActivitySector.PUBLIC.name,
                    autre_activite='Other name',
                )
            ],
            experiences_academiques=[
                _ExperienceAcademiqueDTO(
                    uuid='uuid-1',
                    pays=FR_ISO_CODE,
                    nom_pays='France',
                    nom_institut='Institut 1',
                    adresse_institut='Paris',
                    code_institut='I1',
                    communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                    regime_linguistique=FR_ISO_CODE,
                    nom_regime_linguistique='Français',
                    type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
                    releve_notes=['uuid-releve-notes'],
                    traduction_releve_notes=['uuid-traduction-releve-notes'],
                    annees=[
                        _AnneeExperienceAcademiqueDTO(
                            annee=2023,
                            resultat=Result.SUCCESS.name,
                            releve_notes=['uuid-releve-notes-1'],
                            traduction_releve_notes=['uuid-traduction-releve-notes'],
                            credits_inscrits=220,
                            credits_acquis=220,
                        )
                    ],
                    a_obtenu_diplome=True,
                    diplome=['uuid-diplome'],
                    traduction_diplome=['uuid-traduction-diplome'],
                    rang_diplome='10',
                    date_prevue_delivrance_diplome=datetime.date(2023, 1, 1),
                    titre_memoire='Title',
                    note_memoire='15',
                    resume_memoire=['uuid-resume-memoire'],
                    grade_obtenu=Grade.GREAT_DISTINCTION.name,
                    systeme_evaluation=EvaluationSystem.ECTS_CREDITS.name,
                    nom_formation='Computer science',
                    type_enseignement=TeachingTypeEnum.FULL_TIME.name,
                )
            ],
            annee_derniere_inscription_ucl=2020,
            annee_diplome_etudes_secondaires=2015,
            annee_minimum_a_remplir=2020,
        )
        continuing_secondary_studies_dto = _EtudesSecondairesDTO(
            diplome_belge=None,
            diplome_etranger=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2015,
            valorisees=False,
        )
        bachelor_secondary_studies_dto = _EtudesSecondairesDTO(
            diplome_belge=DiplomeBelgeEtudesSecondairesDTO(
                resultat=DiplomaResults.GT_75_RESULT.name,
                certificat_inscription=['uuid-certificat-inscription'],
                diplome=['uuid-diplome'],
                type_enseignement=EducationalType.PROFESSIONAL_EDUCATION.name,
                autre_type_enseignement='Other type',
                nom_institut='UCL',
                adresse_institut='Louvain-La-Neuve',
                grille_horaire=None,
                communaute=BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
            ),
            diplome_etranger=_DiplomeEtrangerEtudesSecondairesDTO(
                resultat=DiplomaResults.GT_75_RESULT.name,
                type_diplome=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                regime_linguistique=FR_ISO_CODE,
                pays_regime_linguistique='France',
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                pays_nom='France',
                releve_notes=['uuid-releve-notes'],
                traduction_releve_notes=['uuid-traduction-releve-notes'],
                diplome=['uuid-diplome'],
                traduction_diplome=['uuid-traduction-diplome'],
                certificat_inscription=['uuid-certificat-inscription'],
                traduction_certificat_inscription=['uuid-traduction-certificat-inscription'],
                equivalence=Equivalence.YES.name,
                decision_final_equivalence_ue=['uuid-decision-final-equivalence-ue'],
                decision_final_equivalence_hors_ue=['uuid-decision-final-equivalence-hors-ue'],
                preuve_decision_equivalence=['uuid-preuve-decision-equivalence'],
            ),
            alternative_secondaires=AlternativeSecondairesDTO(
                examen_admission_premier_cycle=['uuid-examen-admission-premier-cycle'],
            ),
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2015,
            valorisees=False,
        )

        accounting_dto = _ComptabiliteDTO(
            demande_allocation_d_etudes_communaute_francaise_belgique=False,
            enfant_personnel=False,
            type_situation_assimilation=TypeSituationAssimilation.AUCUNE_ASSIMILATION.name,
            affiliation_sport=ChoixAffiliationSport.NON.name,
            etudiant_solidaire=False,
            type_numero_compte=ChoixTypeCompteBancaire.NON.name,
            sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
            sous_type_situation_assimilation_2=ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name,
            sous_type_situation_assimilation_3=(ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name),
            relation_parente=LienParente.MERE.name,
            sous_type_situation_assimilation_5=ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
            sous_type_situation_assimilation_6=ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
            attestation_absence_dette_etablissement=['uuid-attestation_absence_dette_etablissement'],
            attestation_enfant_personnel=['uuid-attestation_enfant_personnel'],
            carte_resident_longue_duree=['uuid-carte_resident_longue_duree'],
            carte_cire_sejour_illimite_etranger=['uuid-carte_cire_sejour_illimite_etranger'],
            carte_sejour_membre_ue=['uuid-carte_sejour_membre_ue'],
            carte_sejour_permanent_membre_ue=['uuid-carte_sejour_permanent_membre_ue'],
            carte_a_b_refugie=['uuid-carte_a_b_refugie'],
            annexe_25_26_refugies_apatrides=['uuid-annexe_25_26_refugies_apatrides'],
            attestation_immatriculation=['uuid-attestation_immatriculation'],
            carte_a_b=['uuid-carte_a_b'],
            decision_protection_subsidiaire=['uuid-decision_protection_subsidiaire'],
            decision_protection_temporaire=['uuid-decision_protection_temporaire'],
            titre_sejour_3_mois_professionel=['uuid-titre_sejour_3_mois_professionel'],
            fiches_remuneration=['uuid-fiches_remuneration'],
            titre_sejour_3_mois_remplacement=['uuid-titre_sejour_3_mois_remplacement'],
            preuve_allocations_chomage_pension_indemnite=['uuid-preuve_allocations_chomage_pension_indemnite'],
            attestation_cpas=['uuid-attestation_cpas'],
            composition_menage_acte_naissance=['uuid-composition_menage_acte_naissance'],
            acte_tutelle=['uuid-acte_tutelle'],
            composition_menage_acte_mariage=['uuid-composition_menage_acte_mariage'],
            attestation_cohabitation_legale=['uuid-attestation_cohabitation_legale'],
            carte_identite_parent=['uuid-carte_identite_parent'],
            titre_sejour_longue_duree_parent=['uuid-titre_sejour_longue_duree_parent'],
            annexe_25_26_refugies_apatrides_decision_protection_parent=[
                'uuid-annexe_25_26_refugies_apatrides_decision_protection_parent'
            ],
            titre_sejour_3_mois_parent=['uuid-titre_sejour_3_mois_parent'],
            fiches_remuneration_parent=['uuid-fiches_remuneration_parent'],
            attestation_cpas_parent=['uuid-attestation_cpas_parent'],
            decision_bourse_cfwb=['uuid-decision_bourse_cfwb'],
            attestation_boursier=['uuid-attestation_boursier'],
            titre_identite_sejour_longue_duree_ue=['uuid-titre_identite_sejour_longue_duree_ue'],
            titre_sejour_belgique=['uuid-titre_sejour_belgique'],
            numero_compte_iban='BE43068999999501',
            iban_valide=True,
            numero_compte_autre_format='123456',
            code_bic_swift_banque='GKCCBEBB',
            prenom_titulaire_compte='John',
            nom_titulaire_compte='Doe',
        )

        continuing_proposition_dto = _PropositionFormationContinueDTO(
            uuid='uuid-proposition',
            formation=_FormationDTO(
                sigle='FC1',
                annee=2023,
                intitule='Formation continue 1',
                campus='Louvain-La-Neuve',
                type=TrainingType.CERTIFICATE_OF_SUCCESS.name,
                code_domaine='CDFC',
                campus_inscription='Mons',
                sigle_entite_gestion='FFC',
                code='FC1',
            ),
            reference='0123',
            annee_calculee=2023,
            pot_calcule=None,
            date_fin_pot=None,
            creee_le=datetime.datetime(2023, 1, 1),
            modifiee_le=datetime.datetime(2023, 1, 1),
            soumise_le=None,
            erreurs=[],
            statut=ChoixStatutPropositionContinue.EN_BROUILLON.name,
            matricule_candidat='MAT1',
            prenom_candidat='John',
            nom_candidat='Doe',
            pays_nationalite_candidat='BE',
            pays_nationalite_ue_candidat=True,
            reponses_questions_specifiques=cls.answers_to_specific_questions,
            curriculum=['uuid-curriculum'],
            equivalence_diplome=['uuid-equivalence-diplome'],
            copie_titre_sejour=['uuid-copie-titre-sejour'],
            inscription_a_titre=ChoixInscriptionATitre.PRIVE.name,
            nom_siege_social='',
            numero_unique_entreprise='',
            numero_tva_entreprise='',
            adresse_mail_professionnelle='',
            type_adresse_facturation='',
            adresse_facturation=None,
            elements_confirmation={},
            pdf_recapitulatif=['uuid-pdf-recapitulatif'],
        )
        bachelor_proposition_dto = _PropositionFormationGeneraleDTO(
            uuid='uuid-proposition',
            formation=_FormationDTO(
                sigle='FG1',
                annee=2023,
                intitule='Bachelor 1',
                campus='Louvain-La-Neuve',
                type=TrainingType.BACHELOR.name,
                code_domaine='CDFG',
                campus_inscription='Mons',
                sigle_entite_gestion='FFG',
                code='FG1',
            ),
            reference='0123',
            annee_calculee=2023,
            pot_calcule=None,
            date_fin_pot=None,
            creee_le=datetime.datetime(2023, 1, 1),
            modifiee_le=datetime.datetime(2023, 1, 1),
            soumise_le=None,
            erreurs=[],
            statut=ChoixStatutPropositionContinue.EN_BROUILLON.name,
            matricule_candidat='MAT1',
            prenom_candidat='John',
            nom_candidat='Doe',
            reponses_questions_specifiques=cls.answers_to_specific_questions,
            curriculum=['uuid-curriculum'],
            equivalence_diplome=['uuid-equivalence-diplome'],
            elements_confirmation={},
            pdf_recapitulatif=['uuid-pdf-recapitulatif'],
            attestation_inscription_reguliere=['uuid-attestation-inscription-reguliere'],
            bourse_double_diplome=None,
            bourse_erasmus_mundus=None,
            bourse_internationale=None,
            est_bachelier_belge=None,
            est_modification_inscription_externe=None,
            est_non_resident_au_sens_decret=None,
            est_reorientation_inscription_externe=None,
            formulaire_modification_inscription=['uuid-formulaire-modification-inscription'],
        )
        doctorate_proposition_dto = _PropositionFormationDoctoraleDTO(
            uuid='uuid-proposition',
            doctorat=DoctoratDTO(
                sigle='FD1',
                annee=2023,
                intitule='Doctorate 1',
                campus='Louvain-La-Neuve',
                type=TrainingType.BACHELOR.name,
                campus_inscription='Mons',
                sigle_entite_gestion='FFD',
            ),
            reference='1234',
            annee_calculee=2023,
            pot_calcule=None,
            date_fin_pot=None,
            creee_le=datetime.datetime(2023, 1, 1),
            modifiee_le=datetime.datetime(2023, 1, 1),
            soumise_le=None,
            erreurs=[],
            statut=ChoixStatutPropositionContinue.EN_BROUILLON.name,
            matricule_candidat='MAT1',
            prenom_candidat='John',
            nom_candidat='Doe',
            reponses_questions_specifiques=cls.answers_to_specific_questions,
            curriculum=['uuid-curriculum'],
            elements_confirmation={},
            pdf_recapitulatif=['uuid-pdf-recapitulatif'],
            bourse_erasmus_mundus=None,
            autre_bourse_recherche='',
            bourse_date_debut=None,
            bourse_date_fin=None,
            bourse_preuve=['uuid-bourse-preuve'],
            bourse_recherche=None,
            code_secteur_formation='',
            commission_proximite='',
            date_soutenance=None,
            doctorat_deja_realise='',
            documents_projet=['uuid-documents-projet'],
            domaine_these='',
            duree_prevue=None,
            eft=None,
            fiche_archive_signatures_envoyees=['uuid-fiche-archive-signatures-envoyees'],
            graphe_gantt=['uuid-graphe-gantt'],
            institut_these=None,
            nom_institut_these='',
            sigle_institut_these='',
            institution='',
            intitule_secteur_formation='',
            justification='',
            langue_redaction_these='',
            lettres_recommandation=['uuid-lettres-recommandation'],
            lieu_these='',
            nationalite_candidat='',
            projet_formation_complementaire=['uuid-projet-formation-complementaire'],
            proposition_programme_doctoral=['uuid-proposition-programme-doctoral'],
            raison_non_soutenue='',
            resume_projet='',
            temps_consacre=None,
            titre_projet='',
            type_admission='',
            type_contrat_travail='',
            type_financement='',
        )
        cls.continuing_context = _ResumePropositionDTO(
            identification=identification_dto,
            coordonnees=coordinates_dto,
            curriculum=curriculum_dto,
            etudes_secondaires=continuing_secondary_studies_dto,
            connaissances_langues=None,
            proposition=continuing_proposition_dto,
            comptabilite=None,
            groupe_supervision=None,
        )
        cls.general_bachelor_context = _ResumePropositionDTO(
            identification=identification_dto,
            coordonnees=coordinates_dto,
            curriculum=curriculum_dto,
            etudes_secondaires=bachelor_secondary_studies_dto,
            connaissances_langues=None,
            proposition=bachelor_proposition_dto,
            comptabilite=accounting_dto,
            groupe_supervision=None,
        )
        cls.doctorate_context = _ResumePropositionDTO(
            identification=identification_dto,
            coordonnees=coordinates_dto,
            curriculum=curriculum_dto,
            etudes_secondaires=None,
            connaissances_langues=[
                ConnaissanceLangueDTO(
                    langue=FR_ISO_CODE,
                    nom_langue='French',
                    comprehension_orale='C2',
                    capacite_orale='C2',
                    capacite_ecriture='C2',
                    certificat=['uuid-french-certificat'],
                ),
                ConnaissanceLangueDTO(
                    langue='EN',
                    nom_langue='English',
                    comprehension_orale='C1',
                    capacite_orale='C1',
                    capacite_ecriture='C1',
                    certificat=['uuid-english-certificat'],
                ),
            ],
            proposition=doctorate_proposition_dto,
            comptabilite=accounting_dto,
            groupe_supervision=_GroupeDeSupervisionDTO(
                signatures_promoteurs=[
                    DetailSignaturePromoteurDTO(
                        statut=ChoixEtatSignature.APPROVED.name,
                        pdf=['uuid-signature-1'],
                        promoteur=PromoteurDTO(
                            uuid='uuid-1',
                            matricule='123',
                            nom='Doe',
                            prenom='John',
                            email='john.doe@example.com',
                        ),
                    ),
                    DetailSignaturePromoteurDTO(
                        statut=ChoixEtatSignature.INVITED.name,
                        pdf=['uuid-signature-3'],
                        promoteur=PromoteurDTO(
                            uuid='uuid-3',
                            matricule='789',
                            nom='Poe',
                            prenom='Joe',
                            email='joe.poe@example.com',
                        ),
                    ),
                ],
                signatures_membres_CA=[
                    DetailSignatureMembreCADTO(
                        statut=ChoixEtatSignature.APPROVED.name,
                        pdf=['uuid-signature-2'],
                        membre_CA=MembreCADTO(
                            uuid='uuid-2',
                            matricule='456',
                            nom='Foe',
                            prenom='Jane',
                            email='jane.foe@example.com',
                        ),
                    )
                ],
                cotutelle=_CotutelleDTO(
                    cotutelle=True,
                    motivation='Reason for the cotutelle',
                    institution_fwb=False,
                    institution='Institute',
                    demande_ouverture=['uuid-demande-ouverture'],
                    convention=['uuid-convention'],
                    autres_documents=['uuid-autres-documents'],
                ),
            ),
        )

    def setUp(self) -> None:
        # Mock weasyprint
        patcher = mock.patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

    # Identification attachments
    def test_identification_attachments_without_id_number(self):
        with mock.patch.multiple(
            self.continuing_context.identification,
            numero_carte_identite='',
            numero_registre_national_belge='',
            numero_passeport='',
        ):
            section = get_identification_section(self.continuing_context)
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(_('Identity picture'), self.continuing_context.identification.photo_identite),
                ],
            )

    def test_identification_attachments_with_national_number(self):
        with mock.patch.multiple(
            self.continuing_context.identification,
            numero_carte_identite='',
            numero_registre_national_belge='0123456',
            numero_passeport='',
        ):
            section = get_identification_section(self.continuing_context)
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(_('Identity picture'), self.continuing_context.identification.photo_identite),
                    Attachment(_('Identity card (both sides)'), self.continuing_context.identification.carte_identite),
                ],
            )

    def test_identification_attachments_with_id_card_number(self):
        with mock.patch.multiple(
            self.continuing_context.identification,
            numero_carte_identite='0123456',
            numero_registre_national_belge='',
            numero_passeport='',
        ):
            section = get_identification_section(self.continuing_context)
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(_('Identity picture'), self.continuing_context.identification.photo_identite),
                    Attachment(_('Identity card (both sides)'), self.continuing_context.identification.carte_identite),
                ],
            )

    def test_identification_attachments_with_passport_number(self):
        with mock.patch.multiple(
            self.continuing_context.identification,
            numero_carte_identite='',
            numero_registre_national_belge='',
            numero_passeport='0123456',
        ):
            section = get_identification_section(self.continuing_context)
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(_('Identity picture'), self.continuing_context.identification.photo_identite),
                    Attachment(_('Passport'), self.continuing_context.identification.passeport),
                ],
            )

    # Secondary studies attachments
    def test_secondary_studies_attachments_for_continuing_proposition(self):
        section = get_secondary_studies_section(
            self.continuing_context,
            settings.LANGUAGE_CODE_FR,
            self.specific_questions,
        )
        document_question = self.specific_questions.get(Onglets.ETUDES_SECONDAIRES.name)[1]
        self.assertCountEqual(
            section.attachments,
            [
                Attachment(
                    document_question.form_item.title.get(settings.LANGUAGE_CODE_FR),
                    self.answers_to_specific_questions[str(document_question.form_item.uuid)],
                )
            ],
        )
        section = get_secondary_studies_section(
            self.continuing_context,
            settings.LANGUAGE_CODE_EN,
            self.specific_questions,
        )
        document_question = self.specific_questions.get(Onglets.ETUDES_SECONDAIRES.name)[1]
        self.assertCountEqual(
            section.attachments,
            [
                Attachment(
                    document_question.form_item.title.get(settings.LANGUAGE_CODE_EN),
                    self.answers_to_specific_questions[str(document_question.form_item.uuid)],
                )
            ],
        )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_got_belgian_diploma(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_etranger=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.YES.name,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('High school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_belge.diplome,
                    )
                ],
            )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_got_belgian_diploma_this_year(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_etranger=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.THIS_YEAR.name,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('High school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_belge.diplome,
                    ),
                    Attachment(
                        _('Certificate of enrolment or school attendance'),
                        self.general_bachelor_context.etudes_secondaires.diplome_belge.certificat_inscription,
                    ),
                ],
            )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_alternative(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_etranger=None,
            diplome_belge=None,
            diplome_etudes_secondaires=GotDiploma.NO.name,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _(
                            'Certificate of successful completion of the admission test for the first cycle of higher '
                            'education'
                        ),
                        self.general_bachelor_context.etudes_secondaires.alternative_secondaires.examen_admission_premier_cycle,
                    ),
                ],
            )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_foreign_diploma(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_belge=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.YES.name,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('High school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
                    ),
                    Attachment(
                        _('A transcript or your last year at high school'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
                    ),
                ],
            )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_foreign_diploma_with_translations(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_belge=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.YES.name,
        ), mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires.diplome_etranger,
            regime_linguistique='BR',
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('High school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
                    ),
                    Attachment(
                        _('A transcript or your last year at high school'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
                    ),
                    Attachment(
                        _('A certified translation of your high school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.traduction_diplome,
                    ),
                    Attachment(
                        _(
                            'A certified translation of your official transcript of marks for your final year of '
                            'secondary education'
                        ),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.traduction_releve_notes,
                    ),
                ],
            )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_not_ue_foreign_diploma_this_year(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_belge=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.THIS_YEAR.name,
        ), mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires.diplome_etranger,
            pays_membre_ue=False,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('High school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
                    ),
                    Attachment(
                        _('A transcript or your last year at high school'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
                    ),
                ],
            )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_ue_foreign_diploma_this_year(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_belge=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.THIS_YEAR.name,
        ), mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires.diplome_etranger,
            regime_linguistique='BR',
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('High school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
                    ),
                    Attachment(
                        _('A transcript or your last year at high school'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
                    ),
                    Attachment(
                        _('A certified translation of your high school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.traduction_diplome,
                    ),
                    Attachment(
                        _(
                            'A certified translation of your official transcript of marks for your final year of '
                            'secondary education'
                        ),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.traduction_releve_notes,
                    ),
                    Attachment(
                        _('Certificate of enrolment or school attendance'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.certificat_inscription,
                    ),
                    Attachment(
                        _('A certified translation of your certificate of enrolment or school attendance'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.traduction_certificat_inscription,
                    ),
                ],
            )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_assimilated_foreign_diploma_this_year(
        self,
    ):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_belge=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.THIS_YEAR.name,
        ), mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires.diplome_etranger,
            pays_membre_ue=False,
        ), mock.patch.multiple(
            self.general_bachelor_context.proposition.formation,
            code_domaine='11SA',
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('High school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
                    ),
                    Attachment(
                        _('A transcript or your last year at high school'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
                    ),
                    Attachment(
                        _('Certificate of enrolment or school attendance'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.certificat_inscription,
                    ),
                ],
            )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_not_ue_foreign_national_bachelor_diploma_equiv(
        self,
    ):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_belge=None,
            alternative_secondaires=None,
        ), mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires.diplome_etranger,
            type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            pays_membre_ue=False,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('High school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
                    ),
                    Attachment(
                        _('A transcript or your last year at high school'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
                    ),
                    Attachment(
                        _('A double-sided copy of the final equivalence decision'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.decision_final_equivalence_hors_ue,
                    ),
                ],
            )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_ue_foreign_national_bachelor_diploma_equival(
        self,
    ):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_belge=None,
            alternative_secondaires=None,
        ), mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires.diplome_etranger,
            type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            equivalence=Equivalence.YES.name,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('High school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
                    ),
                    Attachment(
                        _('A transcript or your last year at high school'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
                    ),
                    Attachment(
                        _('A double-sided copy of the final equivalence decision'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.decision_final_equivalence_ue,
                    ),
                ],
            )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_ue_foreign_national_bachelor_diploma_pending_eq(
        self,
    ):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_belge=None,
            alternative_secondaires=None,
        ), mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires.diplome_etranger,
            type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            equivalence=Equivalence.PENDING.name,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('High school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
                    ),
                    Attachment(
                        _('A transcript or your last year at high school'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
                    ),
                    Attachment(
                        _('Proof of the final equivalence decision'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.preuve_decision_equivalence,
                    ),
                ],
            )

    def test_secondary_studies_attachments_for_bachelor_proposition_and_ue_foreign_national_bachelor_diploma_without_eq(
        self,
    ):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_belge=None,
            alternative_secondaires=None,
        ), mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires.diplome_etranger,
            type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            equivalence=Equivalence.NO.name,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('High school diploma'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
                    ),
                    Attachment(
                        _('A transcript or your last year at high school'),
                        self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
                    ),
                ],
            )

    # Curriculum attachments
    def test_curriculum_attachments_for_continuing_proposition_without_equivalence(self):
        section = get_curriculum_section(
            self.continuing_context,
            settings.LANGUAGE_CODE_FR,
            self.specific_questions,
        )

        document_question = self.specific_questions.get(Onglets.CURRICULUM.name)[1]
        self.assertCountEqual(
            section.attachments,
            [
                Attachment(
                    document_question.form_item.title.get(settings.LANGUAGE_CODE_FR),
                    self.answers_to_specific_questions[str(document_question.form_item.uuid)],
                ),
                Attachment(
                    _('Curriculum vitae detailed, dated and signed'), self.continuing_context.proposition.curriculum
                ),
            ],
        )

    def test_curriculum_attachments_for_continuing_proposition_with_equivalence(self):
        with mock.patch.multiple(
            self.continuing_context.proposition.formation,
            type=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
        ):
            section = get_curriculum_section(self.continuing_context, settings.LANGUAGE_CODE_FR, self.empty_questions)

            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('Curriculum vitae detailed, dated and signed'),
                        self.continuing_context.proposition.curriculum,
                    ),
                    Attachment(
                        _(
                            'Decision of equivalence for your diploma(s) giving access to the training, if this(these) '
                            'has(have) been obtained outside Belgium'
                        ),
                        self.continuing_context.proposition.equivalence_diplome,
                    ),
                ],
            )

    def test_curriculum_attachments_for_master_proposition(self):
        with mock.patch.multiple(
            self.general_bachelor_context.proposition.formation,
            type=TrainingType.MASTER_MC.name,
        ):
            section = get_curriculum_section(
                self.general_bachelor_context, settings.LANGUAGE_CODE_FR, self.empty_questions
            )

            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('Curriculum vitae detailed, dated and signed'),
                        self.continuing_context.proposition.curriculum,
                    ),
                ],
            )

    def test_curriculum_attachments_for_capaes_proposition_and_equivalence(self):
        with mock.patch.multiple(
            self.general_bachelor_context.proposition.formation,
            type=TrainingType.CAPAES.name,
        ):
            section = get_curriculum_section(
                self.general_bachelor_context, settings.LANGUAGE_CODE_FR, self.empty_questions
            )

            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('Curriculum vitae detailed, dated and signed'),
                        self.continuing_context.proposition.curriculum,
                    ),
                    Attachment(
                        _(
                            'Decision of equivalence for your diploma(s) giving access to the training, if this(these) '
                            'has(have) been obtained outside Belgium'
                        ),
                        self.continuing_context.proposition.equivalence_diplome,
                    ),
                ],
            )

    def test_curriculum_attachments_for_bachelor_proposition(self):
        section = get_curriculum_section(self.general_bachelor_context, settings.LANGUAGE_CODE_FR, self.empty_questions)
        self.assertEqual(len(section.attachments), 0)

    def test_curriculum_acad_experience_attachments_with_continuing_proposition(self):
        experience = self.continuing_context.curriculum.experiences_academiques[0]
        section = get_educational_experience_section(
            self.continuing_context,
            experience,
        )
        self.assertCountEqual(
            section.attachments,
            [Attachment(_('Graduate degree'), experience.diplome)],
        )

    def test_curriculum_acad_experience_attachments_with_general_proposition_and_global_transcript(self):
        experience = self.general_bachelor_context.curriculum.experiences_academiques[0]
        with mock.patch.multiple(experience, type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name):
            section = get_educational_experience_section(
                self.general_bachelor_context,
                experience,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(_('Transcript'), experience.releve_notes),
                    Attachment(_('Graduate degree'), experience.diplome),
                ],
            )

    def test_curriculum_acad_experience_attachments_with_general_proposition_and_global_transcript_and_translation(
        self,
    ):
        experience = self.general_bachelor_context.curriculum.experiences_academiques[0]
        with mock.patch.multiple(
            experience,
            type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
            regime_linguistique='BR',
        ):
            section = get_educational_experience_section(
                self.general_bachelor_context,
                experience,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(_('Transcript'), experience.releve_notes),
                    Attachment(_('Transcript translation'), experience.traduction_releve_notes),
                    Attachment(_('Graduate degree'), experience.diplome),
                    Attachment(_('Graduate degree translation'), experience.traduction_diplome),
                ],
            )

    def test_curriculum_acad_experience_attachments_with_general_proposition_and_annual_transcript(self):
        experience = self.general_bachelor_context.curriculum.experiences_academiques[0]
        experience_year = experience.annees[0]
        with mock.patch.multiple(experience, type_releve_notes=TranscriptType.ONE_A_YEAR.name):
            section = get_educational_experience_section(
                self.general_bachelor_context,
                experience,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(_('Transcript') + f' - {experience_year.annee}', experience_year.releve_notes),
                    Attachment(_('Graduate degree'), experience.diplome),
                ],
            )

    def test_curriculum_acad_experience_attachments_with_general_proposition_and_annual_transcript_and_translation(
        self,
    ):
        experience = self.general_bachelor_context.curriculum.experiences_academiques[0]
        experience_year = experience.annees[0]
        with mock.patch.multiple(
            experience,
            type_releve_notes=TranscriptType.ONE_A_YEAR.name,
            regime_linguistique='BR',
        ):
            section = get_educational_experience_section(
                self.general_bachelor_context,
                experience,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(_('Transcript') + f' - {experience_year.annee}', experience_year.releve_notes),
                    Attachment(
                        _('Transcript translation') + f' - {experience_year.annee}',
                        experience_year.traduction_releve_notes,
                    ),
                    Attachment(_('Graduate degree'), experience.diplome),
                    Attachment(_('Graduate degree translation'), experience.traduction_diplome),
                ],
            )

    def test_curriculum_acad_experience_attachments_with_doctorate_proposition(self):
        experience = self.doctorate_context.curriculum.experiences_academiques[0]
        section = get_educational_experience_section(
            self.doctorate_context,
            experience,
        )
        self.assertCountEqual(
            section.attachments,
            [
                Attachment(_('Dissertation summary'), experience.resume_memoire),
                Attachment(_('Transcript'), experience.releve_notes),
                Attachment(_('Graduate degree'), experience.diplome),
            ],
        )

    def test_curriculum_non_academic_experience_attachments_with_continuing_proposition(self):
        section = get_non_educational_experience_section(
            self.continuing_context,
            self.continuing_context.curriculum.experiences_non_academiques[0],
        )
        self.assertEqual(len(section.attachments), 0)

    def test_curriculum_non_academic_experience_attachments_with_general_proposition_and_working_activity(self):
        experience = self.general_bachelor_context.curriculum.experiences_non_academiques[0]
        section = get_non_educational_experience_section(
            self.general_bachelor_context,
            experience,
        )
        self.assertCountEqual(
            section.attachments,
            [
                Attachment(
                    CURRICULUM_ACTIVITY_LABEL.get(ActivityType.WORK.name),
                    experience.certificat,
                ),
            ],
        )

    def test_curriculum_non_academic_experience_attachments_with_general_proposition_and_other_activity(self):
        experience = self.general_bachelor_context.curriculum.experiences_non_academiques[0]
        with mock.patch.multiple(experience, type=ActivityType.OTHER.name):
            section = get_non_educational_experience_section(
                self.general_bachelor_context,
                experience,
            )
            self.assertEqual(len(section.attachments), 0)

    def test_curriculum_non_academic_experience_attachments_with_doctorate_proposition_and_other_activity(self):
        experience = self.doctorate_context.curriculum.experiences_non_academiques[0]
        with mock.patch.multiple(experience, type=ActivityType.LANGUAGE_TRAVEL.name):
            section = get_non_educational_experience_section(
                self.doctorate_context,
                experience,
            )
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        CURRICULUM_ACTIVITY_LABEL.get(ActivityType.LANGUAGE_TRAVEL.name),
                        experience.certificat,
                    ),
                ],
            )

    def test_specific_questions_attachments_with_continuing_proposition(self):
        with mock.patch.multiple(
            self.continuing_context.proposition,
            pays_nationalite_ue_candidat=True,
        ):
            section = get_specific_questions_section(
                self.continuing_context,
                settings.LANGUAGE_CODE_FR,
                self.specific_questions,
            )
            document_question = self.specific_questions.get(Onglets.INFORMATIONS_ADDITIONNELLES.name)[1]

            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        document_question.form_item.title.get(settings.LANGUAGE_CODE_FR),
                        self.answers_to_specific_questions[str(document_question.form_item.uuid)],
                    ),
                ],
            )

    def test_specific_questions_attachments_with_continuing_proposition_non_ue_candidate(self):
        with mock.patch.multiple(
            self.continuing_context.proposition,
            pays_nationalite_ue_candidat=False,
        ):
            section = get_specific_questions_section(
                self.continuing_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )

            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _(
                            'Copy of the residence permit covering the entire course, including the evaluation test (except for courses organised online)'
                        ),
                        self.continuing_context.proposition.copie_titre_sejour,
                    )
                ],
            )

    def test_specific_questions_attachments_with_general_proposition_and_reorientation(self):
        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            est_non_resident_au_sens_decret=False,
            est_reorientation_inscription_externe=True,
        ):
            section = get_specific_questions_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )

            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('Certificate of regular enrolment'),
                        self.general_bachelor_context.proposition.attestation_inscription_reguliere,
                    )
                ],
            )
        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            est_non_resident_au_sens_decret=False,
            est_reorientation_inscription_externe=False,
        ):
            section = get_specific_questions_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )

            self.assertEqual(len(section.attachments), 0)

    def test_specific_questions_attachments_with_general_proposition_and_modification(self):
        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            est_non_resident_au_sens_decret=False,
            est_modification_inscription_externe=True,
        ):
            section = get_specific_questions_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )

            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        _('Registration modification form'),
                        self.general_bachelor_context.proposition.formulaire_modification_inscription,
                    )
                ],
            )
        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            est_non_resident_au_sens_decret=False,
            est_modification_inscription_externe=False,
        ):
            section = get_specific_questions_section(
                self.general_bachelor_context,
                settings.LANGUAGE_CODE_FR,
                self.empty_questions,
            )

            self.assertEqual(len(section.attachments), 0)

    def test_accounting_attachments_with_general_proposition_for_ue_candidate_and_french_frequented_institute(self):
        section = get_accounting_section(self.general_bachelor_context)
        self.assertCountEqual(
            section.attachments,
            [
                Attachment(
                    ngettext(
                        'Certificate stating the absence of debts towards the institution attended during '
                        'the academic year %(academic_year)s: %(names)s',
                        'Certificates stating the absence of debts towards the institutions attended during '
                        'the academic year %(academic_year)s: %(names)s',
                        1,
                    )
                    % {'academic_year': '2023-2024', 'names': 'Institut 1'},
                    self.general_bachelor_context.comptabilite.attestation_absence_dette_etablissement,
                ),
            ],
        )

    def test_accounting_attachments_with_general_proposition_for_ue_child_staff_candidate(self):
        with mock.patch.multiple(self.general_bachelor_context.comptabilite, enfant_personnel=True):
            section = get_accounting_section(self.general_bachelor_context)
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        ngettext(
                            'Certificate stating the absence of debts towards the institution attended during '
                            'the academic year %(academic_year)s: %(names)s',
                            'Certificates stating the absence of debts towards the institutions attended during '
                            'the academic year %(academic_year)s: %(names)s',
                            1,
                        )
                        % {'academic_year': '2023-2024', 'names': 'Institut 1'},
                        self.general_bachelor_context.comptabilite.attestation_absence_dette_etablissement,
                    ),
                    Attachment(
                        _('Staff child certificate'),
                        self.general_bachelor_context.comptabilite.attestation_enfant_personnel,
                    ),
                ],
            )

    def test_accounting_attachments_with_general_proposition_for_not_ue_candidate(self):
        with mock.patch.multiple(
            self.general_bachelor_context.identification,
            pays_nationalite_europeen=False,
        ), mock.patch.multiple(
            self.general_bachelor_context.comptabilite,
            type_situation_assimilation=TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name,
            sous_type_situation_assimilation_5=ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
            relation_parente=LienParente.PERE.name,
        ):
            section = get_accounting_section(self.general_bachelor_context)
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(
                        ngettext(
                            'Certificate stating the absence of debts towards the institution attended during '
                            'the academic year %(academic_year)s: %(names)s',
                            'Certificates stating the absence of debts towards the institutions attended during '
                            'the academic year %(academic_year)s: %(names)s',
                            1,
                        )
                        % {'academic_year': '2023-2024', 'names': 'Institut 1'},
                        self.general_bachelor_context.comptabilite.attestation_absence_dette_etablissement,
                    ),
                    Attachment(
                        ACCOUNTING_LABEL['composition_menage_acte_naissance'],
                        self.general_bachelor_context.comptabilite.composition_menage_acte_naissance,
                    ),
                    Attachment(
                        ACCOUNTING_LABEL['attestation_cpas_parent'] % {'person_concerned': 'votre père'},
                        self.general_bachelor_context.comptabilite.attestation_cpas_parent,
                    ),
                ],
            )

    def test_languages_attachments_with_doctorate_proposition(self):
        section = get_languages_section(self.doctorate_context)
        self.assertCountEqual(
            section.attachments,
            [
                Attachment(
                    _('Certificate of language knowledge') + ' - French',
                    self.doctorate_context.connaissances_langues[0].certificat,
                ),
                Attachment(
                    _('Certificate of language knowledge') + ' - English',
                    self.doctorate_context.connaissances_langues[1].certificat,
                ),
            ],
        )

    def test_research_project_attachments_with_doctorate_proposition(self):
        section = get_research_project_section(self.doctorate_context)
        self.assertCountEqual(
            section.attachments,
            [
                Attachment(_('Research project'), self.doctorate_context.proposition.documents_projet),
                Attachment(
                    _("Doctoral program proposition"), self.doctorate_context.proposition.proposition_programme_doctoral
                ),
                Attachment(
                    _("Complementary training proposition"),
                    self.doctorate_context.proposition.projet_formation_complementaire,
                ),
                Attachment(_("Gantt graph"), self.doctorate_context.proposition.graphe_gantt),
                Attachment(_("Recommendation letters"), self.doctorate_context.proposition.lettres_recommandation),
            ],
        )

    def test_research_project_attachments_with_doctorate_proposition_and_search_scholarship(self):
        with mock.patch.multiple(
            self.doctorate_context.proposition,
            type_financement=ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
        ):
            section = get_research_project_section(self.doctorate_context)
            self.assertCountEqual(
                section.attachments,
                [
                    Attachment(_('Research project'), self.doctorate_context.proposition.documents_projet),
                    Attachment(
                        _("Doctoral program proposition"),
                        self.doctorate_context.proposition.proposition_programme_doctoral,
                    ),
                    Attachment(
                        _("Complementary training proposition"),
                        self.doctorate_context.proposition.projet_formation_complementaire,
                    ),
                    Attachment(_("Gantt graph"), self.doctorate_context.proposition.graphe_gantt),
                    Attachment(_("Recommendation letters"), self.doctorate_context.proposition.lettres_recommandation),
                    Attachment(_('Scholarship proof'), self.doctorate_context.proposition.bourse_preuve),
                ],
            )

    def test_cotutelle_attachments_with_doctorate_proposition_without_specified_cotutelle(self):
        with mock.patch.multiple(
            self.doctorate_context.groupe_supervision,
            cotutelle=None,
        ):
            section = get_cotutelle_section(self.doctorate_context)
            self.assertEqual(len(section.attachments), 0)

    def test_cotutelle_attachments_with_doctorate_proposition_with_no_cotutelle(self):
        with mock.patch.multiple(
            self.doctorate_context.groupe_supervision.cotutelle,
            cotutelle=False,
        ):
            section = get_cotutelle_section(self.doctorate_context)
            self.assertEqual(len(section.attachments), 0)

    def test_cotutelle_attachments_with_doctorate_proposition_with_specified_cotutelle(self):
        section = get_cotutelle_section(self.doctorate_context)
        self.assertCountEqual(
            section.attachments,
            [
                Attachment(
                    _('Cotutelle opening request'),
                    self.doctorate_context.groupe_supervision.cotutelle.demande_ouverture,
                ),
                Attachment(
                    _('Cotutelle convention'),
                    self.doctorate_context.groupe_supervision.cotutelle.convention,
                ),
                Attachment(
                    _('Other documents concerning cotutelle'),
                    self.doctorate_context.groupe_supervision.cotutelle.autres_documents,
                ),
            ],
        )

    def test_supervision_attachments_with_doctorate_proposition(self):
        section = get_supervision_section(self.doctorate_context)
        self.assertCountEqual(
            section.attachments,
            [
                Attachment(
                    _('Approbation by pdf of %(member)s') % {'member': 'Jane Foe'},
                    self.doctorate_context.groupe_supervision.signatures_membres_CA[0].pdf,
                ),
                Attachment(
                    _('Approbation by pdf of %(member)s') % {'member': 'John Doe'},
                    self.doctorate_context.groupe_supervision.signatures_promoteurs[0].pdf,
                ),
            ],
        )
