# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional

from django.utils.functional import cached_property
from rest_framework.generics import get_object_or_404

from admission.models import (
    ContinuingEducationAdmission,
    DoctorateAdmission,
    GeneralEducationAdmission,
)
from admission.utils import (
    get_cached_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
)


class PersonRelatedMixin:
    @cached_property
    def candidate(self):
        if self.kwargs.get('uuid'):
            return get_object_or_404(DoctorateAdmission, uuid=self.kwargs.get('uuid')).candidate
        return self.request.user.person

    def get_object(self):
        return self.candidate

    def get_permission_object(self) -> Optional[DoctorateAdmission]:
        if self.kwargs.get('uuid'):
            return get_cached_admission_perm_obj(self.kwargs['uuid'])


class GeneralEducationPersonRelatedMixin:
    @cached_property
    def candidate(self):
        return get_object_or_404(GeneralEducationAdmission, uuid=self.kwargs.get('uuid')).candidate

    def get_object(self):
        return self.candidate

    def get_permission_object(self) -> Optional[GeneralEducationAdmission]:
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])


class ContinuingEducationPersonRelatedMixin:
    @cached_property
    def candidate(self):
        return get_object_or_404(ContinuingEducationAdmission, uuid=self.kwargs.get('uuid')).candidate

    def get_object(self):
        return self.candidate

    def get_permission_object(self) -> Optional[ContinuingEducationAdmission]:
        return get_cached_continuing_education_admission_perm_obj(self.kwargs['uuid'])
