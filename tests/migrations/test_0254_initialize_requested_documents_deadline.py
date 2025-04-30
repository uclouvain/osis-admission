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
import datetime

from django.test import TestCase

from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.migrations.utils.initialize_requested_documents_deadline import (
    initialize_requested_documents_deadline,
)
from admission.models import GeneralEducationAdmission
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory


class InitializeRequestedDocumentsDeadlineTestCase(TestCase):
    def test_with_no_admission_to_complete(self):
        initialize_requested_documents_deadline()

        admissions = GeneralEducationAdmission.objects.all()

        self.assertEqual(admissions.count(), 0)

    def test_with_no_requested_document(self):
        # No document at all
        first_admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
            requested_documents={},
            requested_documents_deadline=None,
        )

        initialize_requested_documents_deadline()

        first_admission.refresh_from_db()

        self.assertIsNone(first_admission.requested_documents_deadline)

        # No requested document
        first_admission.requested_documents = {
            'doc_1': {
                'last_action_at': datetime.datetime(2023, 1, 1),
                'deadline_at': datetime.date(2023, 1, 15),
                'status': StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION.name,
            },
        }
        first_admission.save()

        initialize_requested_documents_deadline()

        first_admission.refresh_from_db()

        self.assertIsNone(first_admission.requested_documents_deadline)

    def test_with_several_requested_documents(self):
        first_admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
            requested_documents={
                'doc_1': {
                    'last_action_at': datetime.datetime(2023, 1, 1),
                    'deadline_at': datetime.date(2023, 1, 15),
                    'status': StatutEmplacementDocument.RECLAME.name,
                },
                # Last updated and requested document -> deadline to use
                'doc_2': {
                    'last_action_at': datetime.datetime(2024, 1, 1),
                    'deadline_at': datetime.date(2023, 2, 15),
                    'status': StatutEmplacementDocument.RECLAME.name,
                },
                'doc_3': {
                    'last_action_at': datetime.datetime(2023, 1, 1),
                    'deadline_at': datetime.date(2023, 3, 15),
                    'status': StatutEmplacementDocument.RECLAME.name,
                },
                'doc_4': {
                    'last_action_at': datetime.datetime(2025, 1, 1),
                    'deadline_at': datetime.date(2023, 4, 15),
                    'status': StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION.name,
                },
            },
            requested_documents_deadline=None,
        )

        initialize_requested_documents_deadline()

        first_admission.refresh_from_db()

        self.assertEqual(first_admission.requested_documents_deadline, datetime.date(2023, 2, 15))
