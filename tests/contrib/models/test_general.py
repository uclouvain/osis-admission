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

import freezegun
from django.test import override_settings

from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.enums.emplacement_document import StatutReclamationEmplacementDocument
from admission.tests import TestCase
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from base.models.enums.education_group_types import TrainingType


@freezegun.freeze_time('2023-01-01')
@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class TestGeneralEducationAdmissionDocuments(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.auto_required_params = {
            'automatically_required': True,
            'last_action_at': '2023-01-01T00:00:00',
            'last_actor': '',
            'deadline_at': '',
            'reason': '',
            'requested_at': '',
            'status': 'A_RECLAMER',
            'type': 'NON_LIBRE',
            'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            'related_checklist_tab': '',
        }
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
            return_value={"name": "myfile", "mimetype": "application/pdf"},
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

        self.assertEqual(
            self.general_admission.requested_documents,
            {
                'CURRICULUM.CURRICULUM': self.auto_required_params,
            },
        )

        # Complete the missing field
        self.general_admission.curriculum = [uuid.uuid4()]
        self.general_admission.save()
        self.general_admission.update_requested_documents()
        self.general_admission.refresh_from_db()
        self.assertEqual(
            self.general_admission.requested_documents,
            {},
        )

    def test_update_requested_documents_with_existing_request_concerning_the_missing_field(self):
        # Simulate a manuel request on the missing field
        self.general_admission.requested_documents['CURRICULUM.CURRICULUM'] = self.manuel_required_params
        self.general_admission.save()
        self.general_admission.update_requested_documents()
        self.general_admission.refresh_from_db()

        # We just specify that this field is automatically required and keep the previous request data
        self.assertEqual(
            self.general_admission.requested_documents,
            {
                'CURRICULUM.CURRICULUM': {
                    **self.manuel_required_params,
                    'automatically_required': True,
                }
            },
        )

    def test_update_requested_documents_with_existing_request_concerning_other_field(self):
        # Simulate a manuel request on the missing field
        self.general_admission.requested_documents['IDENTIFICATION.CARTE_IDENTITE'] = self.manuel_required_params
        self.general_admission.save()
        self.general_admission.update_requested_documents()
        self.general_admission.refresh_from_db()

        # We keep the previous manuel request data
        self.assertEqual(
            self.general_admission.requested_documents,
            {
                'IDENTIFICATION.CARTE_IDENTITE': self.manuel_required_params,
                'CURRICULUM.CURRICULUM': self.auto_required_params,
            },
        )
