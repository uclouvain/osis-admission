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
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.utils import (
    get_cached_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
)
from osis_role.contrib.views import APIPermissionRequiredMixin


class BasePDFRecapView(APIPermissionRequiredMixin, RetrieveAPIView):
    pagination_class = None
    filter_backends = []

    def get(self, request, *args, **kwargs):
        """Generate the proposition recap and return a file read token"""
        from admission.exports.admission_recap.admission_recap import (
            admission_pdf_recap,
        )

        admission = self.get_permission_object()

        token = admission_pdf_recap(admission=admission, language=admission.candidate.language)
        serializer = serializers.PDFRecapSerializer(instance={'token': token})
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        responses=serializers.PDFRecapSerializer,
        operation_id='retrieve_continuing_education_proposition_pdf_recap',
    ),
)
class ContinuingPDFRecapView(BasePDFRecapView):
    name = "continuing_pdf_recap"
    permission_mapping = {
        'GET': 'admission.download_continuingeducationadmission_pdf_recap',
    }

    def get_permission_object(self):
        return get_cached_continuing_education_admission_perm_obj(self.kwargs['uuid'])


@extend_schema_view(
    get=extend_schema(
        responses=serializers.PDFRecapSerializer,
        operation_id='retrieve_doctorate_education_proposition_pdf_recap',
    ),
)
class DoctoratePDFRecapView(BasePDFRecapView):
    name = "doctorate_pdf_recap"
    permission_mapping = {
        'GET': 'admission.download_doctorateadmission_pdf_recap',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])


@extend_schema_view(
    get=extend_schema(
        responses=serializers.PDFRecapSerializer,
        operation_id='retrieve_general_education_proposition_pdf_recap',
    ),
)
class GeneralPDFRecapView(BasePDFRecapView):
    name = "general_pdf_recap"
    permission_mapping = {
        'GET': 'admission.download_generaleducationadmission_pdf_recap',
    }

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])
