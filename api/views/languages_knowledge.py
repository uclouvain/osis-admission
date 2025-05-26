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
from functools import partial

from django.core.exceptions import ValidationError
from django.db.models import Case, When
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.permissions import IsSelfPersonTabOrTabPermission
from admission.api.views.mixins import PersonRelatedMixin
from admission.ddd import LANGUES_OBLIGATOIRES_DOCTORAT
from osis_profile.models.education import LanguageKnowledge
from osis_role.contrib.views import APIPermissionRequiredMixin


class LanguagesKnowledgeViewSet(
    PersonRelatedMixin,
    APIPermissionRequiredMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericAPIView,
):
    name = "languages-knowledge"
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.LanguageKnowledgeSerializer
    permission_classes = [partial(IsSelfPersonTabOrTabPermission, permission_suffix='languages')]

    def get_queryset(self):
        return self.candidate.languages_knowledge.alias(
            relevancy=Case(
                When(language__code='EN', then=2),
                When(language__code='FR', then=1),
                default=0,
            ),
        ).order_by('-relevancy', 'language__code')

    @extend_schema(operation_id='listLanguageKnowledgesAdmission', tags=['person'])
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @staticmethod
    def validate_languages(data):
        """Validate language uniqueness and mandatory languages presence."""
        languages = [language_knowledge.get("language").code for language_knowledge in data]
        if not all(language in languages for language in LANGUES_OBLIGATOIRES_DOCTORAT):
            raise ValidationError(_("Mandatory languages are missing."))
        duplicate_languages = set([language for language in languages if languages.count(language) > 1])
        if duplicate_languages:
            raise ValidationError(_("You cannot enter a language more than once, please correct the form."))

    @extend_schema(
        operation_id='createLanguageKnowledgeAdmission',
        request=serializers.LanguageKnowledgeSerializer(many=True),
        responses=serializers.LanguageKnowledgeSerializer(many=True),
        tags=['person'],
    )
    def post(self, request, *args, **kwargs):
        person = self.request.user.person
        input_serializer = self.get_serializer(request, many=True, data=request.data)
        input_serializer.is_valid(raise_exception=True)
        self.validate_languages(input_serializer.validated_data)
        LanguageKnowledge.objects.filter(person=person).delete()
        LanguageKnowledge.objects.bulk_create(
            (
                LanguageKnowledge(person=person, **language_knowledge)
                for language_knowledge in input_serializer.validated_data
            )
        )
        output_serializer = self.get_serializer_class()(
            instance=LanguageKnowledge.objects.filter(person=person).all(),
            many=True,
        )
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status(person)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(operation_id='listLanguageKnowledges', tags=['person']),
    post=extend_schema(operation_id='createLanguageKnowledge', tags=['person']),
)
class CommonLanguagesKnowledgeViewSet(LanguagesKnowledgeViewSet):
    name = "common-languages-knowledge"
