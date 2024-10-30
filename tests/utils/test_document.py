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

import uuid
from unittest.mock import patch

from django.test import override_settings

from admission.constants import JPEG_MIME_TYPE, SUPPORTED_MIME_TYPES
from admission.models import GeneralEducationAdmission, ContinuingEducationAdmission, DoctorateAdmission
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.enums.emplacement_document import (
    IdentifiantBaseEmplacementDocument,
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    OngletsDemande,
)
from admission.ddd.admission.formation_generale.domain.model.enums import OngletsChecklist
from admission.infrastructure.utils import get_document_from_identifier, CORRESPONDANCE_CHAMPS_COMPTABILITE
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
    ProfessionalExperienceFactory,
)
from admission.tests.factories.form_item import DocumentAdmissionFormItemFactory, AdmissionFormItemInstantiationFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.language import LanguageKnowledgeFactory
from admission.tests.factories.secondary_studies import (
    BelgianHighSchoolDiplomaFactory,
    ForeignHighSchoolDiplomaFactory,
    HighSchoolDiplomaAlternativeFactory,
)
from admission.tests.factories.supervision import PromoterFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.tests import TestCaseWithQueriesAssertions
from reference.tests.factories.language import FrenchLanguageFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class TestGetDocumentFromIdentifier(TestCaseWithQueriesAssertions):
    def setUp(self) -> None:
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={
                "name": "myfile",
                "explicit_name": "My file",
                "author": "0123456",
                "mimetype": JPEG_MIME_TYPE,
                "size": 1,
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, tokens, __: tokens,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory()

    def test_get_document_from_invalid_identifier(self):
        self.assertIsNone(get_document_from_identifier(self.general_admission, 'foobar'))
        self.assertIsNone(get_document_from_identifier(self.general_admission, ''))

    def test_get_free_requestable_document(self):
        base_identifier = IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name

        item = AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(),
            admission=self.general_admission,
            academic_year=self.general_admission.determined_academic_year,
        )

        specific_question_uuid = str(item.form_item.uuid)

        sic_free_requestable_document_id = f'{base_identifier}.{specific_question_uuid}'

        self.general_admission.requested_documents[sic_free_requestable_document_id] = {
            'last_actor': '0123456789',
            'reason': 'My reason',
            'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
            'last_action_at': '2020-01-01T00:00:00',
            'status': StatutEmplacementDocument.RECLAME.name,
            'requested_at': '2020-01-01T00:00:00',
            'deadline_at': '2020-01-15',
            'automatically_required': False,
            'related_checklist_tab': OngletsChecklist.parcours_anterieur.name,
        }

        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]

        self.general_admission.save()

        # Too short identifier
        document = get_document_from_identifier(self.general_admission, base_identifier)
        self.assertIsNone(document)

        # Too long identifier
        document = get_document_from_identifier(self.general_admission, f'{sic_free_requestable_document_id}.11')
        self.assertIsNone(document)

        # Valid identifier
        document = get_document_from_identifier(self.general_admission, sic_free_requestable_document_id)
        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'specific_question_answers')
        self.assertEqual(document.uuids, self.general_admission.specific_question_answers[specific_question_uuid])
        self.assertEqual(document.type, TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name)
        self.assertEqual(document.requestable, True)
        self.assertEqual(document.specific_question_uuid, specific_question_uuid)
        self.assertEqual(document.status, StatutEmplacementDocument.RECLAME.name)
        self.assertEqual(document.reason, 'My reason')
        self.assertEqual(document.requested_at, '2020-01-01T00:00:00')
        self.assertEqual(document.deadline_at, '2020-01-15')
        self.assertEqual(document.last_action_at, '2020-01-01T00:00:00')
        self.assertEqual(document.last_actor, '0123456789')
        self.assertEqual(document.automatically_required, False)
        self.assertEqual(document.mimetypes, list(SUPPORTED_MIME_TYPES))
        self.assertEqual(document.label, 'Champ document')
        self.assertEqual(document.label_fr, 'Champ document')
        self.assertEqual(document.label_en, 'Document field')
        self.assertEqual(document.document_submitted_by, '0123456')
        self.assertEqual(document.related_checklist_tab, OngletsChecklist.parcours_anterieur.name)

    def test_get_non_free_requestable_document_in_a_specific_question(self):
        base_identifier = Onglets.CURRICULUM.name

        item = AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(),
            admission=self.general_admission,
            academic_year=self.general_admission.determined_academic_year,
            tab=base_identifier,
        )

        specific_question_uuid = str(item.form_item.uuid)

        document_id = (
            f'{base_identifier}.{IdentifiantBaseEmplacementDocument.QUESTION_SPECIFIQUE.name}.'
            f'{specific_question_uuid}'
        )

        # Already requested
        self.general_admission.requested_documents[document_id] = {
            'last_actor': '0123456789',
            'reason': 'My reason',
            'type': TypeEmplacementDocument.NON_LIBRE.name,
            'last_action_at': '2020-01-01T00:00:00',
            'status': StatutEmplacementDocument.RECLAME.name,
            'requested_at': '2020-01-01T00:00:00',
            'deadline_at': '2020-01-15',
            'automatically_required': False,
        }

        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]

        self.general_admission.save()

        # Invalid identifier
        document = get_document_from_identifier(self.general_admission, f'{document_id}.AA')
        self.assertIsNone(document)

        # Valid identifier
        document = get_document_from_identifier(self.general_admission, document_id)
        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'specific_question_answers')
        self.assertEqual(document.uuids, self.general_admission.specific_question_answers[specific_question_uuid])
        self.assertEqual(document.type, TypeEmplacementDocument.NON_LIBRE.name)
        self.assertEqual(document.requestable, True)
        self.assertEqual(document.specific_question_uuid, specific_question_uuid)
        self.assertEqual(document.status, StatutEmplacementDocument.RECLAME.name)
        self.assertEqual(document.reason, 'My reason')
        self.assertEqual(document.requested_at, '2020-01-01T00:00:00')
        self.assertEqual(document.deadline_at, '2020-01-15')
        self.assertEqual(document.last_action_at, '2020-01-01T00:00:00')
        self.assertEqual(document.last_actor, '0123456789')
        self.assertEqual(document.automatically_required, False)
        self.assertEqual(document.mimetypes, list(SUPPORTED_MIME_TYPES))
        self.assertEqual(document.label, 'Champ document')
        self.assertEqual(document.document_submitted_by, '0123456')

        # Not already requested
        self.general_admission.requested_documents.pop(document_id, None)
        self.general_admission.save()

        document = get_document_from_identifier(self.general_admission, document_id)
        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'specific_question_answers')
        self.assertEqual(document.uuids, self.general_admission.specific_question_answers[specific_question_uuid])
        self.assertEqual(document.type, TypeEmplacementDocument.NON_LIBRE.name)
        self.assertEqual(document.requestable, True)
        self.assertEqual(document.specific_question_uuid, specific_question_uuid)
        self.assertEqual(document.status, StatutEmplacementDocument.NON_ANALYSE.name)
        self.assertEqual(document.reason, '')
        self.assertEqual(document.requested_at, '')
        self.assertEqual(document.deadline_at, '')
        self.assertEqual(document.last_action_at, '')
        self.assertEqual(document.last_actor, '')
        self.assertEqual(document.automatically_required, False)
        self.assertEqual(document.mimetypes, list(SUPPORTED_MIME_TYPES))
        self.assertEqual(document.label, 'Champ document')
        self.assertEqual(document.document_submitted_by, '0123456')

        # Remove the specific question
        form_item = item.form_item
        item.delete()
        form_item.delete()

        document = get_document_from_identifier(self.general_admission, document_id)
        self.assertIsNone(document)

    def test_get_free_non_requestable_document(self):
        base_identifier = IdentifiantBaseEmplacementDocument.LIBRE_GESTIONNAIRE.name

        file_uuid = uuid.uuid4()

        # Unknown identifier
        document = get_document_from_identifier(self.general_admission, f'{base_identifier}.{file_uuid}')
        self.assertIsNone(document)

        # TypeEmplacementDocument.LIBRE_INTERNE_SIC
        self.general_admission.uclouvain_sic_documents = [file_uuid]
        self.general_admission.save()

        document = get_document_from_identifier(self.general_admission, f'{base_identifier}.{file_uuid}')
        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'uclouvain_sic_documents')
        self.assertEqual(document.uuids, [file_uuid])
        self.assertEqual(document.type, TypeEmplacementDocument.LIBRE_INTERNE_SIC.name)
        self.assertEqual(document.requestable, False)
        self.assertEqual(document.specific_question_uuid, '')
        self.assertEqual(document.status, StatutEmplacementDocument.VALIDE.name)
        self.assertEqual(document.reason, '')
        self.assertEqual(document.requested_at, '')
        self.assertEqual(document.deadline_at, '')
        self.assertEqual(document.last_action_at, '')
        self.assertEqual(document.last_actor, '0123456')
        self.assertEqual(document.automatically_required, False)
        self.assertEqual(document.mimetypes, [JPEG_MIME_TYPE])
        self.assertEqual(document.label, 'My file')
        self.assertEqual(document.document_submitted_by, '0123456')

        # TypeEmplacementDocument.LIBRE_INTERNE_FAC
        self.general_admission.uclouvain_sic_documents = []
        self.general_admission.uclouvain_fac_documents = [file_uuid]
        self.general_admission.save()

        document = get_document_from_identifier(self.general_admission, f'{base_identifier}.{file_uuid}')
        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'uclouvain_fac_documents')
        self.assertEqual(document.uuids, [file_uuid])
        self.assertEqual(document.type, TypeEmplacementDocument.LIBRE_INTERNE_FAC.name)
        self.assertEqual(document.requestable, False)
        self.assertEqual(document.specific_question_uuid, '')
        self.assertEqual(document.status, StatutEmplacementDocument.VALIDE.name)
        self.assertEqual(document.reason, '')
        self.assertEqual(document.requested_at, '')
        self.assertEqual(document.deadline_at, '')
        self.assertEqual(document.last_action_at, '')
        self.assertEqual(document.last_actor, '0123456')
        self.assertEqual(document.automatically_required, False)
        self.assertEqual(document.mimetypes, [JPEG_MIME_TYPE])
        self.assertEqual(document.label, 'My file')
        self.assertEqual(document.document_submitted_by, '0123456')

    def test_get_system_document(self):
        base_identifier = IdentifiantBaseEmplacementDocument.SYSTEME.name

        # Invalid identifier
        document = get_document_from_identifier(self.general_admission, f'{base_identifier}.UNKNOWN')
        self.assertIsNone(document)

        document = get_document_from_identifier(self.general_admission, f'{base_identifier}.DOSSIER_ANALYSE.TOO_LONG')
        self.assertIsNone(document)

        # PDF recap
        file_uuid = uuid.uuid4()
        self.general_admission.pdf_recap = [file_uuid]
        self.general_admission.save()
        document = get_document_from_identifier(self.general_admission, f'{base_identifier}.DOSSIER_ANALYSE')

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'pdf_recap')
        self.assertEqual(document.uuids, [file_uuid])
        self.assertEqual(document.type, TypeEmplacementDocument.SYSTEME.name)
        self.assertEqual(document.requestable, False)
        self.assertEqual(document.specific_question_uuid, '')
        self.assertEqual(document.status, StatutEmplacementDocument.VALIDE.name)
        self.assertEqual(document.reason, '')
        self.assertEqual(document.requested_at, '')
        self.assertEqual(document.deadline_at, '')
        self.assertEqual(document.last_action_at, '')
        self.assertEqual(document.last_actor, '')
        self.assertEqual(document.automatically_required, False)
        self.assertEqual(document.mimetypes, list(SUPPORTED_MIME_TYPES))
        self.assertEqual(document.label, '')
        self.assertEqual(document.document_submitted_by, '0123456')

        # Faculty approval decision document
        file_uuid = uuid.uuid4()
        self.general_admission.fac_approval_certificate = [file_uuid]
        self.general_admission.save()
        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.ATTESTATION_ACCORD_FACULTAIRE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'fac_approval_certificate')
        self.assertEqual(document.mimetypes, [PDF_MIME_TYPE])

        # Faculty refusal decision document
        file_uuid = uuid.uuid4()
        self.general_admission.fac_refusal_certificate = [file_uuid]
        self.general_admission.save()
        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.ATTESTATION_REFUS_FACULTAIRE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'fac_refusal_certificate')
        self.assertEqual(document.mimetypes, [PDF_MIME_TYPE])

    def test_get_non_free_identification_document(self):
        base_identifier = OngletsDemande.IDENTIFICATION.name

        # passport
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.passport = [file_uuid]
        self.general_admission.save()

        document = get_document_from_identifier(self.general_admission, f'{base_identifier}.PASSEPORT')

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate)
        self.assertEqual(document.field, 'passport')
        self.assertEqual(document.uuids, [file_uuid])
        self.assertEqual(document.type, TypeEmplacementDocument.NON_LIBRE.name)
        self.assertEqual(document.requestable, True)
        self.assertEqual(document.specific_question_uuid, '')
        self.assertEqual(document.status, StatutEmplacementDocument.NON_ANALYSE.name)
        self.assertEqual(document.reason, '')
        self.assertEqual(document.requested_at, '')
        self.assertEqual(document.deadline_at, '')
        self.assertEqual(document.last_action_at, '')
        self.assertEqual(document.last_actor, '')
        self.assertEqual(document.automatically_required, False)
        self.assertCountEqual(document.mimetypes, list(SUPPORTED_MIME_TYPES))
        self.assertEqual(document.label, '')
        self.assertEqual(document.document_submitted_by, '0123456')

        # id card
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.id_card = [file_uuid]
        self.general_admission.save()

        document = get_document_from_identifier(self.general_admission, f'{base_identifier}.CARTE_IDENTITE')

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate)
        self.assertEqual(document.field, 'id_card')
        self.assertEqual(document.uuids, [file_uuid])

        # id photo
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.id_photo = [file_uuid]
        self.general_admission.save()

        document = get_document_from_identifier(self.general_admission, f'{base_identifier}.PHOTO_IDENTITE')

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate)
        self.assertEqual(document.field, 'id_photo')
        self.assertEqual(document.uuids, [file_uuid])

    def test_get_non_free_secondary_studies_document(self):
        base_identifier = OngletsDemande.ETUDES_SECONDAIRES.name

        # Belgian high school

        document = get_document_from_identifier(self.general_admission, f'{base_identifier}.DIPLOME_BELGE_DIPLOME')
        self.assertIsNone(document)

        BelgianHighSchoolDiplomaFactory(person=self.general_admission.candidate)

        # diploma
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.belgianhighschooldiploma.high_school_diploma = [file_uuid]
        self.general_admission.candidate.belgianhighschooldiploma.save()

        document = get_document_from_identifier(self.general_admission, f'{base_identifier}.DIPLOME_BELGE_DIPLOME')

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate.belgianhighschooldiploma)
        self.assertEqual(document.field, 'high_school_diploma')
        self.assertEqual(document.uuids, [file_uuid])

        # Foreign high school

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE',
        )
        self.assertIsNone(document)

        ForeignHighSchoolDiplomaFactory(person=self.general_admission.candidate)

        # final equivalence decision ue
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.foreignhighschooldiploma.final_equivalence_decision_ue = [file_uuid]
        self.general_admission.candidate.foreignhighschooldiploma.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate.foreignhighschooldiploma)
        self.assertEqual(document.field, 'final_equivalence_decision_ue')
        self.assertEqual(document.uuids, [file_uuid])

        # equivalence decision proof
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.foreignhighschooldiploma.equivalence_decision_proof = [file_uuid]
        self.general_admission.candidate.foreignhighschooldiploma.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate.foreignhighschooldiploma)
        self.assertEqual(document.field, 'equivalence_decision_proof')
        self.assertEqual(document.uuids, [file_uuid])

        # final equivalence decision not ue
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.foreignhighschooldiploma.final_equivalence_decision_not_ue = [file_uuid]
        self.general_admission.candidate.foreignhighschooldiploma.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate.foreignhighschooldiploma)
        self.assertEqual(document.field, 'final_equivalence_decision_not_ue')
        self.assertEqual(document.uuids, [file_uuid])

        # high school diploma
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.foreignhighschooldiploma.high_school_diploma = [file_uuid]
        self.general_admission.candidate.foreignhighschooldiploma.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.DIPLOME_ETRANGER_DIPLOME',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate.foreignhighschooldiploma)
        self.assertEqual(document.field, 'high_school_diploma')
        self.assertEqual(document.uuids, [file_uuid])

        # high school diploma translation
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.foreignhighschooldiploma.high_school_diploma_translation = [file_uuid]
        self.general_admission.candidate.foreignhighschooldiploma.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.DIPLOME_ETRANGER_TRADUCTION_DIPLOME',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate.foreignhighschooldiploma)
        self.assertEqual(document.field, 'high_school_diploma_translation')
        self.assertEqual(document.uuids, [file_uuid])

        # high school transcript
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.foreignhighschooldiploma.high_school_transcript = [file_uuid]
        self.general_admission.candidate.foreignhighschooldiploma.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.DIPLOME_ETRANGER_RELEVE_NOTES',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate.foreignhighschooldiploma)
        self.assertEqual(document.field, 'high_school_transcript')
        self.assertEqual(document.uuids, [file_uuid])

        # high school transcript translation
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.foreignhighschooldiploma.high_school_transcript_translation = [file_uuid]
        self.general_admission.candidate.foreignhighschooldiploma.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate.foreignhighschooldiploma)
        self.assertEqual(document.field, 'high_school_transcript_translation')
        self.assertEqual(document.uuids, [file_uuid])

        # High school diploma alternative
        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE',
        )

        self.assertIsNone(document)

        HighSchoolDiplomaAlternativeFactory(person=self.general_admission.candidate)

        # first cycle admission exam
        file_uuid = uuid.uuid4()
        self.general_admission.candidate.highschooldiplomaalternative.first_cycle_admission_exam = [file_uuid]
        self.general_admission.candidate.foreignhighschooldiploma.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission.candidate.highschooldiplomaalternative)
        self.assertEqual(document.field, 'first_cycle_admission_exam')
        self.assertEqual(document.uuids, [file_uuid])

    def test_get_non_free_language_document(self):
        base_identifier = OngletsDemande.LANGUES.name

        # Invalid identifier
        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.CERTIFICAT_CONNAISSANCE_LANGUE',
        )
        self.assertIsNone(document)

        # Valid identifier
        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.FR.CERTIFICAT_CONNAISSANCE_LANGUE',
        )

        self.assertIsNone(document)

        language_knowledge = LanguageKnowledgeFactory(
            person=self.general_admission.candidate,
            language=FrenchLanguageFactory(),
        )

        # certificate
        file_uuid = uuid.uuid4()
        language_knowledge.certificate = [file_uuid]
        language_knowledge.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.FR.CERTIFICAT_CONNAISSANCE_LANGUE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, language_knowledge)
        self.assertEqual(document.field, 'certificate')
        self.assertEqual(document.uuids, [file_uuid])

    def test_get_non_free_curriculum_document(self):
        base_identifier = OngletsDemande.CURRICULUM.name

        # diploma equivalence
        file_uuid = uuid.uuid4()
        self.general_admission.diploma_equivalence = [file_uuid]
        self.general_admission.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.DIPLOME_EQUIVALENCE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'diploma_equivalence')
        self.assertEqual(document.uuids, [file_uuid])

        # curriculum
        file_uuid = uuid.uuid4()
        self.general_admission.curriculum = [file_uuid]
        self.general_admission.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.CURRICULUM',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'curriculum')
        self.assertEqual(document.uuids, [file_uuid])

        # Academic experience
        academic_experience = EducationalExperienceFactory(person=self.general_admission.candidate)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.RELEVE_NOTES',
        )
        self.assertIsNone(document)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{uuid.uuid4()}.RELEVE_NOTES',
        )
        self.assertIsNone(document)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{academic_experience.uuid}.RELEVE_NOTES',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, academic_experience)
        self.assertEqual(document.field, 'transcript')
        self.assertEqual(document.uuids, academic_experience.transcript)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{academic_experience.uuid}.TRADUCTION_RELEVE_NOTES',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, academic_experience)
        self.assertEqual(document.field, 'transcript_translation')
        self.assertEqual(document.uuids, academic_experience.transcript_translation)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{academic_experience.uuid}.RESUME_MEMOIRE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, academic_experience)
        self.assertEqual(document.field, 'dissertation_summary')
        self.assertEqual(document.uuids, academic_experience.dissertation_summary)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{academic_experience.uuid}.DIPLOME',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, academic_experience)
        self.assertEqual(document.field, 'graduate_degree')
        self.assertEqual(document.uuids, academic_experience.graduate_degree)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{academic_experience.uuid}.TRADUCTION_DIPLOME',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, academic_experience)
        self.assertEqual(document.field, 'graduate_degree_translation')
        self.assertEqual(document.uuids, academic_experience.graduate_degree_translation)

        academic_experience_year = EducationalExperienceYearFactory(
            educational_experience=academic_experience,
        )

        # Year missing
        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{academic_experience.uuid}.RELEVE_NOTES_ANNUEL',
        )
        self.assertIsNone(document)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{academic_experience.uuid}.{1900}.RELEVE_NOTES_ANNUEL',
        )

        self.assertIsNone(document)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{academic_experience.uuid}.'
            f'{academic_experience_year.academic_year.year}.RELEVE_NOTES_ANNUEL',
        )
        self.assertIsNotNone(document)
        self.assertEqual(document.obj, academic_experience_year)
        self.assertEqual(document.field, 'transcript')
        self.assertEqual(document.uuids, academic_experience_year.transcript)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{academic_experience.uuid}.'
            f'{academic_experience_year.academic_year.year}.TRADUCTION_RELEVE_NOTES_ANNUEL',
        )
        self.assertIsNotNone(document)
        self.assertEqual(document.obj, academic_experience_year)
        self.assertEqual(document.field, 'transcript_translation')
        self.assertEqual(document.uuids, academic_experience_year.transcript_translation)

        # Professional experience
        experience = ProfessionalExperienceFactory(person=self.general_admission.candidate)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{uuid.uuid4()}.CERTIFICAT_EXPERIENCE',
        )

        self.assertIsNone(document)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.CERTIFICAT_EXPERIENCE',
        )

        self.assertIsNone(document)

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.{experience.uuid}.CERTIFICAT_EXPERIENCE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, experience)
        self.assertEqual(document.field, 'certificate')
        self.assertEqual(document.uuids, experience.certificate)

    def test_get_non_free_additional_information_document(self):
        base_identifier = OngletsDemande.INFORMATIONS_ADDITIONNELLES.name

        # residence permit
        file_uuid = uuid.uuid4()
        continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory()
        continuing_admission.residence_permit = [file_uuid]
        continuing_admission.save()

        document = get_document_from_identifier(
            continuing_admission,
            f'{base_identifier}.COPIE_TITRE_SEJOUR',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, continuing_admission)
        self.assertEqual(document.field, 'residence_permit')
        self.assertEqual(document.uuids, [file_uuid])

        # regular registration proof
        file_uuid = uuid.uuid4()
        self.general_admission.regular_registration_proof = [file_uuid]
        self.general_admission.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.ATTESTATION_INSCRIPTION_REGULIERE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'regular_registration_proof')
        self.assertEqual(document.uuids, [file_uuid])

        # registration change form
        file_uuid = uuid.uuid4()
        self.general_admission.registration_change_form = [file_uuid]
        self.general_admission.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.FORMULAIRE_MODIFICATION_INSCRIPTION',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'registration_change_form')
        self.assertEqual(document.uuids, [file_uuid])

        # additional documents
        file_uuid = uuid.uuid4()
        self.general_admission.additional_documents = [file_uuid]
        self.general_admission.save()

        document = get_document_from_identifier(
            self.general_admission,
            f'{base_identifier}.ADDITIONAL_DOCUMENTS',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, self.general_admission)
        self.assertEqual(document.field, 'additional_documents')
        self.assertEqual(document.uuids, [file_uuid])

    def test_get_non_free_additional_accounting_document(self):
        base_identifier = OngletsDemande.COMPTABILITE.name

        # Update the accounting object
        for field_name in CORRESPONDANCE_CHAMPS_COMPTABILITE.values():
            setattr(self.general_admission.accounting, field_name, [uuid.uuid4()])

        self.general_admission.accounting.save()

        for identifier, field_name in CORRESPONDANCE_CHAMPS_COMPTABILITE.items():
            document = get_document_from_identifier(
                self.general_admission,
                f'{base_identifier}.{identifier}',
            )

            self.assertIsNotNone(document)
            self.assertEqual(document.obj, self.general_admission.accounting)
            self.assertEqual(document.field, field_name)
            self.assertEqual(document.uuids, getattr(self.general_admission.accounting, field_name))

    def test_get_non_free_doctorate_project_document(self):
        base_identifier = OngletsDemande.PROJET.name

        doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory()

        # scholarship proof
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.PREUVE_BOURSE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, doctorate_admission)
        self.assertEqual(document.field, 'scholarship_proof')
        self.assertEqual(document.uuids, doctorate_admission.scholarship_proof)

        # project document
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.DOCUMENTS_PROJET',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, doctorate_admission)
        self.assertEqual(document.field, 'project_document')
        self.assertEqual(document.uuids, doctorate_admission.project_document)

        # program proposition
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.PROPOSITION_PROGRAMME_DOCTORAL',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, doctorate_admission)
        self.assertEqual(document.field, 'program_proposition')
        self.assertEqual(document.uuids, doctorate_admission.program_proposition)

        # additional training project
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.PROJET_FORMATION_COMPLEMENTAIRE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, doctorate_admission)
        self.assertEqual(document.field, 'additional_training_project')
        self.assertEqual(document.uuids, doctorate_admission.additional_training_project)

        # gantt graph
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.GRAPHE_GANTT',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, doctorate_admission)
        self.assertEqual(document.field, 'gantt_graph')
        self.assertEqual(document.uuids, doctorate_admission.gantt_graph)

        # recommandation letters
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.LETTRES_RECOMMANDATION',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, doctorate_admission)
        self.assertEqual(document.field, 'recommendation_letters')
        self.assertEqual(document.uuids, doctorate_admission.recommendation_letters)

    def test_get_non_free_doctorate_cotutelle_document(self):
        base_identifier = OngletsDemande.COTUTELLE.name

        doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory()

        # cotutelle opening request
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.DEMANDE_OUVERTURE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, doctorate_admission)
        self.assertEqual(document.field, 'cotutelle_opening_request')
        self.assertEqual(document.uuids, doctorate_admission.cotutelle_opening_request)

        # cotutelle convention
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.CONVENTION',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, doctorate_admission)
        self.assertEqual(document.field, 'cotutelle_convention')
        self.assertEqual(document.uuids, doctorate_admission.cotutelle_convention)

        # cotutelle other documents
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.AUTRES_DOCUMENTS',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, doctorate_admission)
        self.assertEqual(document.field, 'cotutelle_other_documents')
        self.assertEqual(document.uuids, doctorate_admission.cotutelle_other_documents)

    def test_get_authorization_document(self):
        base_identifier = OngletsDemande.SUITE_AUTORISATION.name

        general_admission = GeneralEducationAdmissionFactory(
            student_visa_d=[uuid.uuid4()],
            signed_enrollment_authorization=[uuid.uuid4()],
        )

        # Bad identifier
        document = get_document_from_identifier(
            general_admission,
            f'{base_identifier}.UNKNOWN',
        )

        self.assertIsNone(document)

        # Valid identifier

        # student visa d
        document = get_document_from_identifier(
            general_admission,
            f'{base_identifier}.VISA_ETUDES',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, general_admission)
        self.assertEqual(document.field, 'student_visa_d')
        self.assertEqual(document.uuids, general_admission.student_visa_d)

        # signed enrollment authorization
        document = get_document_from_identifier(
            general_admission,
            f'{base_identifier}.AUTORISATION_PDF_SIGNEE',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, general_admission)
        self.assertEqual(document.field, 'signed_enrollment_authorization')
        self.assertEqual(document.uuids, general_admission.signed_enrollment_authorization)

    def test_get_non_free_doctorate_supervision_document(self):
        base_identifier = OngletsDemande.SUPERVISION.name

        promoter = PromoterFactory(
            actor_ptr__person__first_name="Joe",
            pdf_from_candidate=[uuid.uuid4()],
        )

        doctorate_admission = DoctorateAdmissionFactory(
            supervision_group=promoter.actor_ptr.process,
        )

        # Bad identifier
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.APPROBATION_PDF',
        )

        self.assertIsNone(document)

        # Unknown actor
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.{uuid.uuid4()}.APPROBATION_PDF',
        )

        self.assertIsNone(document)

        # Valid identifier
        document = get_document_from_identifier(
            doctorate_admission,
            f'{base_identifier}.{promoter.uuid}.APPROBATION_PDF',
        )

        self.assertIsNotNone(document)
        self.assertEqual(document.obj, promoter)
        self.assertEqual(document.field, 'pdf_from_candidate')
        self.assertEqual(document.uuids, promoter.pdf_from_candidate)
