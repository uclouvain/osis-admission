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

import uuid
from unittest import mock

from django.test import TestCase, override_settings


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class SicPatchMixin(TestCase):
    def setUp(self) -> None:
        self.file_uuid = uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')

        self.confirm_remote_upload_patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = str(self.file_uuid)
        self.addCleanup(self.confirm_remote_upload_patcher.stop)

        self.confirm_several_remote_upload_patcher = mock.patch(
            'osis_document.contrib.fields.FileField._confirm_multiple_upload'
        )
        patched = self.confirm_several_remote_upload_patcher.start()
        patched.side_effect = lambda _, value, __: [str(self.file_uuid)] if value else []
        self.addCleanup(self.confirm_several_remote_upload_patcher.stop)

        self.get_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf", "size": 1, "mimetype": "application/pdf"}
        self.addCleanup(self.get_remote_metadata_patcher.stop)

        self.get_several_remote_metadata_patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        patched = self.get_several_remote_metadata_patcher.start()
        patched.return_value = {"foo": {"name": "test.pdf", "size": 1, "mimetype": "application/pdf"}}
        self.addCleanup(self.get_several_remote_metadata_patcher.stop)

        self.get_remote_token_patcher = mock.patch('osis_document.api.utils.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'foobar'
        self.addCleanup(self.get_remote_token_patcher.stop)

        self.get_remote_tokens_patcher = mock.patch('osis_document.api.utils.get_remote_tokens')
        patched = self.get_remote_tokens_patcher.start()
        patched.return_value = {'foo': 'foobar'}
        self.addCleanup(self.get_remote_tokens_patcher.stop)

        self.save_raw_content_remotely_patcher = mock.patch('osis_document.utils.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'
        self.addCleanup(self.save_raw_content_remotely_patcher.stop)

        patcher = mock.patch('admission.exports.utils.change_remote_metadata')
        self.change_remote_metadata_patcher = patcher.start()
        self.change_remote_metadata_patcher.return_value = 'a-token'
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'admission.infrastructure.admission.formation_generale.domain.service.notification.get_remote_token'
        )
        patched = patcher.start()
        patched.return_value = 'foobar'
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'admission.infrastructure.admission.formation_generale.domain.service.notification.get_remote_tokens'
        )
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {file_uuid: 'foobar' for file_uuid in uuids}
        self.addCleanup(patcher.stop)

        # Mock weasyprint
        patcher = mock.patch(
            'admission.exports.utils.get_pdf_from_template',
            return_value=b'some content',
        )
        self.get_pdf_from_template_patcher = patcher.start()
        self.addCleanup(patcher.stop)
