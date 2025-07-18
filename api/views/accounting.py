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
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.ddd.admission.doctorat.preparation import commands as doctorate_commands
from admission.ddd.admission.formation_generale import commands as general_commands
from admission.utils import (
    get_cached_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
)
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class BaseAccountingView(
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    pagination_class = None
    filter_backends = []
    get_serializer_class = None
    put_serializer_class = None
    get_accounting_cmd_class = None
    put_accounting_cmd_class = None

    def get(self, request, *args, **kwargs):
        """Get additional data conditioning the required accounting fields"""
        comptabilite = message_bus_instance.invoke(self.get_accounting_cmd_class(uuid_proposition=self.kwargs['uuid']))
        candidate = self.get_permission_object().candidate
        serializer = self.get_serializer_class(instance=comptabilite, context={'candidate': candidate})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """Edit the accounting of a proposition"""
        serializer = self.put_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            self.put_accounting_cmd_class(
                auteur_modification=request.user.person.global_id,
                **serializer.data,
            )
        )
        self.get_permission_object().update_detailed_status(author=request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        responses=serializers.DoctorateEducationAccountingDTOSerializer,
        operation_id='retrieve_accounting',
    ),
    put=extend_schema(
        request=serializers.CompleterComptabilitePropositionDoctoraleCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='update_accounting',
    ),
)
class DoctorateAccountingView(BaseAccountingView):
    name = 'doctorate_accounting'
    permission_mapping = {
        'GET': 'admission.api_view_admission_accounting',
        'PUT': 'admission.api_change_admission_accounting',
    }
    get_serializer_class = serializers.DoctorateEducationAccountingDTOSerializer
    put_serializer_class = serializers.CompleterComptabilitePropositionDoctoraleCommandSerializer
    get_accounting_cmd_class = doctorate_commands.GetComptabiliteQuery
    put_accounting_cmd_class = doctorate_commands.CompleterComptabilitePropositionCommand

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])


@extend_schema_view(
    get=extend_schema(
        responses=serializers.GeneralEducationAccountingDTOSerializer,
        operation_id='retrieve_general_accounting',
    ),
    put=extend_schema(
        request=serializers.CompleterComptabilitePropositionGeneraleCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='update_general_accounting',
    ),
)
class GeneralAccountingView(BaseAccountingView):
    name = 'general_accounting'
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_accounting',
        'PUT': 'admission.change_generaleducationadmission_accounting',
    }
    get_serializer_class = serializers.GeneralEducationAccountingDTOSerializer
    put_serializer_class = serializers.CompleterComptabilitePropositionGeneraleCommandSerializer
    get_accounting_cmd_class = general_commands.GetComptabiliteQuery
    put_accounting_cmd_class = general_commands.CompleterComptabilitePropositionCommand

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])
