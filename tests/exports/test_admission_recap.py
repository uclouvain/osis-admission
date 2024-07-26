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
from io import BytesIO
from typing import Dict, List
from unittest.mock import MagicMock

import attr
import freezegun
import img2pdf
import mock
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import override_settings
from osis_async.models import AsyncTask
from rest_framework import status

from admission.calendar.admission_calendar import (
    AdmissionPoolExternalEnrollmentChangeCalendar,
    AdmissionPoolExternalReorientationCalendar,
)
from admission.constants import JPEG_MIME_TYPE, PNG_MIME_TYPE, ORDERED_CAMPUSES_UUIDS
from admission.models import AdmissionTask
from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeFinancement,
    ChoixEtatSignature,
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.dtos import (
    ConnaissanceLangueDTO,
    CotutelleDTO,
    DetailSignatureMembreCADTO,
    DetailSignaturePromoteurDTO,
    DoctoratDTO,
    GroupeDeSupervisionDTO,
    MembreCADTO,
    PromoteurDTO,
    PropositionDTO as PropositionFormationDoctoraleDTO,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.ddd.admission.dtos import AdressePersonnelleDTO, CoordonneesDTO, IdentificationDTO
from admission.ddd.admission.dtos.campus import CampusDTO
from admission.ddd.admission.dtos.etudes_secondaires import EtudesSecondairesAdmissionDTO
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
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
from admission.ddd.admission.enums.emplacement_document import (
    DocumentsIdentification,
    DocumentsEtudesSecondaires,
    DocumentsCurriculum,
    DocumentsQuestionsSpecifiques,
    DocumentsComptabilite,
    DocumentsConnaissancesLangues,
    DocumentsProjetRecherche,
    DocumentsCotutelle,
    DocumentsSupervision,
    IdentifiantBaseEmplacementDocument,
    DocumentsSuiteAutorisation,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_continue.commands import RecupererQuestionsSpecifiquesQuery
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixInscriptionATitre,
    ChoixStatutPropositionContinue,
    ChoixEdition,
)
from admission.ddd.admission.formation_continue.dtos import PropositionDTO as PropositionFormationContinueDTO
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.dtos import (
    ComptabiliteDTO,
    PropositionDTO as PropositionFormationGeneraleDTO,
)
from admission.exports.admission_recap.attachments import (
    Attachment,
)
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
    get_dynamic_questions_by_tab,
    get_training_choice_section,
    get_authorization_section,
    get_requestable_free_document_section,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import UnfrozenDTO
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.curriculum import (
    AdmissionEducationalValuatedExperiencesFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
)
from admission.tests.factories.form_item import (
    AdmissionFormItemInstantiationFactory,
    DocumentAdmissionFormItemFactory,
    TextAdmissionFormItemFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.person import (
    CompletePersonForIUFCFactory,
    CompletePersonForBachelorFactory,
    CompletePersonFactory,
)
from admission.tests.factories.roles import ProgramManagerRoleFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.civil_state import CivilState
from base.models.enums.community import CommunityEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.enums.got_diploma import GotDiploma
from base.models.enums.state_iufc import StateIUFC
from base.models.enums.teaching_type import TeachingTypeEnum
from base.models.person import Person
from base.tests import QueriesAssertionsMixin, TestCaseWithQueriesAssertions
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import (
    AlternativeSecondairesDTO,
    DiplomeBelgeEtudesSecondairesDTO,
    DiplomeEtrangerEtudesSecondairesDTO,
    ValorisationEtudesSecondairesDTO,
)
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import (
    AnneeExperienceAcademiqueDTO,
    ExperienceAcademiqueDTO,
    ExperienceNonAcademiqueDTO,
)
from infrastructure.messages_bus import message_bus_instance
from osis_profile import BE_ISO_CODE
from osis_profile.models.enums.curriculum import (
    ActivitySector,
    ActivityType,
    EvaluationSystem,
    Grade,
    Result,
    TranscriptType,
    CURRICULUM_ACTIVITY_LABEL,
)
from osis_profile.models.enums.education import (
    BelgianCommunitiesOfEducation,
    EducationalType,
    Equivalence,
    ForeignDiplomaTypes,
)
from reference.models.enums.cycle import Cycle
from reference.tests.factories.country import CountryFactory


@attr.dataclass
class _IdentificationDTO(UnfrozenDTO, IdentificationDTO):
    pass


@attr.dataclass
class _EtudesSecondairesDTO(UnfrozenDTO, EtudesSecondairesAdmissionDTO):
    pass


@attr.dataclass
class _ValorisationEtudesSecondairesDTO(UnfrozenDTO, ValorisationEtudesSecondairesDTO):
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
class _CurriculumDTO(UnfrozenDTO, CurriculumAdmissionDTO):
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
class _DiplomeBelgeEtudesSecondairesDTO(UnfrozenDTO, DiplomeBelgeEtudesSecondairesDTO):
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
@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class AdmissionRecapTestCase(TestCaseWithQueriesAssertions, QueriesAssertionsMixin):
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
                'size': 1,
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: ['550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'] if value else []
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {
            token: {
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
                'size': 1,
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

    def test_attachment_equality(self):
        id_card_1 = Attachment(label='PDF', uuids=[''], identifier='CARTE_IDENTITE')
        id_card_2 = Attachment(label='PDF', uuids=[''], identifier='CARTE_IDENTITE')
        id_photo = Attachment(label='JPEG', uuids=[''], identifier='PHOTO_IDENTITE')
        self.assertEqual(id_card_1, id_card_2)
        self.assertNotEqual(id_card_1, id_photo)

    def test_get_raw_with_pdf_attachment(self):
        pdf_attachment = Attachment(label='PDF', uuids=[''], identifier='CARTE_IDENTITE')
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
        image_attachment = Attachment(label='JPEG', uuids=[''], identifier='CARTE_IDENTITE')
        image_attachment.get_raw(
            token='token',
            metadata={
                'name': 'myfile',
                'mimetype': JPEG_MIME_TYPE,
            },
            default_content=self.bytes_io_default_content,
        )
        self.get_raw_content_mock.assert_called_once_with('token')
        self.convert_img_mock.assert_called_once_with(
            self.get_raw_content_mock.return_value, rotation=img2pdf.Rotation.ifvalid
        )

    def test_convert_and_get_raw_with_png_attachment(self):
        image_attachment = Attachment(label='PNG', uuids=[''], identifier='CARTE_IDENTITE')
        image_attachment.get_raw(
            token='token',
            metadata={
                'name': 'myfile',
                'mimetype': PNG_MIME_TYPE,
            },
            default_content=self.bytes_io_default_content,
        )
        self.get_raw_content_mock.assert_called_once_with('token')
        self.convert_img_mock.assert_called_once_with(
            self.get_raw_content_mock.return_value, rotation=img2pdf.Rotation.ifvalid
        )

    def test_get_default_content_if_mimetype_is_not_supported(self):
        unknown_attachment = Attachment(label='Unknown', uuids=[''], identifier='CARTE_IDENTITE')
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
        pdf_attachment = Attachment(label='PDF', uuids=[''], identifier='CARTE_IDENTITE')
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

    def test_generation_with_continuing_education_not_submitted_proposition(self):
        candidate = CompletePersonForIUFCFactory(country_of_citizenship=CountryFactory(european_union=False))
        admission = ContinuingEducationAdmissionFactory(
            candidate=candidate,
            residence_permit=['file-uuid'],
            status=ChoixStatutPropositionContinue.EN_BROUILLON.name,
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
                    'curriculum_academic_experience',
                    'curriculum_non_academic_experience',
                    'curriculum',
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
        self.assertEqual(
            call_args_by_tab['curriculum_academic_experience'].title,
            'Curriculum > Computer science 2021-2022',
        )
        self.assertEqual(
            call_args_by_tab['curriculum_non_academic_experience'].title,
            'Curriculum > Travail 01/2021-03/2021',
        )
        self.assertEqual(call_args_by_tab['curriculum'].title, 'Curriculum')
        self.assertEqual(call_args_by_tab['specific_question'].title, 'Informations complémentaires')
        self.assertEqual(len(call_args_by_tab['specific_question'].children), 1)
        self.assertEqual(
            call_args_by_tab['specific_question'].children[0].title,
            'Copie du titre de séjour qui couvre la totalité de la formation, épreuve d’évaluation comprise (sauf '
            'pour les formations organisées en ligne)',
        )
        self.assertEqual(call_args_by_tab['confirmation'].title, 'Finalisation')

        self.assertEqual(pdf_token, 'pdf-token')

    def test_generation_with_continuing_education_submitted_proposition(self):
        candidate: Person = CompletePersonForIUFCFactory(country_of_citizenship=CountryFactory(european_union=False))

        educational_experience = candidate.educationalexperience_set.first()
        non_educational_experience = candidate.professionalexperience_set.first()

        admission = ContinuingEducationAdmissionFactory(
            candidate=candidate,
            residence_permit=['file-uuid'],
            submitted=True,
        )

        from admission.exports.admission_recap.admission_recap import admission_pdf_recap

        admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        tabs_titles = [tab[0][0].title for tab in self.outline_root.append.call_args_list]

        self.assertEqual(len(tabs_titles), 7)

        self.assertNotIn('Curriculum > Computer science 2021-2022', tabs_titles)
        self.assertNotIn('Curriculum > Travail 01/2021-03/2021', tabs_titles)

        other_admission = ContinuingEducationAdmissionFactory()

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=other_admission, educationalexperience=educational_experience
        )

        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=other_admission,
            professionalexperience=non_educational_experience,
        )

        self.outline_root.reset_mock()

        admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        tabs_titles = [tab[0][0].title for tab in self.outline_root.append.call_args_list]

        self.assertEqual(len(tabs_titles), 7)

        self.assertNotIn('Curriculum > Computer science 2021-2022', tabs_titles)
        self.assertNotIn('Curriculum > Travail 01/2021-03/2021', tabs_titles)

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=admission, educationalexperience=educational_experience
        )

        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=admission,
            professionalexperience=non_educational_experience,
        )

        self.outline_root.reset_mock()

        admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        tabs_titles = [tab[0][0].title for tab in self.outline_root.append.call_args_list]

        self.assertEqual(len(tabs_titles), 9)

        self.assertIn('Curriculum > Computer science 2021-2022', tabs_titles)
        self.assertIn('Curriculum > Travail 01/2021-03/2021', tabs_titles)

    def test_generation_with_general_education_not_submitted_proposition(self):
        candidate: Person = CompletePersonForBachelorFactory(
            country_of_citizenship=CountryFactory(european_union=False),
        )

        admission = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.BACHELOR.name,
            status=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            candidate=candidate,
        )

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
                    'curriculum_academic_experience',
                    'curriculum_non_academic_experience',
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
        self.assertEqual(
            call_args_by_tab['curriculum_academic_experience'].title,
            'Curriculum > Computer science 2021-2022',
        )
        self.assertEqual(
            call_args_by_tab['curriculum_non_academic_experience'].title,
            'Curriculum > Travail 01/2021-03/2021',
        )
        self.assertEqual(call_args_by_tab['curriculum'].title, 'Curriculum')
        self.assertEqual(call_args_by_tab['specific_question'].title, 'Informations complémentaires')
        self.assertEqual(call_args_by_tab['accounting'].title, 'Comptabilité')
        self.assertEqual(call_args_by_tab['confirmation'].title, 'Finalisation')

    def test_generation_with_general_education_submitted_proposition(self):
        candidate: Person = CompletePersonForBachelorFactory(
            country_of_citizenship=CountryFactory(european_union=False),
        )

        educational_experience = candidate.educationalexperience_set.first()
        non_educational_experience = candidate.professionalexperience_set.first()

        admission = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.BACHELOR.name,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            candidate=candidate,
        )
        from admission.exports.admission_recap.admission_recap import admission_pdf_recap

        admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        tabs_titles = [tab[0][0].title for tab in self.outline_root.append.call_args_list]

        self.assertEqual(len(tabs_titles), 8)

        self.assertNotIn('Curriculum > Computer science 2021-2022', tabs_titles)
        self.assertNotIn('Curriculum > Travail 01/2021-03/2021', tabs_titles)

        other_admission = GeneralEducationAdmissionFactory(candidate=candidate)

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=other_admission, educationalexperience=educational_experience
        )

        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=other_admission,
            professionalexperience=non_educational_experience,
        )

        self.outline_root.reset_mock()

        admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        tabs_titles = [tab[0][0].title for tab in self.outline_root.append.call_args_list]

        self.assertEqual(len(tabs_titles), 8)

        self.assertNotIn('Curriculum > Computer science 2021-2022', tabs_titles)
        self.assertNotIn('Curriculum > Travail 01/2021-03/2021', tabs_titles)

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=admission, educationalexperience=educational_experience
        )

        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=admission,
            professionalexperience=non_educational_experience,
        )

        self.outline_root.reset_mock()

        admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        tabs_titles = [tab[0][0].title for tab in self.outline_root.append.call_args_list]

        self.assertEqual(len(tabs_titles), 10)

        self.assertIn('Curriculum > Computer science 2021-2022', tabs_titles)
        self.assertIn('Curriculum > Travail 01/2021-03/2021', tabs_titles)

    def test_generation_with_doctorate_education_not_submitted_proposition(self):
        candidate = CompletePersonFactory()
        admission = DoctorateAdmissionFactory(
            candidate=candidate,
            status=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
        )

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
                    'curriculum_attachment',
                    'curriculum_academic_experience',
                    'curriculum_non_academic_experience',
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
        self.assertEqual(call_args_by_tab['curriculum_attachment'].title, 'Curriculum vitae détaillé, daté et signé')
        self.assertEqual(call_args_by_tab['curriculum'].title, 'Curriculum')
        self.assertEqual(
            call_args_by_tab['curriculum_academic_experience'].title,
            'Curriculum > Computer science 2021-2023',
        )
        self.assertEqual(
            call_args_by_tab['curriculum_non_academic_experience'].title,
            'Curriculum > Travail 01/2021-03/2021',
        )
        self.assertEqual(call_args_by_tab['accounting'].title, 'Comptabilité')
        self.assertEqual(call_args_by_tab['project'].title, 'Projet de recherche doctoral')
        self.assertEqual(call_args_by_tab['cotutelle'].title, 'Cotutelle')
        self.assertEqual(call_args_by_tab['supervision'].title, 'Supervision')
        self.assertEqual(call_args_by_tab['confirmation'].title, 'Finalisation')

    def test_generation_with_doctorate_education_submitted_proposition(self):
        candidate: Person = CompletePersonFactory()
        admission = DoctorateAdmissionFactory(
            candidate=candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        educational_experience = candidate.educationalexperience_set.first()
        non_educational_experience = candidate.professionalexperience_set.first()

        from admission.exports.admission_recap.admission_recap import admission_pdf_recap

        admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        tabs_titles = [tab[0][0].title for tab in self.outline_root.append.call_args_list]

        self.assertEqual(len(tabs_titles), 11)

        self.assertNotIn('Curriculum > Computer science 2021-2023', tabs_titles)
        self.assertNotIn('Curriculum > Travail 01/2021-03/2021', tabs_titles)

        other_admission = DoctorateAdmissionFactory(candidate=candidate)

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=other_admission,
            educationalexperience=educational_experience,
        )

        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=other_admission,
            professionalexperience=non_educational_experience,
        )

        self.outline_root.reset_mock()

        admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        tabs_titles = [tab[0][0].title for tab in self.outline_root.append.call_args_list]

        self.assertEqual(len(tabs_titles), 11)

        self.assertNotIn('Curriculum > Computer science 2021-2023', tabs_titles)
        self.assertNotIn('Curriculum > Travail 01/2021-03/2021', tabs_titles)

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=admission,
            educationalexperience=educational_experience,
        )

        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=admission,
            professionalexperience=non_educational_experience,
        )

        self.outline_root.reset_mock()

        admission_pdf_recap(admission, settings.LANGUAGE_CODE)

        tabs_titles = [tab[0][0].title for tab in self.outline_root.append.call_args_list]

        self.assertEqual(len(tabs_titles), 13)

        self.assertIn('Curriculum > Computer science 2021-2023', tabs_titles)
        self.assertIn('Curriculum > Travail 01/2021-03/2021', tabs_titles)

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

        with self.assertNumQueriesLessThan(14):
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

        with self.assertNumQueriesLessThan(15):
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
@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class SectionsAttachmentsTestCase(TestCaseWithQueriesAssertions):
    @classmethod
    def setUpTestData(cls):
        # Mock osis-document
        cls.get_remote_token_patcher = mock.patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        cls.get_remote_token_patcher.start()

        cls.get_remote_metadata_patcher = mock.patch(
            "osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile", "size": 1}
        )
        cls.get_remote_metadata_patcher.start()

        cls.confirm_remote_upload_patcher = mock.patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        cls.confirm_remote_upload_patcher.start()

        cls.confirm_multiple_remote_upload_patcher = mock.patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        cls.confirm_multiple_remote_upload_patcher.start()

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

        specific_questions: Dict[str, List[AdmissionFormItemInstantiationFactory]] = {
            tab.name: [
                AdmissionFormItemInstantiationFactory(
                    form_item=TextAdmissionFormItemFactory(),
                    academic_year=cls.academic_year,
                    tab=tab.name,
                    weight=0,
                ),
                AdmissionFormItemInstantiationFactory(
                    form_item=DocumentAdmissionFormItemFactory(),
                    academic_year=cls.academic_year,
                    tab=tab.name,
                    weight=1,
                ),
            ]
            for tab in Onglets
        }

        cls.admission = ContinuingEducationAdmissionFactory(
            training__academic_year=cls.academic_year,
            specific_question_answers={
                str(question.form_item.uuid): f'answer-{index}'
                if question.form_item.type == TypeItemFormulaire.TEXTE.name
                else [f'uuid-file-{index}']
                for index, tab_questions in enumerate(specific_questions.values())
                for question in tab_questions
            },
        )

        for free_document in specific_questions[Onglets.DOCUMENTS.name]:
            free_document.admission = cls.admission
            free_document.save()

        all_specific_questions_dto: List[QuestionSpecifiqueDTO] = message_bus_instance.invoke(
            RecupererQuestionsSpecifiquesQuery(uuid_proposition=cls.admission.uuid),
        )

        cls.specific_questions = get_dynamic_questions_by_tab(all_specific_questions_dto)
        cls.empty_questions = get_dynamic_questions_by_tab([])

        identification_dto = _IdentificationDTO(
            matricule='MAT1',
            nom='Doe',
            prenom='John',
            autres_prenoms='Jack',
            date_naissance=datetime.date(1990, 1, 1),
            annee_naissance=None,
            pays_nationalite='BE',
            pays_nationalite_europeen=True,
            nom_pays_nationalite='Belgique',
            sexe='M',
            genre='H',
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
            date_expiration_carte_identite=datetime.date(2023, 1, 1),
            date_expiration_passeport=datetime.date(2023, 1, 1),
        )
        coordinates_dto = _CoordonneesDTO(
            domicile_legal=_AdressePersonnelleDTO(
                rue='Rue du pin',
                code_postal='1048',
                ville='Louvain-la-Neuve',
                pays='BE',
                nom_pays='Belgique',
                numero_rue='1',
                boite_postale='BB8',
            ),
            adresse_correspondance=None,
            numero_mobile='0123456789',
            adresse_email_privee='johndoe@example.com',
            numero_contact_urgence='0123456789',
        )
        cls.belgian_academic_curriculum_experience = _ExperienceAcademiqueDTO(
            uuid='uuid-1',
            pays=BE_ISO_CODE,
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
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2023,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['uuid-releve-notes-1'],
                    traduction_releve_notes=['uuid-traduction-releve-notes'],
                    credits_inscrits=220,
                    credits_acquis=220,
                    avec_bloc_1=None,
                    avec_complement=None,
                    allegement='',
                    est_reorientation_102=None,
                    credits_inscrits_communaute_fr=None,
                    credits_acquis_communaute_fr=None,
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
            cycle_formation=Cycle.FIRST_CYCLE.name,
            type_institut=EstablishmentTypeEnum.UNIVERSITY.name,
            nom_formation_equivalente_communaute_fr='',
            est_autre_formation=False,
            identifiant_externe='123456789',
        )
        cls.foreign_academic_curriculum_experience = _ExperienceAcademiqueDTO(
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
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2023,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['uuid-releve-notes-1'],
                    traduction_releve_notes=['uuid-traduction-releve-notes'],
                    credits_inscrits=220,
                    credits_acquis=220,
                    avec_bloc_1=None,
                    avec_complement=None,
                    allegement='',
                    est_reorientation_102=None,
                    credits_inscrits_communaute_fr=None,
                    credits_acquis_communaute_fr=None,
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
            cycle_formation=Cycle.FIRST_CYCLE.name,
            type_institut=EstablishmentTypeEnum.UNIVERSITY.name,
            nom_formation_equivalente_communaute_fr='',
            est_autre_formation=False,
            identifiant_externe='123456789',
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
                    identifiant_externe='123456789',
                )
            ],
            experiences_academiques=[
                cls.foreign_academic_curriculum_experience,
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
            valorisation=_ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[],
            ),
        )
        bachelor_secondary_studies_dto = _EtudesSecondairesDTO(
            diplome_belge=_DiplomeBelgeEtudesSecondairesDTO(
                diplome=['uuid-diplome'],
                type_enseignement=EducationalType.PROFESSIONAL_EDUCATION.name,
                autre_type_enseignement='Other type',
                nom_institut='UCL',
                adresse_institut='Louvain-la-Neuve',
                communaute=BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
            ),
            diplome_etranger=_DiplomeEtrangerEtudesSecondairesDTO(
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
            valorisation=_ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[],
            ),
            identifiant_externe='123456789',
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
            preuve_statut_apatride=['uuid-preuve_statut_apatride'],
            carte_a=['uuid-carte_a'],
        )

        continuing_proposition_dto = _PropositionFormationContinueDTO(
            uuid='uuid-proposition',
            profil_soumis_candidat=None,
            formation=_FormationDTO(
                sigle='FC1',
                annee=2023,
                date_debut=datetime.date(2023, 9, 15),
                intitule='Formation continue 1',
                intitule_fr='Formation continue 1',
                intitule_en='Formation continue 1',
                campus=CampusDTO(
                    uuid=ORDERED_CAMPUSES_UUIDS['LOUVAIN_LA_NEUVE_UUID'],
                    nom='Louvain-la-Neuve',
                    code_postal='',
                    ville='',
                    pays_iso_code='',
                    nom_pays='',
                    rue='',
                    numero_rue='',
                    boite_postale='',
                    localisation='',
                    email_inscription_sic='',
                ),
                type=TrainingType.CERTIFICATE_OF_SUCCESS.name,
                code_domaine='CDFC',
                campus_inscription=CampusDTO(
                    uuid=ORDERED_CAMPUSES_UUIDS['MONS_UUID'],
                    nom='Mons',
                    code_postal='',
                    ville='',
                    pays_iso_code='',
                    nom_pays='',
                    rue='',
                    numero_rue='',
                    boite_postale='',
                    localisation='',
                    email_inscription_sic='',
                ),
                sigle_entite_gestion='FFC',
                code='FC1',
                credits=180,
            ),
            reference='0123',
            annee_calculee=2023,
            langue_contact_candidat=settings.LANGUAGE_CODE_FR,
            documents_libres_fac_uclouvain=[],
            documents_libres_sic_uclouvain=[],
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
            nom_pays_nationalite_candidat='Belgique',
            noma_candidat='548267',
            adresse_email_candidat='john.doe@example.be',
            date_changement_statut=datetime.datetime(2023, 1, 1),
            candidat_a_plusieurs_demandes=False,
            reponses_questions_specifiques=cls.admission.specific_question_answers,
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
            documents_additionnels=[],
            motivations='My motivation',
            moyens_decouverte_formation=[],
            autre_moyen_decouverte_formation='',
            adresses_emails_gestionnaires_formation=[],
            documents_demandes={},
            marque_d_interet=False,
            aide_a_la_formation=False,
            inscription_au_role_obligatoire=True,
            etat_formation=StateIUFC.OPEN.name,
            edition=ChoixEdition.UN.name,
            en_ordre_de_paiement=False,
            droits_reduits=False,
            paye_par_cheque_formation=False,
            cep=False,
            etalement_des_paiments=False,
            etalement_de_la_formation=False,
            valorisation_des_acquis_d_experience=False,
            a_presente_l_epreuve_d_evaluation=False,
            a_reussi_l_epreuve_d_evaluation=False,
            diplome_produit=False,
            intitule_du_tff="",
            decision_dernier_mail_envoye_le=None,
            decision_dernier_mail_envoye_par="",
            motif_de_mise_en_attente="",
            motif_de_mise_en_attente_autre="",
            condition_d_approbation_par_la_faculte="",
            motif_de_refus="",
            motif_de_refus_autre="",
            motif_d_annulation="",
        )
        bachelor_proposition_dto = _PropositionFormationGeneraleDTO(
            uuid='uuid-proposition',
            formation=_FormationDTO(
                sigle='FG1',
                annee=2023,
                date_debut=datetime.date(2023, 9, 15),
                intitule='Bachelor 1',
                intitule_fr='Bachelor 1',
                intitule_en='Bachelor 1',
                campus=CampusDTO(
                    uuid=ORDERED_CAMPUSES_UUIDS['LOUVAIN_LA_NEUVE_UUID'],
                    nom='Louvain-la-Neuve',
                    code_postal='',
                    ville='',
                    pays_iso_code='',
                    nom_pays='',
                    rue='',
                    numero_rue='',
                    boite_postale='',
                    localisation='',
                    email_inscription_sic='',
                ),
                type=TrainingType.BACHELOR.name,
                code_domaine='CDFG',
                campus_inscription=CampusDTO(
                    uuid=ORDERED_CAMPUSES_UUIDS['MONS_UUID'],
                    nom='Mons',
                    code_postal='',
                    ville='',
                    pays_iso_code='',
                    nom_pays='',
                    rue='',
                    numero_rue='',
                    boite_postale='',
                    localisation='',
                    email_inscription_sic='',
                ),
                sigle_entite_gestion='FFG',
                code='FG1',
                credits=180,
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
            reponses_questions_specifiques=cls.admission.specific_question_answers,
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
            documents_demandes={},
            documents_libres_sic_uclouvain=[],
            documents_libres_fac_uclouvain=[],
            certificat_refus_fac=[],
            certificat_approbation_fac=[],
            documents_additionnels=[],
            poste_diplomatique=None,
            financabilite_regle_calcule="",
            financabilite_regle_calcule_situation='',
            financabilite_regle_calcule_le=None,
            financabilite_regle="",
            financabilite_regle_etabli_par="",
            financabilite_regle_etabli_le=None,
            certificat_approbation_sic=[],
            certificat_approbation_sic_annexe=[],
            certificat_refus_sic=[],
            doit_fournir_visa_etudes=False,
            visa_etudes_d=['uuid-visa-etudes-d'],
            certificat_autorisation_signe=['uuid-certificat-autorisation-signe'],
            type=TypeDemande.ADMISSION.name,
            financabilite_derogation_statut='',
            financabilite_derogation_premiere_notification_le=None,
            financabilite_derogation_premiere_notification_par='',
            financabilite_derogation_derniere_notification_le=None,
            financabilite_derogation_derniere_notification_par='',
        )
        doctorate_proposition_dto = _PropositionFormationDoctoraleDTO(
            uuid='uuid-proposition',
            doctorat=DoctoratDTO(
                sigle='FD1',
                annee=2023,
                intitule='Doctorate 1',
                campus='Louvain-la-Neuve',
                type=TrainingType.BACHELOR.name,
                campus_inscription='Mons',
                sigle_entite_gestion='FFD',
                code='CFD1',
            ),
            reference='1234',
            annee_calculee=2023,
            type_demande=TypeDemande.ADMISSION.name,
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
            reponses_questions_specifiques=cls.admission.specific_question_answers,
            curriculum=['uuid-curriculum'],
            elements_confirmation={},
            pdf_recapitulatif=['uuid-pdf-recapitulatif'],
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
            projet_doctoral_deja_commence=False,
            projet_doctoral_institution='',
            projet_doctoral_date_debut=None,
            nationalite_candidat='',
            projet_formation_complementaire=['uuid-projet-formation-complementaire'],
            proposition_programme_doctoral=['uuid-proposition-programme-doctoral'],
            raison_non_soutenue='',
            resume_projet='',
            temps_consacre=None,
            est_lie_fnrs_fria_fresh_csc=False,
            commentaire_financement='',
            titre_projet='',
            type_admission='',
            type_contrat_travail='',
            type_financement='',
            langue_contact_candidat=settings.LANGUAGE_CODE_FR,
            documents_demandes={},
            documents_libres_sic_uclouvain=[],
            documents_libres_fac_uclouvain=[],
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
                    nom_langue_en='French',
                    nom_langue_fr='Français',
                    comprehension_orale='C2',
                    capacite_orale='C2',
                    capacite_ecriture='C2',
                    certificat=['uuid-french-certificat'],
                ),
                ConnaissanceLangueDTO(
                    langue='EN',
                    nom_langue_en='English',
                    nom_langue_fr='Anglais',
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
                    autre_institution=False,
                    autre_institution_nom='',
                    autre_institution_adresse='',
                ),
            ),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.get_remote_token_patcher.stop()
        cls.get_remote_metadata_patcher.stop()
        cls.confirm_remote_upload_patcher.stop()
        cls.confirm_multiple_remote_upload_patcher.stop()
        super().tearDownClass()

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
            section = get_identification_section(self.continuing_context, True)
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)

            self.assertEqual(attachments[0].identifier, 'PHOTO_IDENTITE')
            self.assertEqual(attachments[0].label, DocumentsIdentification['PHOTO_IDENTITE'])
            self.assertEqual(attachments[0].uuids, self.continuing_context.identification.photo_identite)
            self.assertTrue(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

    def test_identification_attachments_with_national_number(self):
        with mock.patch.multiple(
            self.continuing_context.identification,
            numero_carte_identite='',
            numero_registre_national_belge='0123456',
            numero_passeport='',
        ):
            section = get_identification_section(self.continuing_context, False)
            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'PHOTO_IDENTITE')
            self.assertEqual(attachments[0].label, DocumentsIdentification['PHOTO_IDENTITE'])
            self.assertEqual(attachments[0].uuids, self.continuing_context.identification.photo_identite)
            self.assertTrue(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'CARTE_IDENTITE')
            self.assertEqual(attachments[1].label, DocumentsIdentification['CARTE_IDENTITE'])
            self.assertEqual(attachments[1].uuids, self.continuing_context.identification.carte_identite)
            self.assertTrue(attachments[1].required)
            self.assertFalse(attachments[1].readonly)

    def test_identification_attachments_with_id_card_number(self):
        with mock.patch.multiple(
            self.continuing_context.identification,
            numero_carte_identite='0123456',
            numero_registre_national_belge='',
            numero_passeport='',
        ):
            section = get_identification_section(self.continuing_context, False)
            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'PHOTO_IDENTITE')
            self.assertEqual(attachments[0].label, DocumentsIdentification['PHOTO_IDENTITE'])
            self.assertEqual(attachments[0].uuids, self.continuing_context.identification.photo_identite)
            self.assertTrue(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'CARTE_IDENTITE')
            self.assertEqual(attachments[1].label, DocumentsIdentification['CARTE_IDENTITE'])
            self.assertEqual(attachments[1].uuids, self.continuing_context.identification.carte_identite)
            self.assertTrue(attachments[1].required)
            self.assertFalse(attachments[1].readonly)

    def test_identification_attachments_with_passport_number(self):
        with mock.patch.multiple(
            self.continuing_context.identification,
            numero_carte_identite='',
            numero_registre_national_belge='',
            numero_passeport='0123456',
        ):
            section = get_identification_section(self.continuing_context, False)
            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'PHOTO_IDENTITE')
            self.assertEqual(attachments[0].label, DocumentsIdentification['PHOTO_IDENTITE'])
            self.assertEqual(attachments[0].uuids, self.continuing_context.identification.photo_identite)
            self.assertTrue(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'PASSEPORT')
            self.assertEqual(attachments[1].label, DocumentsIdentification['PASSEPORT'])
            self.assertEqual(attachments[1].uuids, self.continuing_context.identification.passeport)
            self.assertTrue(attachments[1].required)
            self.assertFalse(attachments[1].readonly)

    # Secondary studies attachments
    def test_secondary_studies_attachments_for_continuing_proposition(self):
        section = get_secondary_studies_section(
            self.continuing_context,
            self.specific_questions,
            True,
        )
        attachments = section.attachments
        document_question = self.specific_questions.get(Onglets.ETUDES_SECONDAIRES.name)[1]

        self.assertEqual(len(attachments), 1)

        self.assertEqual(
            attachments[0].identifier,
            f'{IdentifiantBaseEmplacementDocument.QUESTION_SPECIFIQUE.name}.{document_question.uuid}',
        )
        self.assertEqual(attachments[0].label, document_question.label)
        self.assertEqual(attachments[0].uuids, self.admission.specific_question_answers[document_question.uuid])
        self.assertFalse(attachments[0].required)
        self.assertFalse(attachments[0].readonly)

    def test_secondary_studies_attachments_for_bachelor_proposition_and_got_belgian_diploma(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_etranger=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.YES.name,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                self.empty_questions,
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_BELGE_DIPLOME')
            self.assertEqual(attachments[0].label, DocumentsEtudesSecondaires['DIPLOME_BELGE_DIPLOME'])
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_belge.diplome,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

    def test_secondary_studies_attachments_for_bachelor_proposition_and_got_not_epc_belgian_diploma(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_etranger=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.YES.name,
            identifiant_externe=None,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                self.empty_questions,
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_BELGE_DIPLOME')
            self.assertFalse(attachments[0].readonly)

    def test_secondary_studies_attachments_for_bachelor_proposition_and_got_belgian_diploma_this_year(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_etranger=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.THIS_YEAR.name,
        ):
            # The document is specified
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                self.empty_questions,
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_BELGE_DIPLOME')
            self.assertEqual(attachments[0].label, DocumentsEtudesSecondaires['DIPLOME_BELGE_DIPLOME'])
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_belge.diplome,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            # The document is missing
            with mock.patch.multiple(
                self.general_bachelor_context.etudes_secondaires.diplome_belge,
                diplome=[],
            ):
                section = get_secondary_studies_section(
                    self.general_bachelor_context,
                    self.empty_questions,
                    False,
                )
                attachments = section.attachments

                self.assertEqual(len(attachments), 1)

                self.assertEqual(attachments[0].identifier, 'DIPLOME_BELGE_DIPLOME')
                self.assertTrue(attachments[0].required)
                self.assertTrue(attachments[0].readonly)

    def test_secondary_studies_attachments_for_bachelor_proposition_and_alternative(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_etranger=None,
            diplome_belge=None,
            diplome_etudes_secondaires=GotDiploma.NO.name,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                self.empty_questions,
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)

            self.assertEqual(attachments[0].identifier, 'ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE')
            self.assertEqual(
                attachments[0].label,
                DocumentsEtudesSecondaires['ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE'],
            )
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.alternative_secondaires.examen_admission_premier_cycle,
            )
            # Required because it is not a VAE access
            self.assertTrue(attachments[0].required)

            self.assertTrue(attachments[0].readonly)

            # Simulate a VAE access (36 months of non academic experiences) -> Not required
            experience = self.general_bachelor_context.curriculum.experiences_non_academiques[0]
            with mock.patch.multiple(experience, date_debut=datetime.date(2020, 4, 1)):
                section = get_secondary_studies_section(
                    self.general_bachelor_context,
                    self.empty_questions,
                    False,
                )
                attachments = section.attachments

                self.assertEqual(len(attachments), 1)
                self.assertEqual(
                    attachments[0].identifier,
                    'ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE',
                )
                self.assertFalse(attachments[0].required)
                self.assertTrue(attachments[0].readonly)

            # Simulate a non-VAE access (35 months of non academic experiences) -> Required
            with mock.patch.multiple(experience, date_debut=datetime.date(2020, 5, 1)):
                section = get_secondary_studies_section(
                    self.general_bachelor_context,
                    self.empty_questions,
                    False,
                )
                attachments = section.attachments

                self.assertEqual(len(attachments), 1)
                self.assertEqual(
                    attachments[0].identifier,
                    'ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE',
                )
                self.assertTrue(attachments[0].required)
                self.assertTrue(attachments[0].readonly)

    def test_secondary_studies_attachments_for_bachelor_proposition_and_foreign_diploma(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_belge=None,
            alternative_secondaires=None,
            diplome_etudes_secondaires=GotDiploma.YES.name,
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                self.empty_questions,
                False,
            )

            attachments = section.attachments
            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_ETRANGER_DIPLOME')
            self.assertEqual(attachments[0].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DIPLOME'])
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_RELEVE_NOTES')
            self.assertEqual(attachments[1].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_RELEVE_NOTES'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
            )
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

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
                self.empty_questions,
                False,
            )

            attachments = section.attachments

            self.assertEqual(len(attachments), 4)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_ETRANGER_DIPLOME')
            self.assertEqual(attachments[0].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DIPLOME'])
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_TRADUCTION_DIPLOME')
            self.assertEqual(attachments[1].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_TRADUCTION_DIPLOME'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.traduction_diplome,
            )
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

            self.assertEqual(attachments[2].identifier, 'DIPLOME_ETRANGER_RELEVE_NOTES')
            self.assertEqual(attachments[2].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_RELEVE_NOTES'])
            self.assertEqual(
                attachments[2].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
            )
            self.assertTrue(attachments[2].required)
            self.assertTrue(attachments[2].readonly)

            self.assertEqual(attachments[3].identifier, 'DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES')
            self.assertEqual(
                attachments[3].label,
                DocumentsEtudesSecondaires['DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES'],
            )
            self.assertEqual(
                attachments[3].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.traduction_releve_notes,
            )
            self.assertTrue(attachments[3].required)
            self.assertTrue(attachments[3].readonly)

            # The diploma is not specified -> the related translation is required
            with mock.patch.multiple(
                self.general_bachelor_context.etudes_secondaires.diplome_etranger,
                diplome=[],
            ):
                section = get_secondary_studies_section(
                    self.general_bachelor_context,
                    self.empty_questions,
                    False,
                )
                attachments = section.attachments

                self.assertEqual(len(attachments), 4)

                self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_TRADUCTION_DIPLOME')
                self.assertTrue(attachments[1].required)
                self.assertTrue(attachments[1].readonly)

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
                self.empty_questions,
                False,
            )

            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_ETRANGER_DIPLOME')
            self.assertEqual(attachments[0].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DIPLOME'])
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_RELEVE_NOTES')
            self.assertEqual(attachments[1].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_RELEVE_NOTES'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
            )
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

    def test_secondary_studies_attachments_for_bachelor_proposition_and_not_ue_foreign_diploma_with_translations(self):
        with mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires,
            diplome_belge=None,
            alternative_secondaires=None,
        ), mock.patch.multiple(
            self.general_bachelor_context.etudes_secondaires.diplome_etranger,
            pays_membre_ue=False,
            regime_linguistique='BR',
        ):
            section = get_secondary_studies_section(
                self.general_bachelor_context,
                self.empty_questions,
                False,
            )

            attachments = section.attachments

            self.assertEqual(len(attachments), 4)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_ETRANGER_DIPLOME')
            self.assertEqual(attachments[0].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DIPLOME'])
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_TRADUCTION_DIPLOME')
            self.assertEqual(attachments[1].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_TRADUCTION_DIPLOME'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.traduction_diplome,
            )
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

            self.assertEqual(attachments[2].identifier, 'DIPLOME_ETRANGER_RELEVE_NOTES')
            self.assertEqual(attachments[2].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_RELEVE_NOTES'])
            self.assertEqual(
                attachments[2].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
            )
            self.assertTrue(attachments[2].required)
            self.assertTrue(attachments[2].readonly)

            self.assertEqual(attachments[3].identifier, 'DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES')
            self.assertEqual(
                attachments[3].label,
                DocumentsEtudesSecondaires['DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES'],
            )
            self.assertEqual(
                attachments[3].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.traduction_releve_notes,
            )
            self.assertTrue(attachments[3].required)
            self.assertTrue(attachments[3].readonly)

            # The diploma is not specified -> the related translation is required
            with mock.patch.multiple(
                self.general_bachelor_context.etudes_secondaires.diplome_etranger,
                diplome=[],
            ):
                section = get_secondary_studies_section(
                    self.general_bachelor_context,
                    self.empty_questions,
                    False,
                )
                attachments = section.attachments

                self.assertEqual(len(attachments), 4)

                self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_TRADUCTION_DIPLOME')
                self.assertTrue(attachments[1].required)
                self.assertTrue(attachments[1].readonly)

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
                self.empty_questions,
                False,
            )

            attachments = section.attachments

            self.assertEqual(len(attachments), 4)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_ETRANGER_DIPLOME')
            self.assertEqual(attachments[0].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DIPLOME'])
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_TRADUCTION_DIPLOME')
            self.assertEqual(attachments[1].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_TRADUCTION_DIPLOME'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.traduction_diplome,
            )
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

            self.assertEqual(attachments[2].identifier, 'DIPLOME_ETRANGER_RELEVE_NOTES')
            self.assertEqual(attachments[2].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_RELEVE_NOTES'])
            self.assertEqual(
                attachments[2].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
            )
            self.assertTrue(attachments[2].required)
            self.assertTrue(attachments[2].readonly)

            self.assertEqual(attachments[3].identifier, 'DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES')
            self.assertEqual(
                attachments[3].label,
                DocumentsEtudesSecondaires['DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES'],
            )
            self.assertEqual(
                attachments[3].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.traduction_releve_notes,
            )
            self.assertTrue(attachments[3].required)
            self.assertTrue(attachments[3].readonly)

            # The diploma is not specified
            with mock.patch.multiple(
                self.general_bachelor_context.etudes_secondaires.diplome_etranger,
                diplome=[],
            ):
                section = get_secondary_studies_section(
                    self.general_bachelor_context,
                    self.empty_questions,
                    False,
                )
                attachments = section.attachments

                self.assertEqual(len(attachments), 4)

                self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_TRADUCTION_DIPLOME')
                self.assertTrue(attachments[1].required)
                self.assertTrue(attachments[1].readonly)

    def test_secondary_studies_attachments_for_bachelor_proposition_and_assimilated_foreign_diploma_this_year(self):
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
            section = get_secondary_studies_section(self.general_bachelor_context, self.empty_questions, False)

            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_ETRANGER_DIPLOME')
            self.assertEqual(attachments[0].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DIPLOME'])
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_RELEVE_NOTES')
            self.assertEqual(attachments[1].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_RELEVE_NOTES'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
            )
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

            # The diploma is missing
            with mock.patch.multiple(
                self.general_bachelor_context.etudes_secondaires.diplome_etranger,
                diplome=[],
            ):
                section = get_secondary_studies_section(
                    self.general_bachelor_context,
                    self.empty_questions,
                    False,
                )
                attachments = section.attachments

                self.assertEqual(len(attachments), 2)

                self.assertEqual(attachments[0].identifier, 'DIPLOME_ETRANGER_DIPLOME')
                self.assertTrue(attachments[0].required)
                self.assertTrue(attachments[0].readonly)

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
                self.empty_questions,
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 3)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE')
            self.assertEqual(
                attachments[0].label,
                DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE'],
            )
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.decision_final_equivalence_hors_ue,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_DIPLOME')
            self.assertEqual(attachments[1].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DIPLOME'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
            )
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

            self.assertEqual(attachments[2].identifier, 'DIPLOME_ETRANGER_RELEVE_NOTES')
            self.assertEqual(attachments[2].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_RELEVE_NOTES'])
            self.assertEqual(
                attachments[2].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
            )
            self.assertTrue(attachments[2].required)
            self.assertTrue(attachments[2].readonly)

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
            section = get_secondary_studies_section(self.general_bachelor_context, self.empty_questions, False)

            attachments = section.attachments

            self.assertEqual(len(attachments), 3)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE')
            self.assertEqual(
                attachments[0].label,
                DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE'],
            )
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.decision_final_equivalence_ue,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_DIPLOME')
            self.assertEqual(attachments[1].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DIPLOME'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
            )
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

            self.assertEqual(attachments[2].identifier, 'DIPLOME_ETRANGER_RELEVE_NOTES')
            self.assertEqual(attachments[2].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_RELEVE_NOTES'])
            self.assertEqual(
                attachments[2].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
            )
            self.assertTrue(attachments[2].required)
            self.assertTrue(attachments[2].readonly)

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
                self.empty_questions,
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 3)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE')
            self.assertEqual(
                attachments[0].label,
                DocumentsEtudesSecondaires['DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE'],
            )
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.preuve_decision_equivalence,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_DIPLOME')
            self.assertEqual(attachments[1].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DIPLOME'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
            )
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

            self.assertEqual(attachments[2].identifier, 'DIPLOME_ETRANGER_RELEVE_NOTES')
            self.assertEqual(attachments[2].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_RELEVE_NOTES'])
            self.assertEqual(
                attachments[2].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
            )
            self.assertTrue(attachments[2].required)
            self.assertTrue(attachments[2].readonly)

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
            section = get_secondary_studies_section(self.general_bachelor_context, self.empty_questions, False)
            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_ETRANGER_DIPLOME')
            self.assertEqual(attachments[0].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DIPLOME'])
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.diplome,
            )
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME_ETRANGER_RELEVE_NOTES')
            self.assertEqual(attachments[1].label, DocumentsEtudesSecondaires['DIPLOME_ETRANGER_RELEVE_NOTES'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.etudes_secondaires.diplome_etranger.releve_notes,
            )
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

    def test_curriculum_attachments_for_continuing_proposition_with_short_training(self):
        with mock.patch.multiple(
            self.continuing_context.proposition,
            inscription_au_role_obligatoire=False,
        ):
            section = get_curriculum_section(self.continuing_context, self.empty_questions, False)
            attachments = section.attachments

            self.assertEqual(len(attachments), 0)

    def test_curriculum_attachments_for_continuing_proposition_with_long_training(self):
        with mock.patch.multiple(
            self.continuing_context.proposition,
            inscription_au_role_obligatoire=True,
        ):
            section = get_curriculum_section(self.continuing_context, self.empty_questions, False)
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)

            self.assertEqual(attachments[0].identifier, 'CURRICULUM')
            self.assertEqual(attachments[0].label, DocumentsCurriculum['CURRICULUM'])
            self.assertEqual(attachments[0].uuids, self.continuing_context.proposition.curriculum)
            self.assertFalse(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

    # Curriculum attachments
    def test_curriculum_attachments_for_continuing_proposition_without_equivalence(self):
        section = get_curriculum_section(
            self.continuing_context,
            self.specific_questions,
            True,
        )
        attachments = section.attachments

        document_question = self.specific_questions.get(Onglets.CURRICULUM.name)[1]

        self.assertEqual(len(attachments), 2)

        self.assertEqual(attachments[0].identifier, 'CURRICULUM')
        self.assertEqual(attachments[0].label, DocumentsCurriculum['CURRICULUM'])
        self.assertEqual(attachments[0].uuids, self.continuing_context.proposition.curriculum)
        self.assertFalse(attachments[0].required)
        self.assertFalse(attachments[0].readonly)

        self.assertEqual(
            attachments[1].identifier,
            f'{IdentifiantBaseEmplacementDocument.QUESTION_SPECIFIQUE.name}.{document_question.uuid}',
        )
        self.assertEqual(attachments[1].label, document_question.label)
        self.assertEqual(attachments[1].uuids, self.admission.specific_question_answers[document_question.uuid])
        self.assertFalse(attachments[1].required)
        self.assertFalse(attachments[1].readonly)

    def test_curriculum_attachments_for_continuing_proposition_with_equivalence(self):
        with mock.patch.multiple(
            self.continuing_context.proposition.formation,
            type=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
        ):
            section = get_curriculum_section(self.continuing_context, self.empty_questions, False)
            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_EQUIVALENCE')
            self.assertEqual(attachments[0].label, DocumentsCurriculum['DIPLOME_EQUIVALENCE'])
            self.assertEqual(attachments[0].uuids, self.continuing_context.proposition.equivalence_diplome)
            self.assertFalse(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'CURRICULUM')
            self.assertEqual(attachments[1].label, DocumentsCurriculum['CURRICULUM'])
            self.assertEqual(attachments[1].uuids, self.continuing_context.proposition.curriculum)
            self.assertFalse(attachments[1].required)
            self.assertFalse(attachments[1].readonly)

    def test_curriculum_attachments_for_master_proposition(self):
        with mock.patch.multiple(
            self.general_bachelor_context.proposition.formation,
            type=TrainingType.MASTER_MC.name,
        ):
            section = get_curriculum_section(self.general_bachelor_context, self.empty_questions, False)
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)

            self.assertEqual(attachments[0].identifier, 'CURRICULUM')
            self.assertEqual(attachments[0].label, DocumentsCurriculum['CURRICULUM'])
            self.assertEqual(attachments[0].uuids, self.general_bachelor_context.proposition.curriculum)
            self.assertTrue(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

    def test_curriculum_attachments_for_capaes_proposition_and_equivalence(self):
        with mock.patch.multiple(
            self.general_bachelor_context.proposition.formation,
            type=TrainingType.CAPAES.name,
        ):
            # With one obtained foreign diploma, display a required equivalence
            section = get_curriculum_section(self.general_bachelor_context, self.empty_questions, False)
            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'DIPLOME_EQUIVALENCE')
            self.assertEqual(attachments[0].label, DocumentsCurriculum['DIPLOME_EQUIVALENCE'])
            self.assertEqual(attachments[0].uuids, self.general_bachelor_context.proposition.equivalence_diplome)
            self.assertTrue(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'CURRICULUM')
            self.assertEqual(attachments[1].label, DocumentsCurriculum['CURRICULUM'])
            self.assertEqual(attachments[1].uuids, self.general_bachelor_context.proposition.curriculum)
            self.assertTrue(attachments[1].required)
            self.assertFalse(attachments[1].readonly)

            # With only one obtained belgian diploma, don't display the equivalence
            with mock.patch.multiple(
                self.general_bachelor_context.curriculum.experiences_academiques[0],
                pays=BE_ISO_CODE,
            ):
                section = get_curriculum_section(self.general_bachelor_context, self.empty_questions, False)
                attachments = section.attachments

                self.assertEqual(len(attachments), 1)
                self.assertEqual(attachments[0].identifier, 'CURRICULUM')

            # Without diploma, don't display the equivalence
            with mock.patch.multiple(
                self.general_bachelor_context.curriculum,
                experiences_academiques=[],
            ):
                section = get_curriculum_section(self.general_bachelor_context, self.empty_questions, False)
                attachments = section.attachments

                self.assertEqual(len(attachments), 1)
                self.assertEqual(attachments[0].identifier, 'CURRICULUM')

            # Without obtained diploma, don't display the equivalence
            with mock.patch.multiple(
                self.general_bachelor_context.curriculum.experiences_academiques[0],
                a_obtenu_diplome=False,
            ):
                section = get_curriculum_section(self.general_bachelor_context, self.empty_questions, False)
                attachments = section.attachments

                self.assertEqual(len(attachments), 1)
                self.assertEqual(attachments[0].identifier, 'CURRICULUM')

            # With both obtained foreign and belgian diplomas, display a facultative equivalence
            with mock.patch.multiple(
                self.general_bachelor_context.curriculum,
                experiences_academiques=[
                    self.foreign_academic_curriculum_experience,
                    self.belgian_academic_curriculum_experience,
                ],
            ):
                section = get_curriculum_section(self.general_bachelor_context, self.empty_questions, False)
                attachments = section.attachments

                self.assertEqual(len(attachments), 2)

                self.assertEqual(attachments[0].identifier, 'DIPLOME_EQUIVALENCE')
                self.assertFalse(attachments[0].required)

            # With several obtained foreign diplomas, display a required equivalence
            with mock.patch.multiple(
                self.general_bachelor_context.curriculum,
                experiences_academiques=[
                    self.foreign_academic_curriculum_experience,
                    self.foreign_academic_curriculum_experience,
                ],
            ):
                section = get_curriculum_section(self.general_bachelor_context, self.empty_questions, False)
                attachments = section.attachments

                self.assertEqual(len(attachments), 2)

                self.assertEqual(attachments[0].identifier, 'DIPLOME_EQUIVALENCE')
                self.assertTrue(attachments[0].required)

    def test_curriculum_attachments_for_bachelor_proposition(self):
        section = get_curriculum_section(self.general_bachelor_context, self.empty_questions, False)
        self.assertEqual(len(section.attachments), 0)

    def test_curriculum_acad_experience_attachments_with_continuing_proposition(self):
        experience = self.continuing_context.curriculum.experiences_academiques[0]
        section = get_educational_experience_section(
            self.continuing_context,
            experience,
            True,
        )
        attachments = section.attachments

        self.assertEqual(len(attachments), 1)

        self.assertEqual(attachments[0].identifier, 'DIPLOME')
        self.assertEqual(attachments[0].label, DocumentsCurriculum['DIPLOME'])
        self.assertEqual(attachments[0].uuids, experience.diplome)
        self.assertTrue(attachments[0].required)
        self.assertTrue(attachments[0].readonly)

    def test_curriculum_acad_non_epc_experience_attachments_with_continuing_proposition(self):
        experience = self.continuing_context.curriculum.experiences_academiques[0]

        with mock.patch.multiple(
            experience,
            type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
            identifiant_externe=None,
        ):
            section = get_educational_experience_section(
                self.continuing_context,
                experience,
                True,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)

            self.assertEqual(attachments[0].identifier, 'DIPLOME')
            self.assertFalse(attachments[0].readonly)

    def test_curriculum_acad_experience_attachments_with_general_proposition_and_global_transcript(self):
        experience = self.general_bachelor_context.curriculum.experiences_academiques[0]
        with mock.patch.multiple(experience, type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name):
            section = get_educational_experience_section(
                self.general_bachelor_context,
                experience,
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'RELEVE_NOTES')
            self.assertEqual(attachments[0].label, DocumentsCurriculum['RELEVE_NOTES'])
            self.assertEqual(attachments[0].uuids, experience.releve_notes)
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME')
            self.assertEqual(attachments[1].label, DocumentsCurriculum['DIPLOME'])
            self.assertEqual(attachments[1].uuids, experience.diplome)
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

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
                False,
            )

            attachments = section.attachments

            self.assertEqual(len(attachments), 4)

            self.assertEqual(attachments[0].identifier, 'RELEVE_NOTES')
            self.assertEqual(attachments[0].label, DocumentsCurriculum['RELEVE_NOTES'])
            self.assertEqual(attachments[0].uuids, experience.releve_notes)
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'TRADUCTION_RELEVE_NOTES')
            self.assertEqual(attachments[1].label, DocumentsCurriculum['TRADUCTION_RELEVE_NOTES'])
            self.assertEqual(attachments[1].uuids, experience.traduction_releve_notes)
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

            self.assertEqual(attachments[2].identifier, 'DIPLOME')
            self.assertEqual(attachments[2].label, DocumentsCurriculum['DIPLOME'])
            self.assertEqual(attachments[2].uuids, experience.diplome)
            self.assertTrue(attachments[2].required)
            self.assertTrue(attachments[2].readonly)

            self.assertEqual(attachments[3].identifier, 'TRADUCTION_DIPLOME')
            self.assertEqual(attachments[3].label, DocumentsCurriculum['TRADUCTION_DIPLOME'])
            self.assertEqual(attachments[3].uuids, experience.traduction_diplome)
            self.assertTrue(attachments[3].required)
            self.assertTrue(attachments[3].readonly)

    def test_curriculum_acad_experience_attachments_with_general_proposition_and_annual_transcript(self):
        experience = self.general_bachelor_context.curriculum.experiences_academiques[0]
        experience_year = experience.annees[0]
        with mock.patch.multiple(experience, type_releve_notes=TranscriptType.ONE_A_YEAR.name):
            section = get_educational_experience_section(
                self.general_bachelor_context,
                experience,
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, f'{experience_year.annee}.RELEVE_NOTES_ANNUEL')
            self.assertEqual(
                attachments[0].label,
                f'{DocumentsCurriculum["RELEVE_NOTES_ANNUEL"]} {experience_year.annee}-{experience_year.annee + 1}',
            )
            self.assertEqual(attachments[0].uuids, experience_year.releve_notes)
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DIPLOME')
            self.assertEqual(attachments[1].label, DocumentsCurriculum['DIPLOME'])
            self.assertEqual(attachments[1].uuids, experience.diplome)
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

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
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 4)

            self.assertEqual(attachments[0].identifier, f'{experience_year.annee}.RELEVE_NOTES_ANNUEL')
            self.assertEqual(
                attachments[0].label,
                f'{DocumentsCurriculum["RELEVE_NOTES_ANNUEL"]} {experience_year.annee}-{experience_year.annee + 1}',
            )
            self.assertEqual(attachments[0].uuids, experience_year.releve_notes)
            self.assertTrue(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, f'{experience_year.annee}.TRADUCTION_RELEVE_NOTES_ANNUEL')
            self.assertEqual(
                attachments[1].label,
                f'{DocumentsCurriculum["TRADUCTION_RELEVE_NOTES_ANNUEL"]} '
                f'{experience_year.annee}-{experience_year.annee + 1}',
            )
            self.assertEqual(attachments[1].uuids, experience_year.traduction_releve_notes)
            self.assertTrue(attachments[1].required)
            self.assertTrue(attachments[1].readonly)

            self.assertEqual(attachments[2].identifier, 'DIPLOME')
            self.assertEqual(attachments[2].label, DocumentsCurriculum['DIPLOME'])
            self.assertEqual(attachments[2].uuids, experience.diplome)
            self.assertTrue(attachments[2].required)
            self.assertTrue(attachments[2].readonly)

            self.assertEqual(attachments[3].identifier, 'TRADUCTION_DIPLOME')
            self.assertEqual(attachments[3].label, DocumentsCurriculum['TRADUCTION_DIPLOME'])
            self.assertEqual(attachments[3].uuids, experience.traduction_diplome)
            self.assertTrue(attachments[3].required)
            self.assertTrue(attachments[3].readonly)

    def test_curriculum_acad_experience_attachments_with_general_proposition_and_pending_result(self):
        experience = self.general_bachelor_context.curriculum.experiences_academiques[0]
        experience_year = experience.annees[0]
        with mock.patch.multiple(
            experience,
            type_releve_notes=TranscriptType.ONE_A_YEAR.name,
            regime_linguistique='BR',
        ):
            with mock.patch.multiple(experience.annees[0], resultat=Result.WAITING_RESULT.name):
                section = get_educational_experience_section(
                    self.general_bachelor_context,
                    experience,
                    False,
                )
                attachments = section.attachments

                self.assertEqual(len(attachments), 4)

                self.assertEqual(attachments[0].identifier, f'{experience_year.annee}.RELEVE_NOTES_ANNUEL')
                self.assertEqual(
                    attachments[0].label,
                    f'{DocumentsCurriculum["RELEVE_NOTES_ANNUEL"]} {experience_year.annee}-{experience_year.annee + 1}',
                )
                self.assertEqual(attachments[0].uuids, experience_year.releve_notes)
                self.assertFalse(attachments[0].required)
                self.assertTrue(attachments[0].readonly)

                self.assertEqual(attachments[1].identifier, f'{experience_year.annee}.TRADUCTION_RELEVE_NOTES_ANNUEL')
                self.assertEqual(
                    attachments[1].label,
                    f'{DocumentsCurriculum["TRADUCTION_RELEVE_NOTES_ANNUEL"]} '
                    f'{experience_year.annee}-{experience_year.annee + 1}',
                )
                self.assertEqual(attachments[1].uuids, experience_year.traduction_releve_notes)
                self.assertFalse(attachments[1].required)
                self.assertTrue(attachments[1].readonly)

                self.assertEqual(attachments[2].identifier, 'DIPLOME')
                self.assertEqual(attachments[2].label, DocumentsCurriculum['DIPLOME'])
                self.assertEqual(attachments[2].uuids, experience.diplome)
                self.assertTrue(attachments[2].required)
                self.assertTrue(attachments[2].readonly)

                self.assertEqual(attachments[3].identifier, 'TRADUCTION_DIPLOME')
                self.assertEqual(attachments[3].label, DocumentsCurriculum['TRADUCTION_DIPLOME'])
                self.assertEqual(attachments[3].uuids, experience.traduction_diplome)
                self.assertTrue(attachments[3].required)
                self.assertTrue(attachments[3].readonly)

    def test_curriculum_acad_experience_attachments_with_doctorate_proposition(self):
        experience = self.doctorate_context.curriculum.experiences_academiques[0]
        section = get_educational_experience_section(
            self.doctorate_context,
            experience,
            False,
        )
        attachments = section.attachments

        self.assertEqual(len(attachments), 3)

        self.assertEqual(attachments[0].identifier, 'RELEVE_NOTES')
        self.assertEqual(attachments[0].label, DocumentsCurriculum['RELEVE_NOTES'])
        self.assertEqual(attachments[0].uuids, experience.releve_notes)
        self.assertTrue(attachments[0].required)
        self.assertTrue(attachments[0].readonly)

        self.assertEqual(attachments[1].identifier, 'RESUME_MEMOIRE')
        self.assertEqual(attachments[1].label, DocumentsCurriculum['RESUME_MEMOIRE'])
        self.assertEqual(attachments[1].uuids, experience.resume_memoire)
        self.assertTrue(attachments[1].required)
        self.assertTrue(attachments[1].readonly)

        self.assertEqual(attachments[2].identifier, 'DIPLOME')
        self.assertEqual(attachments[2].label, DocumentsCurriculum['DIPLOME'])
        self.assertEqual(attachments[2].uuids, experience.diplome)
        self.assertTrue(attachments[2].required)
        self.assertTrue(attachments[2].readonly)

    def test_curriculum_non_academic_experience_attachments_with_continuing_proposition(self):
        section = get_non_educational_experience_section(
            self.continuing_context,
            self.continuing_context.curriculum.experiences_non_academiques[0],
            True,
        )
        self.assertEqual(len(section.attachments), 0)

    def test_curriculum_non_academic_experience_attachments_with_general_proposition_and_working_activity(self):
        experience = self.general_bachelor_context.curriculum.experiences_non_academiques[0]
        section = get_non_educational_experience_section(
            self.general_bachelor_context,
            experience,
            False,
        )
        attachments = section.attachments

        self.assertEqual(len(attachments), 1)

        self.assertEqual(attachments[0].identifier, 'CERTIFICAT_EXPERIENCE')
        self.assertEqual(attachments[0].label, CURRICULUM_ACTIVITY_LABEL.get(ActivityType.WORK.name))
        self.assertEqual(attachments[0].uuids, experience.certificat)
        self.assertFalse(attachments[0].required)
        self.assertTrue(attachments[0].readonly)

    def test_curriculum_non_academic_non_epc_experience_attachments_with_general_proposition_and_working_activity(self):
        experience = self.general_bachelor_context.curriculum.experiences_non_academiques[0]
        with mock.patch.multiple(experience, identifiant_externe=None):
            section = get_non_educational_experience_section(
                self.general_bachelor_context,
                experience,
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)

            self.assertEqual(attachments[0].identifier, 'CERTIFICAT_EXPERIENCE')
            self.assertFalse(attachments[0].readonly)

    def test_curriculum_non_academic_experience_attachments_with_general_proposition_and_other_activity(self):
        experience = self.general_bachelor_context.curriculum.experiences_non_academiques[0]
        with mock.patch.multiple(experience, type=ActivityType.OTHER.name):
            section = get_non_educational_experience_section(self.general_bachelor_context, experience, False)
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)

            self.assertEqual(attachments[0].identifier, 'CERTIFICAT_EXPERIENCE')
            self.assertEqual(attachments[0].label, CURRICULUM_ACTIVITY_LABEL.get(ActivityType.OTHER.name))
            self.assertEqual(attachments[0].uuids, experience.certificat)
            self.assertFalse(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

    def test_curriculum_non_academic_experience_attachments_with_doctorate_proposition_and_travel_activity(self):
        experience = self.doctorate_context.curriculum.experiences_non_academiques[0]
        with mock.patch.multiple(experience, type=ActivityType.LANGUAGE_TRAVEL.name):
            section = get_non_educational_experience_section(
                self.doctorate_context,
                experience,
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)

            self.assertEqual(attachments[0].identifier, 'CERTIFICAT_EXPERIENCE')
            self.assertEqual(attachments[0].label, CURRICULUM_ACTIVITY_LABEL.get(ActivityType.LANGUAGE_TRAVEL.name))
            self.assertEqual(attachments[0].uuids, experience.certificat)
            self.assertFalse(attachments[0].required)
            self.assertTrue(attachments[0].readonly)

    def test_specific_questions_attachments_with_continuing_proposition(self):
        with mock.patch.multiple(
            self.continuing_context.proposition,
            pays_nationalite_ue_candidat=True,
        ):
            section = get_specific_questions_section(
                self.continuing_context,
                self.specific_questions,
                True,
            )
            attachments = section.attachments
            document_question = self.specific_questions.get(Onglets.INFORMATIONS_ADDITIONNELLES.name)[1]

            self.assertEqual(len(attachments), 2)

            self.assertEqual(
                attachments[0].identifier,
                f'{IdentifiantBaseEmplacementDocument.QUESTION_SPECIFIQUE.name}.{document_question.uuid}',
            )
            self.assertEqual(attachments[0].label, document_question.label)
            self.assertEqual(attachments[0].uuids, self.admission.specific_question_answers[document_question.uuid])
            self.assertFalse(attachments[0].required)
            self.assertFalse(attachments[0].readonly)
            self.assertEqual(
                attachments[1].identifier,
                'ADDITIONAL_DOCUMENTS',
            )
            self.assertEqual(attachments[1].label, DocumentsQuestionsSpecifiques['ADDITIONAL_DOCUMENTS'])
            self.assertEqual(attachments[1].uuids, self.admission.additional_documents)
            self.assertFalse(attachments[1].required)
            self.assertFalse(attachments[1].readonly)

    def test_specific_questions_attachments_with_continuing_proposition_non_ue_candidate(self):
        with mock.patch.multiple(
            self.continuing_context.proposition,
            pays_nationalite_ue_candidat=False,
        ):
            section = get_specific_questions_section(
                self.continuing_context,
                self.empty_questions,
                False,
            )

            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'COPIE_TITRE_SEJOUR')
            self.assertEqual(attachments[0].label, DocumentsQuestionsSpecifiques['COPIE_TITRE_SEJOUR'])
            self.assertEqual(attachments[0].uuids, self.continuing_context.proposition.copie_titre_sejour)
            self.assertFalse(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

            self.assertEqual(
                attachments[1].identifier,
                'ADDITIONAL_DOCUMENTS',
            )
            self.assertEqual(attachments[1].label, DocumentsQuestionsSpecifiques['ADDITIONAL_DOCUMENTS'])
            self.assertEqual(attachments[1].uuids, self.admission.additional_documents)
            self.assertFalse(attachments[1].readonly)

    def test_specific_questions_attachments_with_general_proposition_and_reorientation(self):
        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            est_non_resident_au_sens_decret=False,
            est_reorientation_inscription_externe=True,
        ):
            section = get_specific_questions_section(
                self.general_bachelor_context,
                self.empty_questions,
                False,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'ATTESTATION_INSCRIPTION_REGULIERE')
            self.assertEqual(attachments[0].label, DocumentsQuestionsSpecifiques['ATTESTATION_INSCRIPTION_REGULIERE'])
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.proposition.attestation_inscription_reguliere,
            )
            self.assertTrue(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'ADDITIONAL_DOCUMENTS')
            self.assertEqual(attachments[1].label, DocumentsQuestionsSpecifiques['ADDITIONAL_DOCUMENTS'])
            self.assertEqual(attachments[1].uuids, self.admission.additional_documents)
            self.assertFalse(attachments[1].readonly)

            # The pool is not open...
            with freezegun.freeze_time('2023-10-1'):
                section = get_specific_questions_section(
                    self.general_bachelor_context,
                    self.empty_questions,
                    False,
                )
                attachments = section.attachments

                self.assertEqual(len(attachments), 1)
                self.assertEqual(attachments[0].identifier, 'ADDITIONAL_DOCUMENTS')

                # ...but we simulate its opening after the submission of the proposition to allow
                # the managers to manually choose the reorientation
                with mock.patch.multiple(
                    self.general_bachelor_context.proposition,
                    statut=ChoixStatutPropositionGenerale.CONFIRMEE.name,
                ):
                    section = get_specific_questions_section(
                        self.general_bachelor_context,
                        self.empty_questions,
                        False,
                    )
                    attachments = section.attachments

                    self.assertEqual(len(attachments), 2)

                    self.assertEqual(attachments[0].identifier, 'ATTESTATION_INSCRIPTION_REGULIERE')
                    self.assertEqual(
                        attachments[0].label,
                        DocumentsQuestionsSpecifiques['ATTESTATION_INSCRIPTION_REGULIERE'],
                    )
                    self.assertEqual(
                        attachments[0].uuids,
                        self.general_bachelor_context.proposition.attestation_inscription_reguliere,
                    )
                    self.assertTrue(attachments[0].required)
                    self.assertFalse(attachments[0].readonly)
                    self.assertEqual(attachments[1].identifier, 'ADDITIONAL_DOCUMENTS')

        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            est_non_resident_au_sens_decret=False,
            est_reorientation_inscription_externe=False,
        ):
            section = get_specific_questions_section(
                self.general_bachelor_context,
                self.empty_questions,
                False,
            )

            self.assertEqual(len(section.attachments), 1)
            self.assertEqual(section.attachments[0].identifier, 'ADDITIONAL_DOCUMENTS')

    def test_specific_questions_attachments_with_general_proposition_and_modification(self):
        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            est_non_resident_au_sens_decret=False,
            est_modification_inscription_externe=True,
        ):
            section = get_specific_questions_section(
                self.general_bachelor_context,
                self.empty_questions,
                False,
            )

            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(
                attachments[0].identifier,
                'FORMULAIRE_MODIFICATION_INSCRIPTION',
            )
            self.assertEqual(attachments[0].label, DocumentsQuestionsSpecifiques['FORMULAIRE_MODIFICATION_INSCRIPTION'])
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.proposition.formulaire_modification_inscription,
            )
            self.assertTrue(attachments[0].required)
            self.assertFalse(attachments[0].readonly)
            self.assertEqual(attachments[1].identifier, 'ADDITIONAL_DOCUMENTS')
            self.assertEqual(attachments[1].label, DocumentsQuestionsSpecifiques['ADDITIONAL_DOCUMENTS'])
            self.assertEqual(attachments[1].uuids, self.admission.additional_documents)
            self.assertFalse(attachments[1].readonly)

            # The pool is not open...
            with freezegun.freeze_time('2023-10-1'):
                section = get_specific_questions_section(
                    self.general_bachelor_context,
                    self.empty_questions,
                    False,
                )
                attachments = section.attachments

                self.assertEqual(len(attachments), 1)
                self.assertEqual(attachments[0].identifier, 'ADDITIONAL_DOCUMENTS')

                # ...but we simulate its opening after the submission of the proposition to allow
                # the managers to manually choose the reorientation
                with mock.patch.multiple(
                    self.general_bachelor_context.proposition,
                    statut=ChoixStatutPropositionGenerale.CONFIRMEE.name,
                ):
                    section = get_specific_questions_section(
                        self.general_bachelor_context,
                        self.empty_questions,
                        False,
                    )
                    attachments = section.attachments

                    self.assertEqual(len(attachments), 2)

                    self.assertEqual(attachments[0].identifier, 'FORMULAIRE_MODIFICATION_INSCRIPTION')
                    self.assertEqual(
                        attachments[0].label,
                        DocumentsQuestionsSpecifiques['FORMULAIRE_MODIFICATION_INSCRIPTION'],
                    )
                    self.assertEqual(
                        attachments[0].uuids,
                        self.general_bachelor_context.proposition.formulaire_modification_inscription,
                    )
                    self.assertTrue(attachments[0].required)
                    self.assertFalse(attachments[0].readonly)
                    self.assertEqual(attachments[1].identifier, 'ADDITIONAL_DOCUMENTS')

        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            est_non_resident_au_sens_decret=False,
            est_modification_inscription_externe=False,
        ):
            section = get_specific_questions_section(
                self.general_bachelor_context,
                self.empty_questions,
                False,
            )

            self.assertEqual(len(section.attachments), 1)
            self.assertEqual(section.attachments[0].identifier, 'ADDITIONAL_DOCUMENTS')

    def test_accounting_attachments_with_general_proposition_for_ue_candidate_and_french_frequented_institute(self):
        section = get_accounting_section(self.general_bachelor_context, True)
        attachments = section.attachments

        self.assertEqual(len(attachments), 1)

        self.assertEqual(attachments[0].identifier, 'ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT')
        self.assertEqual(
            attachments[0].label,
            DocumentsComptabilite['ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT']
            % {'academic_year': '2023-2024', 'names': 'Institut 1', 'count': 1},
        )
        self.assertEqual(
            attachments[0].uuids, self.general_bachelor_context.comptabilite.attestation_absence_dette_etablissement
        )
        self.assertTrue(attachments[0].required)

    def test_accounting_attachments_with_general_proposition_for_ue_child_staff_candidate(self):
        with mock.patch.multiple(self.general_bachelor_context.comptabilite, enfant_personnel=True):
            section = get_accounting_section(self.general_bachelor_context, False)

            attachments = section.attachments

            self.assertEqual(len(attachments), 2)

            self.assertEqual(attachments[0].identifier, 'ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT')
            self.assertEqual(
                attachments[0].label,
                DocumentsComptabilite['ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT']
                % {'academic_year': '2023-2024', 'names': 'Institut 1', 'count': 1},
            )
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.comptabilite.attestation_absence_dette_etablissement,
            )
            self.assertTrue(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'ATTESTATION_ENFANT_PERSONNEL')
            self.assertEqual(attachments[1].label, DocumentsComptabilite['ATTESTATION_ENFANT_PERSONNEL'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.comptabilite.attestation_enfant_personnel,
            )
            self.assertFalse(attachments[1].required)
            self.assertFalse(attachments[1].readonly)

    def test_accounting_attachments_with_general_proposition_for_not_ue_candidate(self):
        type_situation = TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name
        with mock.patch.multiple(
            self.general_bachelor_context.identification,
            pays_nationalite_europeen=False,
        ), mock.patch.multiple(
            self.general_bachelor_context.comptabilite,
            type_situation_assimilation=type_situation,
            sous_type_situation_assimilation_5=ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
            relation_parente=LienParente.PERE.name,
        ):
            section = get_accounting_section(self.general_bachelor_context, False)

            attachments = section.attachments

            self.assertEqual(len(attachments), 3)

            self.assertEqual(attachments[0].identifier, 'ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT')
            self.assertEqual(
                attachments[0].label,
                DocumentsComptabilite['ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT']
                % {'academic_year': '2023-2024', 'names': 'Institut 1', 'count': 1},
            )
            self.assertEqual(
                attachments[0].uuids,
                self.general_bachelor_context.comptabilite.attestation_absence_dette_etablissement,
            )
            self.assertTrue(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'COMPOSITION_MENAGE_ACTE_NAISSANCE')
            self.assertEqual(attachments[1].label, DocumentsComptabilite['COMPOSITION_MENAGE_ACTE_NAISSANCE'])
            self.assertEqual(
                attachments[1].uuids,
                self.general_bachelor_context.comptabilite.composition_menage_acte_naissance,
            )
            self.assertTrue(attachments[1].required)
            self.assertFalse(attachments[1].readonly)

            self.assertEqual(
                attachments[2].identifier,
                'ATTESTATION_CPAS_PARENT',
            )
            self.assertEqual(
                attachments[2].label,
                DocumentsComptabilite['ATTESTATION_CPAS_PARENT'] % {'person_concerned': 'votre père'},
            )
            self.assertEqual(
                attachments[2].uuids,
                self.general_bachelor_context.comptabilite.attestation_cpas_parent,
            )
            self.assertTrue(attachments[2].required)
            self.assertFalse(attachments[2].readonly)

    def test_languages_attachments_with_doctorate_proposition(self):
        section = get_languages_section(self.doctorate_context, True)
        attachments = section.attachments

        self.assertEqual(len(attachments), 2)

        self.assertEqual(
            attachments[0].identifier,
            f'{self.doctorate_context.connaissances_langues[0].langue}.CERTIFICAT_CONNAISSANCE_LANGUE',
        )
        self.assertEqual(
            attachments[0].label,
            f'{DocumentsConnaissancesLangues["CERTIFICAT_CONNAISSANCE_LANGUE"]} '
            f'{self.doctorate_context.connaissances_langues[0].nom_langue}',
        )
        self.assertEqual(
            attachments[0].uuids,
            self.doctorate_context.connaissances_langues[0].certificat,
        )
        self.assertFalse(attachments[0].required)
        self.assertFalse(attachments[0].readonly)

        self.assertEqual(
            attachments[1].identifier,
            f'{self.doctorate_context.connaissances_langues[1].langue}.CERTIFICAT_CONNAISSANCE_LANGUE',
        )
        self.assertEqual(
            attachments[1].label,
            f'{DocumentsConnaissancesLangues["CERTIFICAT_CONNAISSANCE_LANGUE"]} '
            f'{self.doctorate_context.connaissances_langues[1].nom_langue}',
        )
        self.assertEqual(
            attachments[1].uuids,
            self.doctorate_context.connaissances_langues[1].certificat,
        )
        self.assertFalse(attachments[1].required)
        self.assertFalse(attachments[1].readonly)

    def test_research_project_attachments_with_doctorate_proposition(self):
        section = get_research_project_section(self.doctorate_context, True)
        attachments = section.attachments

        self.assertEqual(len(attachments), 5)

        self.assertEqual(attachments[0].identifier, 'DOCUMENTS_PROJET')
        self.assertEqual(attachments[0].label, DocumentsProjetRecherche['DOCUMENTS_PROJET'])
        self.assertEqual(attachments[0].uuids, self.doctorate_context.proposition.documents_projet)
        self.assertTrue(attachments[0].required)
        self.assertFalse(attachments[0].readonly)

        self.assertEqual(attachments[1].identifier, 'PROPOSITION_PROGRAMME_DOCTORAL')
        self.assertEqual(attachments[1].label, DocumentsProjetRecherche['PROPOSITION_PROGRAMME_DOCTORAL'])
        self.assertEqual(attachments[1].uuids, self.doctorate_context.proposition.proposition_programme_doctoral)
        self.assertTrue(attachments[1].required)
        self.assertFalse(attachments[1].readonly)

        self.assertEqual(attachments[2].identifier, 'PROJET_FORMATION_COMPLEMENTAIRE')
        self.assertEqual(attachments[2].label, DocumentsProjetRecherche['PROJET_FORMATION_COMPLEMENTAIRE'])
        self.assertEqual(attachments[2].uuids, self.doctorate_context.proposition.projet_formation_complementaire)
        self.assertFalse(attachments[2].required)
        self.assertFalse(attachments[2].readonly)

        self.assertEqual(attachments[3].identifier, 'GRAPHE_GANTT')
        self.assertEqual(attachments[3].label, DocumentsProjetRecherche['GRAPHE_GANTT'])
        self.assertEqual(attachments[3].uuids, self.doctorate_context.proposition.graphe_gantt)
        self.assertFalse(attachments[3].required)
        self.assertFalse(attachments[3].readonly)

        self.assertEqual(attachments[4].identifier, 'LETTRES_RECOMMANDATION')
        self.assertEqual(attachments[4].label, DocumentsProjetRecherche['LETTRES_RECOMMANDATION'])
        self.assertEqual(attachments[4].uuids, self.doctorate_context.proposition.lettres_recommandation)
        self.assertFalse(attachments[4].required)
        self.assertFalse(attachments[4].readonly)

    def test_research_project_attachments_with_doctorate_proposition_and_search_scholarship(self):
        with mock.patch.multiple(
            self.doctorate_context.proposition,
            type_financement=ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
        ):
            section = get_research_project_section(self.doctorate_context, False)
            attachments = section.attachments

            self.assertEqual(len(attachments), 6)

            self.assertEqual(attachments[0].identifier, 'PREUVE_BOURSE')
            self.assertEqual(attachments[0].label, DocumentsProjetRecherche['PREUVE_BOURSE'])
            self.assertEqual(attachments[0].uuids, self.doctorate_context.proposition.bourse_preuve)
            self.assertFalse(attachments[0].required)
            self.assertFalse(attachments[0].readonly)

            self.assertEqual(attachments[1].identifier, 'DOCUMENTS_PROJET')
            self.assertEqual(attachments[1].label, DocumentsProjetRecherche['DOCUMENTS_PROJET'])
            self.assertEqual(attachments[1].uuids, self.doctorate_context.proposition.documents_projet)
            self.assertTrue(attachments[1].required)
            self.assertFalse(attachments[1].readonly)

            self.assertEqual(attachments[2].identifier, 'PROPOSITION_PROGRAMME_DOCTORAL')
            self.assertEqual(attachments[2].label, DocumentsProjetRecherche['PROPOSITION_PROGRAMME_DOCTORAL'])
            self.assertEqual(attachments[2].uuids, self.doctorate_context.proposition.proposition_programme_doctoral)
            self.assertTrue(attachments[2].required)
            self.assertFalse(attachments[2].readonly)

            self.assertEqual(attachments[3].identifier, 'PROJET_FORMATION_COMPLEMENTAIRE')
            self.assertEqual(attachments[3].label, DocumentsProjetRecherche['PROJET_FORMATION_COMPLEMENTAIRE'])
            self.assertEqual(attachments[3].uuids, self.doctorate_context.proposition.projet_formation_complementaire)
            self.assertFalse(attachments[3].required)
            self.assertFalse(attachments[3].readonly)

            self.assertEqual(attachments[4].identifier, 'GRAPHE_GANTT')
            self.assertEqual(attachments[4].label, DocumentsProjetRecherche['GRAPHE_GANTT'])
            self.assertEqual(attachments[4].uuids, self.doctorate_context.proposition.graphe_gantt)
            self.assertFalse(attachments[4].required)
            self.assertFalse(attachments[4].readonly)

            self.assertEqual(attachments[5].identifier, 'LETTRES_RECOMMANDATION')
            self.assertEqual(attachments[5].label, DocumentsProjetRecherche['LETTRES_RECOMMANDATION'])
            self.assertEqual(attachments[5].uuids, self.doctorate_context.proposition.lettres_recommandation)
            self.assertFalse(attachments[5].required)
            self.assertFalse(attachments[5].readonly)

    def test_cotutelle_attachments_with_doctorate_proposition_without_specified_cotutelle(self):
        with mock.patch.multiple(
            self.doctorate_context.groupe_supervision,
            cotutelle=None,
        ):
            section = get_cotutelle_section(self.doctorate_context, True)
            self.assertEqual(len(section.attachments), 0)

    def test_cotutelle_attachments_with_doctorate_proposition_with_no_cotutelle(self):
        with mock.patch.multiple(
            self.doctorate_context.groupe_supervision.cotutelle,
            cotutelle=False,
        ):
            section = get_cotutelle_section(self.doctorate_context, False)
            self.assertEqual(len(section.attachments), 0)

    def test_cotutelle_attachments_with_doctorate_proposition_with_specified_cotutelle(self):
        section = get_cotutelle_section(self.doctorate_context, False)
        attachments = section.attachments

        self.assertEqual(len(attachments), 3)

        self.assertEqual(attachments[0].identifier, 'DEMANDE_OUVERTURE')
        self.assertEqual(attachments[0].label, DocumentsCotutelle['DEMANDE_OUVERTURE'])
        self.assertEqual(attachments[0].uuids, self.doctorate_context.groupe_supervision.cotutelle.demande_ouverture)
        self.assertTrue(attachments[0].required)
        self.assertFalse(attachments[0].readonly)

        self.assertEqual(attachments[1].identifier, 'CONVENTION')
        self.assertEqual(attachments[1].label, DocumentsCotutelle['CONVENTION'])
        self.assertEqual(attachments[1].uuids, self.doctorate_context.groupe_supervision.cotutelle.convention)
        self.assertFalse(attachments[1].required)
        self.assertFalse(attachments[1].readonly)

        self.assertEqual(attachments[2].identifier, 'AUTRES_DOCUMENTS')
        self.assertEqual(attachments[2].label, DocumentsCotutelle['AUTRES_DOCUMENTS'])
        self.assertEqual(attachments[2].uuids, self.doctorate_context.groupe_supervision.cotutelle.autres_documents)
        self.assertFalse(attachments[2].required)
        self.assertFalse(attachments[2].readonly)

    def test_supervision_attachments_with_doctorate_proposition(self):
        section = get_supervision_section(self.doctorate_context, False)
        attachments = section.attachments
        signature_promoteur = self.doctorate_context.groupe_supervision.signatures_promoteurs[0]
        signature_membre_ca = self.doctorate_context.groupe_supervision.signatures_membres_CA[0]

        self.assertEqual(len(attachments), 2)

        self.assertEqual(attachments[0].identifier, f'{signature_promoteur.promoteur.uuid}.APPROBATION_PDF')
        self.assertEqual(
            attachments[0].label,
            f'{DocumentsSupervision["APPROBATION_PDF"]} '
            f'{signature_promoteur.promoteur.prenom} {signature_promoteur.promoteur.nom}',
        )
        self.assertEqual(attachments[0].uuids, signature_promoteur.pdf)
        self.assertFalse(attachments[0].required)
        self.assertFalse(attachments[0].readonly)

        self.assertEqual(attachments[1].identifier, f'{signature_membre_ca.membre_CA.uuid}.APPROBATION_PDF')
        self.assertEqual(
            attachments[1].label,
            f'{DocumentsSupervision["APPROBATION_PDF"]} '
            f'{signature_membre_ca.membre_CA.prenom} {signature_membre_ca.membre_CA.nom}',
        )
        self.assertEqual(attachments[1].uuids, signature_membre_ca.pdf)
        self.assertFalse(attachments[1].required)
        self.assertFalse(attachments[1].readonly)

    def test_authorization_attachments_with_doctorate_proposition(self):
        section = get_authorization_section(
            context=self.doctorate_context,
            load_content=False,
        )

        self.assertEqual(len(section.attachments), 0)

    def test_authorization_attachments_with_continuing_proposition(self):
        section = get_authorization_section(
            context=self.continuing_context,
            load_content=False,
        )

        self.assertEqual(len(section.attachments), 0)

    def test_authorization_attachments_with_general_proposition(self):
        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            certificat_autorisation_signe=[],
            visa_etudes_d=[],
        ):
            section = get_authorization_section(
                context=self.general_bachelor_context,
                load_content=False,
            )

            self.assertEqual(section.attachments, [])

        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            statut=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
            certificat_autorisation_signe=[],
            visa_etudes_d=[],
        ):
            section = get_authorization_section(
                context=self.general_bachelor_context,
                load_content=False,
            )

            self.assertEqual(len(section.attachments), 1)

            authorization_certificate = section.attachments[0]

            self.assertEqual(
                authorization_certificate.identifier,
                'AUTORISATION_PDF_SIGNEE',
            )
            self.assertEqual(
                authorization_certificate.label,
                DocumentsSuiteAutorisation['AUTORISATION_PDF_SIGNEE'],
            )
            self.assertEqual(
                authorization_certificate.uuids,
                self.general_bachelor_context.proposition.certificat_autorisation_signe,
            )

        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            statut=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
            certificat_autorisation_signe=[],
            visa_etudes_d=[],
            doit_fournir_visa_etudes=True,
        ):
            section = get_authorization_section(
                context=self.general_bachelor_context,
                load_content=False,
            )

            self.assertEqual(len(section.attachments), 2)

            self.assertEqual(
                section.attachments[0].identifier,
                'AUTORISATION_PDF_SIGNEE',
            )

            self.assertEqual(
                section.attachments[1].identifier,
                'VISA_ETUDES',
            )
            self.assertEqual(
                section.attachments[1].label,
                DocumentsSuiteAutorisation['VISA_ETUDES'],
            )
            self.assertEqual(section.attachments[1].uuids, self.general_bachelor_context.proposition.visa_etudes_d)

        with mock.patch.multiple(
            self.general_bachelor_context.proposition,
            statut=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
            certificat_autorisation_signe=[],
            visa_etudes_d=[],
            doit_fournir_visa_etudes=True,
            type=TypeDemande.INSCRIPTION.name,
        ):
            section = get_authorization_section(
                context=self.general_bachelor_context,
                load_content=False,
            )

            self.assertEqual(len(section.attachments), 0)

        section = get_authorization_section(
            context=self.general_bachelor_context,
            load_content=False,
        )

        self.assertEqual(len(section.attachments), 2)

    def test_requestable_free_documents_attachments(self):
        section = get_requestable_free_document_section(
            self.general_bachelor_context,
            self.specific_questions,
            False,
        )

        attachments = section.attachments
        self.assertEqual(len(attachments), 1)

        document_question = self.specific_questions.get(Onglets.DOCUMENTS.name)[1]
        self.assertEqual(attachments[0].identifier, document_question.uuid)
        self.assertEqual(attachments[0].label, document_question.label)
        self.assertEqual(attachments[0].uuids, self.admission.specific_question_answers[document_question.uuid])
        self.assertFalse(attachments[0].required)
        self.assertFalse(attachments[0].readonly)

    def test_training_choice_attachments(self):
        section = get_training_choice_section(
            self.continuing_context,
            self.specific_questions,
            True,
        )
        attachments = section.attachments
        document_question = self.specific_questions.get(Onglets.CHOIX_FORMATION.name)[1]

        self.assertEqual(len(attachments), 1)

        self.assertEqual(
            attachments[0].identifier,
            f'{IdentifiantBaseEmplacementDocument.QUESTION_SPECIFIQUE.name}.{document_question.uuid}',
        )
        self.assertEqual(attachments[0].label, document_question.label)
        self.assertEqual(attachments[0].uuids, self.admission.specific_question_answers[document_question.uuid])
        self.assertFalse(attachments[0].required)
        self.assertFalse(attachments[0].readonly)

        with mock.patch.multiple(document_question, requis=True):
            section = get_training_choice_section(
                self.continuing_context,
                self.specific_questions,
                True,
            )
            attachments = section.attachments

            self.assertEqual(len(attachments), 1)
            self.assertEqual(
                attachments[0].identifier,
                f'{IdentifiantBaseEmplacementDocument.QUESTION_SPECIFIQUE.name}.{document_question.uuid}',
            )

            self.assertTrue(attachments[0].required)
            self.assertFalse(attachments[0].readonly)
