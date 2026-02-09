# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from osis_notification.models import EmailNotification

from admission.auth.scope import Scope
from admission.calendar.admission_calendar import SIGLES_WITH_QUOTA
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.models import GeneralEducationAdmission
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import CentralManagerRoleFactory
from base.tests.factories.entity import EntityWithVersionFactory
from program_management.business.xls_customized import management_entity


@freezegun.freeze_time('2026-01-01')
class SpecificiteContingenteNotificationViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.training = GeneralEducationTrainingFactory(
            management_entity=EntityWithVersionFactory(),
            academic_year__year=2026,
            acronym=SIGLES_WITH_QUOTA[1],
        )

        cls.user = CentralManagerRoleFactory(
            entity=cls.training.management_entity,
            scopes=[Scope.CONTINGENTE_NON_RESIDENT.name],
        ).person.user

        AdmissionAcademicCalendarFactory.produce_all_required()

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            is_non_resident=True,
            ares_application_number='ARES_NUMBER',
        )
        cls.url = resolve_url(
            'admission:general-education:contingente-notification',
            uuid=cls.general_admission.uuid,
        )

    def setUp(self) -> None:
        self.file_uuid = uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')

        self.confirm_remote_upload_patcher = mock.patch('osis_document_components.services.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = str(self.file_uuid)
        self.addCleanup(self.confirm_remote_upload_patcher.stop)

        self.confirm_several_remote_upload_patcher = mock.patch(
            'osis_document_components.fields.FileField._confirm_multiple_upload'
        )
        patched = self.confirm_several_remote_upload_patcher.start()
        patched.side_effect = lambda _, value, __: [str(self.file_uuid)] if value else []
        self.addCleanup(self.confirm_several_remote_upload_patcher.stop)

        self.get_remote_metadata_patcher = mock.patch('osis_document_components.services.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf", "size": 1, "mimetype": "application/pdf"}
        self.addCleanup(self.get_remote_metadata_patcher.stop)

        self.get_several_remote_metadata_patcher = mock.patch(
            'osis_document_components.services.get_several_remote_metadata'
        )
        patched = self.get_several_remote_metadata_patcher.start()
        patched.return_value = {"foo": {"name": "test.pdf", "size": 1, "mimetype": "application/pdf"}}
        self.addCleanup(self.get_several_remote_metadata_patcher.stop)

        self.get_remote_token_patcher = mock.patch('osis_document_components.services.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'foobar'
        self.addCleanup(self.get_remote_token_patcher.stop)

        self.get_remote_tokens_patcher = mock.patch('osis_document_components.services.get_remote_tokens')
        patched = self.get_remote_tokens_patcher.start()
        patched.return_value = {'foo': 'foobar'}
        self.addCleanup(self.get_remote_tokens_patcher.stop)

        self.save_raw_content_remotely_patcher = mock.patch(
            'osis_document_components.services.save_raw_content_remotely'
        )
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'
        self.addCleanup(self.save_raw_content_remotely_patcher.stop)

        patcher = mock.patch('admission.exports.utils.change_remote_metadata')
        self.change_remote_metadata_patcher = patcher.start()
        self.change_remote_metadata_patcher.return_value = 'a-token'
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'admission.infrastructure.admission.formation_generale.domain.service.contingente.get_remote_token'
        )
        patched = patcher.start()
        patched.return_value = 'foobar'
        self.addCleanup(patcher.stop)

        # Mock weasyprint
        patcher = mock.patch(
            'admission.exports.utils.get_pdf_from_template',
            return_value=b'some content',
        )
        self.get_pdf_from_template_patcher = patcher.start()
        self.addCleanup(patcher.stop)

    def test_post(self):
        self.client.force_login(user=self.user)

        response = self.client.post(
            self.url,
            data={
                'contingente-notification-subject': 'subject',
                'contingente-notification-body': 'body',
            },
            headers={'HX-Request': "true"},
        )

        self.assertEqual(response.status_code, 200)
        self.general_admission.refresh_from_db()
        self.assertTrue(self.general_admission.non_resident_limited_enrolment_acceptance_file)
        self.assertEqual(EmailNotification.objects.count(), 1)
        email_notification: EmailNotification = EmailNotification.objects.first()
        self.assertEqual(email_notification.person, self.general_admission.candidate)
