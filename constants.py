# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import re
import uuid
from django.utils.translation import gettext_lazy as _

FIELD_REQUIRED_MESSAGE = _("This field is required.")
DEFAULT_PAGINATOR_SIZE = 500
PDF_MIME_TYPE = 'application/pdf'
JPEG_MIME_TYPE = 'image/jpeg'
PNG_MIME_TYPE = 'image/png'
IMAGE_MIME_TYPES = {JPEG_MIME_TYPE, PNG_MIME_TYPE}
SUPPORTED_MIME_TYPES = {PDF_MIME_TYPE} | IMAGE_MIME_TYPES
DEFAULT_MIME_TYPES = [PDF_MIME_TYPE]
UUID_REGEX = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
ORDERED_CAMPUSES_UUIDS = {
    'LOUVAIN_LA_NEUVE_UUID': uuid.UUID('6f207107-bcf0-4b38-a622-9e78a3540c99'),
    'BRUXELLES_WOLUWE_UUID': uuid.UUID('6da2b1d8-d60a-4cca-b3c3-333b43529d11'),
    'BRUXELLES_SAINT_LOUIS_UUID': uuid.UUID('9e942dbe-45fc-4de7-9e17-ccd6e82345da'),
    'MONS_UUID': uuid.UUID('f2b2ac6f-1bde-4389-bd5e-2257407c10f5'),
    'BRUXELLES_SAINT_GILLES_UUID': uuid.UUID('f32a20cf-cfd6-47ab-b768-53c6c9df8b7c'),
    'TOURNAI_UUID': uuid.UUID('cf34ff38-268e-4c10-aaa3-ec0c76df2398'),
    'CHARLEROI_UUID': uuid.UUID('32bfcf4f-4b70-4532-9597-9722c61a27f5'),
    'NAMUR_UUID': uuid.UUID('ccdfd820-52dc-4aef-a325-fbba3a1f0f52'),
    'AUTRE_SITE_UUID': uuid.UUID('35b0431b-9609-4a31-a328-04c56571f4ba'),
}
