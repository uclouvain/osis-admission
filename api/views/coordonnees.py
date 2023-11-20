# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial

from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.permissions import IsSelfPersonTabOrTabPermission, DoesNotHaveSubmittedPropositions
from admission.api.views.mixins import (
    PersonRelatedMixin,
    GeneralEducationPersonRelatedMixin,
    ContinuingEducationPersonRelatedMixin,
)
from osis_role.contrib.views import APIPermissionRequiredMixin
from reference.services.postal_code_validator import PostalCodeValidatorService, PersonAddressException


class BaseCoordonneesViewSet(
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.CoordonneesSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def validate_data(self, data):
        errors = {}
        if data.get('residential'):
            try:
                PostalCodeValidatorService(
                    country_iso_code=data['residential'].get('country'),
                    postal_code=data['residential'].get('postal_code'),
                ).validate()
            except PersonAddressException as exception:
                errors['residential_postal_code'] = [
                    {
                        "status_code": f'RESIDENTIAL-{exception.status_code}',
                        "detail": exception.message,
                    }
                ]
        if data.get('contact'):
            try:
                PostalCodeValidatorService(
                    country_iso_code=data['contact'].get('country'),
                    postal_code=data['contact'].get('postal_code'),
                ).validate()
            except PersonAddressException as exception:
                errors['contact_postal_code'] = [
                    {
                        "status_code": f'CONTACT-{exception.status_code}',
                        "detail": exception.message,
                    }
                ]
        return errors

    def put(self, request, *args, **kwargs):
        errors = self.validate_data(request.data)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        response = self.update(request, *args, **kwargs)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status(request.user.person)
        return response


class CoordonneesViewSet(PersonRelatedMixin, BaseCoordonneesViewSet):  # pylint: disable=too-many-ancestors
    name = "coordonnees"
    permission_classes = [
        DoesNotHaveSubmittedPropositions,
        partial(IsSelfPersonTabOrTabPermission, permission_suffix='coordinates', can_edit=True),
    ]


class GeneralCoordonneesView(
    GeneralEducationPersonRelatedMixin,
    BaseCoordonneesViewSet,
):  # pylint: disable=too-many-ancestors
    name = "general_coordinates"
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_coordinates',
        'PUT': 'admission.change_generaleducationadmission_coordinates',
    }


class ContinuingCoordonneesView(
    ContinuingEducationPersonRelatedMixin,
    BaseCoordonneesViewSet,
):  # pylint: disable=too-many-ancestors
    name = "continuing_coordinates"
    permission_mapping = {
        'GET': 'admission.view_continuingeducationadmission_coordinates',
        'PUT': 'admission.change_continuingeducationadmission_coordinates',
    }
