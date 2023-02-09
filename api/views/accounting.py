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

from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.admission.doctorat.preparation import commands as doctorate_commands
from admission.ddd.admission.formation_generale import commands as general_commands
from admission.utils import (
    get_cached_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
)
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class GeneralAccountingSchema(ResponseSpecificSchema):
    operation_id_base = '_general_accounting'
    serializer_mapping = {
        'GET': serializers.GeneralEducationAccountingDTOSerializer,
        'PUT': (
            serializers.CompleterComptabilitePropositionGeneraleCommandSerializer,
            serializers.PropositionIdentityDTOSerializer,
        ),
    }


class DoctorateAccountingSchema(ResponseSpecificSchema):
    operation_id_base = '_accounting'
    serializer_mapping = {
        'GET': serializers.DoctorateEducationAccountingDTOSerializer,
        'PUT': (
            serializers.CompleterComptabilitePropositionDoctoraleCommandSerializer,
            serializers.PropositionIdentityDTOSerializer,
        ),
    }


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
        result = message_bus_instance.invoke(self.put_accounting_cmd_class(**serializer.data))
        self.get_permission_object().update_detailed_status()
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DoctorateAccountingView(BaseAccountingView):
    name = 'doctorate_accounting'
    schema = DoctorateAccountingSchema()
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission_accounting',
        'PUT': 'admission.change_doctorateadmission_accounting',
    }
    get_serializer_class = serializers.DoctorateEducationAccountingDTOSerializer
    put_serializer_class = serializers.CompleterComptabilitePropositionDoctoraleCommandSerializer
    get_accounting_cmd_class = doctorate_commands.GetComptabiliteQuery
    put_accounting_cmd_class = doctorate_commands.CompleterComptabilitePropositionCommand

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])


class GeneralAccountingView(BaseAccountingView):
    name = 'general_accounting'
    schema = GeneralAccountingSchema()
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
