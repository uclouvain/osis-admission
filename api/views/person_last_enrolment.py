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
from functools import partial

from drf_spectacular.utils import extend_schema
from rest_framework import mixins
from rest_framework.generics import GenericAPIView

from admission.api import serializers
from admission.api.permissions import IsSelfPersonTabOrTabPermission
from admission.api.views.mixins import (
    ContinuingEducationPersonRelatedMixin,
    GeneralEducationPersonRelatedMixin,
    PersonRelatedMixin,
)
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    'CommonPersonLastEnrolmentViewSet',
    'DoctoratePersonLastEnrolmentViewSet',
    'GeneralPersonLastEnrolmentViewSet',
    'ContinuingPersonLastEnrolmentViewSet',
]


@extend_schema(tags=['person'])
class BasePersonLastEnrolmentViewSet(
    APIPermissionRequiredMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    """Change view of the information concerning the person's last registration"""
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.PersonLastEnrolmentSerializer

    def put(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status(request.user.person)
        return response


class CommonPersonLastEnrolmentViewSet(PersonRelatedMixin, BasePersonLastEnrolmentViewSet):
    name = "person_last_enrolment"
    permission_classes = [
        partial(IsSelfPersonTabOrTabPermission, permission_suffix='person_last_enrolment', can_edit=True),
    ]


class DoctoratePersonLastEnrolmentViewSet(PersonRelatedMixin, BasePersonLastEnrolmentViewSet):
    name = "doctorate_person_last_enrolment"
    permission_mapping = {
        'PUT': 'admission.change_admission_person_last_enrolment',
    }


class GeneralPersonLastEnrolmentViewSet(GeneralEducationPersonRelatedMixin, BasePersonLastEnrolmentViewSet):
    name = "general_person_last_enrolment"
    permission_mapping = {
        'PUT': 'admission.change_generaleducationadmission_person_last_enrolment',
    }


class ContinuingPersonLastEnrolmentViewSet(ContinuingEducationPersonRelatedMixin, BasePersonLastEnrolmentViewSet):
    name = "continuing_person_last_enrolment"
    permission_mapping = {
        'PUT': 'admission.change_continuingeducationadmission_person_last_enrolment',
    }
