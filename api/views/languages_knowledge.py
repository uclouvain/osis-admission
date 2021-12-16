# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.schema import ChoicesEnumSchema
from osis_profile.models.education import LanguageKnowledge


class LanguagesKnowledgeSchema(ChoicesEnumSchema):
    def get_responses(self, path, method):
        if method == "POST":
            return super().get_responses(path, "GET")
        return super().get_responses(path, method)

    def get_request_body(self, path, method):
        if method == "POST":
            self.request_media_types = self.map_parsers(path, method)
            item_schema = self._get_reference(self.get_serializer(path, method))
            body_schema = {
                'type': 'array',
                'items': item_schema,
            }
            return {
                'content': {
                    ct: {'schema': body_schema}
                    for ct in self.request_media_types
                }
            }
        return super().get_request_body(path, method)


class LanguagesKnowledgeViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, GenericAPIView):
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.LanguageKnowledgeSerializer
    schema = LanguagesKnowledgeSchema(tags=["person"])
    name = "languages-knowledge"

    def get_queryset(self):
        return self.request.user.person.languages_knowledge.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        person = self.request.user.person
        input_serializer = self.get_serializer(request, many=True, data=request.data)
        input_serializer.is_valid(raise_exception=True)  # should raise unique exception
        LanguageKnowledge.objects.filter(person=person).delete()
        LanguageKnowledge.objects.bulk_create(
            (
                LanguageKnowledge(person=person, **language_knowledge)
                for language_knowledge
                in input_serializer.validated_data
            )
        )
        output_serializer = self.get_serializer_class()(
            instance=LanguageKnowledge.objects.filter(person=person).all(),
            many=True,
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
