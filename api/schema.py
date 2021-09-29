# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from collections import OrderedDict

from rest_framework.schemas.openapi import AutoSchema, SchemaGenerator
from rest_framework.serializers import Serializer

from base.models.utils.utils import ChoiceEnum


class AdmissionSchemaGenerator(SchemaGenerator):
    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        schema["openapi"] = "3.0.0"
        schema["info"]["title"] = "Admission API"
        schema["info"]["description"] = "This API delivers data for the Admission project."
        schema["info"]["contact"] = {
            "name": "UCLouvain - OSIS",
            "url": "https://github.com/uclouvain/osis"
        }
        schema["servers"] = [
            {
                "url": "https://{environment}.osis.uclouvain.be/api/v1/admission/",
                "variables": {
                    "environment": {
                        "default": "dev",
                        "enum": [
                            "dev",
                            "qa",
                            "test"
                        ]
                    }
                }
            },
            {
                "url": "https://osis.uclouvain.be/api/v1/admission/",
                "description": "Production server"
            }
        ]
        schema["security"] = [{"Token": []}]
        schema['components']["securitySchemes"] = {
            "Token": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Enter your token in the format **Token &lt;token>**"
            }
        }
        schema['components']['parameters'] = {
            "X-User-FirstName": {
                "in": "header",
                "name": "X-User-FirstName",
                "schema": {
                    "type": "string"
                },
                "required": False
            },
            "X-User-LastName": {
                "in": "header",
                "name": "X-User-LastName",
                "schema": {
                    "type": "string"
                },
                "required": False
            },
            "X-User-Email": {
                "in": "header",
                "name": "X-User-Email",
                "schema": {
                    "type": "string"
                },
                "required": False
            },
            "X-User-GlobalID": {
                "in": "header",
                "name": "X-User-GlobalID",
                "schema": {
                    "type": "string"
                },
                "required": False
            },
            "Accept-Language": {
                "in": "header",
                "name": "Accept-Language",
                "description": "The header advertises which languages the client is able to understand, and which "
                               "locale variant is preferred. (By languages, we mean natural languages, such as "
                               "English, and not programming languages.)",
                "schema": {
                    "$ref": "#/components/schemas/AcceptedLanguageEnum"
                },
                "required": False
            }
        }
        schema['components']['responses'] = {
            "Unauthorized": {
                "description": "Unauthorized",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/Error"
                        }
                    }
                }
            },
            "BadRequest": {
                "description": "Bad request",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/Error"
                        }
                    }
                }
            },
            "NotFound": {
                "description": "The specified resource was not found",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/Error"
                        }
                    }
                }
            }
        }
        schema['components']['schemas']['Error'] = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string"
                },
                "message": {
                    "type": "string"
                }
            },
            "required": [
                "code",
                "message"
            ]
        }
        schema['components']['schemas']['AcceptedLanguageEnum'] = {
            "type": "string",
            "enum": [
                "en",
                "fr-be"
            ]
        }
        for path, path_content in schema['paths'].items():
            for method, method_content in path_content.items():
                method_content['parameters'].extend([
                    {'$ref': '#/components/parameters/Accept-Language'},
                    {'$ref': '#/components/parameters/X-User-FirstName'},
                    {'$ref': '#/components/parameters/X-User-LastName'},
                    {'$ref': '#/components/parameters/X-User-Email'},
                    {'$ref': '#/components/parameters/X-User-GlobalID'},
                ])
                method_content['responses'].update({
                    "400": {
                        "$ref": "#/components/responses/BadRequest"
                    },
                    "401": {
                        "$ref": "#/components/responses/Unauthorized"
                    },
                    "404": {
                        "$ref": "#/components/responses/NotFound"
                    }
                })
        return schema


class DetailedAutoSchema(AutoSchema):
    operation_id_base = None

    def __init__(self, *args, **kwargs):
        kwargs.pop('operation_id_base', None)
        super().__init__(operation_id_base=self.operation_id_base, *args, **kwargs)
        self.enums = {}

    def get_request_body(self, path, method):
        if method not in ('PUT', 'PATCH', 'POST'):
            return {}

        self.request_media_types = self.map_parsers(path, method)

        serializer = self.get_serializer(path, method, for_response=False)

        if not isinstance(serializer, Serializer):
            item_schema = {}
        else:
            item_schema = self._get_reference(serializer)

        return {
            'content': {
                ct: {'schema': item_schema}
                for ct in self.request_media_types
            }
        }

    def get_components(self, path, method):
        if method.lower() == 'delete':
            return {}

        components = {}
        for with_response in [True, False]:
            serializer = self.get_serializer(path, method, for_response=with_response)
            if not isinstance(serializer, Serializer):
                return {}
            component_name = self.get_component_name(serializer)
            content = self.map_serializer(serializer)
            components[component_name] = content

        for enum_name, enum in self.enums.items():
            components[enum_name] = enum

        return components

    def get_serializer(self, path, method, for_response=True):
        raise NotImplementedError

    def map_choicefield(self, field):
        # The only way to retrieve the original enum is to compare choices
        for declared_enum in ChoiceEnum.__subclasses__():
            if OrderedDict(declared_enum.choices()) == field.choices:
                self.enums[declared_enum.__name__] = super().map_choicefield(field)
                return {
                    '$ref': "#/components/responses/{}".format(declared_enum.__name__)
                }
        return super().map_choicefield(field)


class ResponseSpecificSchema(DetailedAutoSchema):
    serializer_mapping = {}

    def get_serializer(self, path, method, for_response=True):
        serializer_class = self.serializer_mapping.get(method, None)
        if serializer_class and isinstance(serializer_class, tuple):
            if for_response:
                serializer_class = serializer_class[1]
            else:
                serializer_class = serializer_class[0]
        return serializer_class() if serializer_class else None
