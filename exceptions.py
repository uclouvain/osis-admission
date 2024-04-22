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

from typing import List, Dict

from django.utils.translation import gettext_lazy as _


class MergePDFException(Exception):
    pass


class DocumentPostProcessingException(Exception):
    pass


class InvalidMimeTypeException(Exception):
    def __init__(self, field, field_mimetypes: List[str], current_mimetype: str):
        field_mimetypes_as_str = ', '.join(field_mimetypes)
        super().__init__(
            _(f'{current_mimetype} is not a valid mimetype for the field "{field}" ({field_mimetypes_as_str})')
        )


class MergeDocumentsException(Exception):
    def __init__(self, exceptions: Dict[str, Exception]):
        message = (
            'An error occurred while processing the documents:'
            if len(exceptions) == 1
            else 'Errors occurred while processing the documents:'
        )

        for id_document, exception in exceptions.items():
            message += f'\n{id_document}: {exception}.'

        super().__init__(message)
