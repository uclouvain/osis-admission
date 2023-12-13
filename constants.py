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
