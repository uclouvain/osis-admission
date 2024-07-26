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

from unittest.mock import patch

import freezegun
from django.test import override_settings

from admission.ddd.admission.enums.emplacement_document import StatutReclamationEmplacementDocument
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
)
from admission.models import GeneralEducationAdmission
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    AdmissionEducationalValuatedExperiencesFactory,
    EducationalExperienceYearFactory,
)
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from base.models.enums.education_group_types import TrainingType
from base.tests import TestCaseWithQueriesAssertions


@freezegun.freeze_time('2023-01-01')
@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class TestGeneralEducationAdmissionDocuments(TestCaseWithQueriesAssertions):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.manuel_required_params = {
            'automatically_required': False,
            'last_action_at': '2023-01-01T00:00:00',
            'last_actor': '0123456',
            'deadline_at': '',
            'reason': 'My reason',
            'requested_at': '',
            'status': 'A_RECLAMER',
            'type': 'NON_LIBRE',
            'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT.name,
            'related_checklist_tab': '',
        }

    def setUp(self) -> None:
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", "mimetype": "application/pdf", "size": 1},
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
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=CompletePersonFactory(),
            curriculum=[],
            training=GeneralEducationTrainingFactory(
                education_group_type__name=TrainingType.MASTER_MC.name,
            ),
        )

    def test_update_requested_documents_with_no_existing_request(self):
        self.assertEqual(self.general_admission.requested_documents, {})

        self.general_admission.update_requested_documents()
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.requested_documents, {})

    def test_update_requested_documents_with_existing_requests(self):
        # Simulate documents requests
        experience = EducationalExperienceFactory(
            person=self.general_admission.candidate,
            obtained_diploma=True,
        )

        experience_year = EducationalExperienceYearFactory(
            educational_experience=experience,
        )

        valuation = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.general_admission,
            educationalexperience=experience,
        )

        # Unknown documents
        self.general_admission.requested_documents = {
            # Unknown documents
            f'CURRICULUM.IDENTIFIANT_PERSONNALISE_{document_type}': {
                **self.manuel_required_params,
                'type': document_type,
            }
            for document_type in [
                # Non-free documents -> must be deleted
                TypeEmplacementDocument.NON_LIBRE.name,
                # Other documents -> must be kept
                TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
                TypeEmplacementDocument.LIBRE_INTERNE_SIC.name,
                TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
                TypeEmplacementDocument.SYSTEME.name,
            ]
        }

        # Known non-free documents -> must be kept
        self.general_admission.requested_documents['CURRICULUM.CURRICULUM'] = self.manuel_required_params
        self.general_admission.requested_documents[
            f'CURRICULUM.{experience.uuid}.RELEVE_NOTES'
        ] = self.manuel_required_params

        self.general_admission.save()
        self.general_admission.update_requested_documents()
        self.general_admission.refresh_from_db()

        for document_identifier in [
            TypeEmplacementDocument.NON_LIBRE.name,
        ]:
            self.assertIsNone(
                self.general_admission.requested_documents.get(document_identifier),
                f'{document_identifier} must be deleted',
            )

        for document_identifier in [
            f'CURRICULUM.IDENTIFIANT_PERSONNALISE_{TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name}',
            f'CURRICULUM.IDENTIFIANT_PERSONNALISE_{TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name}',
            f'CURRICULUM.IDENTIFIANT_PERSONNALISE_{TypeEmplacementDocument.LIBRE_INTERNE_SIC.name}',
            f'CURRICULUM.IDENTIFIANT_PERSONNALISE_{TypeEmplacementDocument.LIBRE_INTERNE_FAC.name}',
            f'CURRICULUM.IDENTIFIANT_PERSONNALISE_{TypeEmplacementDocument.SYSTEME.name}',
        ] + [
            'CURRICULUM.CURRICULUM',
            f'CURRICULUM.{experience.uuid}.RELEVE_NOTES',
        ]:
            self.assertIsNotNone(
                self.general_admission.requested_documents.get(document_identifier),
                f'{document_identifier} must be kept',
            )

        # The experience is not valuated anymore so we don't want to keep the document
        valuation.delete()

        self.general_admission.update_requested_documents()

        self.general_admission.refresh_from_db()

        self.assertIsNone(self.general_admission.requested_documents.get(f'CURRICULUM.{experience.uuid}.RELEVE_NOTES'))
