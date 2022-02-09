# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework.permissions import BasePermission, SAFE_METHODS

from admission.contrib.models import DoctorateAdmission, SupervisionActor
from admission.ddd.preparation.projet_doctoral.domain.model._enums import ChoixStatutProposition
from admission.ddd.preparation.projet_doctoral.domain.service.initier_proposition import MAXIMUM_AUTORISE


class IsSelfPersonTabOrTabPermission(BasePermission):
    def __init__(self, permission_suffix) -> None:
        super().__init__()
        self.permission_suffix = permission_suffix

    def has_permission(self, request, view):
        # No object means we are editing our own profile
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            permission = 'admission.view_doctorateadmission_{}'.format(self.permission_suffix)
        else:
            permission = 'admission.change_doctorateadmission_{}'.format(self.permission_suffix)
        return request.user.has_perm(permission, obj)


class IsListingOrHasNotAlreadyCreatedPermission(BasePermission):
    def has_permission(self, request, view):
        # No object means we are either listing or creating a new admission
        if request.method in SAFE_METHODS:
            return True
        admission_count = (
            DoctorateAdmission.objects.filter(candidate=request.user.person)
            .exclude(status=ChoixStatutProposition.CANCELLED.name)
            .count()
        )
        return admission_count < MAXIMUM_AUTORISE


class IsSupervisionMember(BasePermission):
    def has_permission(self, request, view):
        # User is among supervision actors
        return SupervisionActor.objects.filter(person_id=request.user.person.pk).exists()
