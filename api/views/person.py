# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.permissions import IsSelfPersonTabOrTabPermission, DoesNotHaveSubmittedPropositions
from admission.api.views.mixins import (
    PersonRelatedMixin,
    GeneralEducationPersonRelatedMixin,
    ContinuingEducationPersonRelatedMixin,
    PersonRelatedSchema,
)
from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from backoffice.settings.rest_framework.common_views import DisplayExceptionsByFieldNameAPIMixin
from osis_role.contrib.views import APIPermissionRequiredMixin
from reference.services.belgian_niss_validator import BelgianNISSException


class BasePersonViewSet(
    APIPermissionRequiredMixin,
    DisplayExceptionsByFieldNameAPIMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.PersonIdentificationSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        try:
            response = self.update(request, *args, **kwargs)
        except BelgianNISSException as exception:
            data = {
                'national_number': [
                    {
                        "status_code": exception.status_code,
                        "detail": exception.message,
                    }
                ]
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status(request.user.person)
        return response


class PersonViewSet(PersonRelatedMixin, BasePersonViewSet):
    name = "person"
    permission_classes = [
        DoesNotHaveSubmittedPropositions,
        partial(IsSelfPersonTabOrTabPermission, permission_suffix='person', can_edit=True),
    ]


class GeneralPersonView(GeneralEducationPersonRelatedMixin, BasePersonViewSet):
    name = "general_person"
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_person',
        'PUT': 'admission.change_generaleducationadmission_person',
    }


class ContinuingPersonView(ContinuingEducationPersonRelatedMixin, BasePersonViewSet):
    name = "continuing_person"
    permission_mapping = {
        'GET': 'admission.view_continuingeducationadmission_person',
        'PUT': 'admission.change_continuingeducationadmission_person',
    }


class IdentificationDTOSchema(PersonRelatedSchema):
    operation_id_base = '_identification_dto'
    serializer_mapping = {
        'GET': (
            None,
            serializers.IdentificationDTOSerializer,
        ),
    }


class IdentificationDTOView(APIPermissionRequiredMixin, RetrieveAPIView):
    name = "person_identification"
    permission_classes = [
        DoesNotHaveSubmittedPropositions,
    ]
    serializer_class = serializers.IdentificationDTOSerializer
    schema = IdentificationDTOSchema()
    filter_backends = []
    pagination_class = None

    def get_object(self):
        return ProfilCandidatTranslator.get_identification(
            matricule=self.request.user.person.global_id,
        )
