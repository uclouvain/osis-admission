# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from rest_framework.generics import get_object_or_404

from admission.api.schema import ChoicesEnumSchema
from admission.contrib.models import DoctorateAdmission


class PersonRelatedSchema(ChoicesEnumSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(tags=["person"], *args, **kwargs)

    def get_operation_id(self, path, method):
        operation_id = super().get_operation_id(path, method)
        if 'uuid' in path:
            operation_id += 'Admission'
        return operation_id


class PersonRelatedMixin:
    schema = PersonRelatedSchema()

    def get_object(self):
        if self.kwargs.get('uuid'):
            return get_object_or_404(DoctorateAdmission, uuid=self.kwargs.get('uuid')).candidate
        return self.request.user.person

    def get_permission_object(self):
        if self.kwargs.get('uuid'):
            return get_object_or_404(DoctorateAdmission, uuid=self.kwargs.get('uuid'))
