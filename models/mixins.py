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
from typing import Optional

from admission.admission_utils.copy_documents import copy_documents

__all__ = [
    'DocumentCopyModelMixin',
]


class DocumentCopyModelMixin:
    """
    This mixin allows to replace each document by a copy of this document when saving the object for the first
    time. To do it, the `duplicate_documents_when_saving` attribute must be set to True.
    The `ID_ATTRIBUTE` property must be defined with the name of the attribute identifying the objects.
    """

    ID_ATTRIBUTE = ''

    def __init__(self, *args, **kwargs):
        self._duplicate_documents_when_saving: Optional[bool] = None

        super().__init__(*args, **kwargs)

    @property
    def duplicate_documents_when_saving(self):
        return self._duplicate_documents_when_saving

    @duplicate_documents_when_saving.setter
    def duplicate_documents_when_saving(self, value):
        self._duplicate_documents_when_saving = value

    def save(self, *args, **kwargs) -> None:
        if self._state.adding and self.duplicate_documents_when_saving:
            copy_documents(objs=[self], id_attribute=self.ID_ATTRIBUTE)

        return super().save(*args, **kwargs)
