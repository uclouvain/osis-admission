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
from drf_spectacular.generators import SchemaGenerator

ADMISSION_SDK_VERSION = "1.1.17.dev1651"


class AdmissionSchemaGenerator(SchemaGenerator):
    """This generator adds extra information and reshape the schema for admission"""

    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        schema["info"]["version"] = ADMISSION_SDK_VERSION
        schema["info"]["title"] = "Admission API"
        schema["info"]["description"] = "This API delivers data for the Admission project."
        schema["info"]["contact"] = {
            "name": "UCLouvain - OSIS",
            "url": "https://github.com/uclouvain/osis",
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
                            "test",
                        ],
                    }
                },
            },
            {
                "url": "https://osis.uclouvain.be/api/v1/admission/",
                "description": "Production server",
            },
        ]
        # Add extra global headers
        schema['components'].setdefault('parameters', {}).update(
            {
                "X-User-FirstName": {
                    "in": "header",
                    "name": "X-User-FirstName",
                    "schema": {"type": "string"},
                    "required": False,
                },
                "X-User-LastName": {
                    "in": "header",
                    "name": "X-User-LastName",
                    "schema": {"type": "string"},
                    "required": False,
                },
                "X-User-Email": {
                    "in": "header",
                    "name": "X-User-Email",
                    "schema": {"type": "string"},
                    "required": False,
                },
                "X-User-GlobalID": {
                    "in": "header",
                    "name": "X-User-GlobalID",
                    "schema": {"type": "string"},
                    "required": False,
                },
                "Accept-Language": {
                    "in": "header",
                    "name": "Accept-Language",
                    "description": "The header advertises which languages the client is able to understand, and which "
                    "locale variant is preferred. (By languages, we mean natural languages, such as "
                    "English, and not programming languages.)",
                    "schema": {"$ref": "#/components/schemas/AcceptedLanguageEnum"},
                    "required": False,
                },
            }
        )
        # Add error responses
        schema['components'].setdefault('responses', {}).update(
            {
                "Unauthorized": {
                    "description": "Unauthorized",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "BadRequest": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "NotFound": {
                    "description": "The specified resource was not found",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            }
        )
        schema['components']['schemas']['Error'] = {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["code", "message"],
        }
        schema['components']['schemas']['ActionLink'] = {
            'type': 'object',
            'properties': {
                'error': {
                    'type': 'string',
                },
                'method': {
                    'type': 'string',
                    'enum': [
                        'DELETE',
                        'GET',
                        'PATCH',
                        'POST',
                        'PUT',
                    ],
                },
                'url': {
                    'type': 'string',
                    'format': 'uri',
                },
            },
            'oneOf': [
                {
                    'required': [
                        'method',
                        'url',
                    ],
                },
                {
                    'required': [
                        'error',
                    ],
                },
            ],
        }
        schema['components']['schemas']['AcceptedLanguageEnum'] = {"type": "string", "enum": ["en", "fr-be"]}
        for path, path_content in schema['paths'].items():
            for method, method_content in path_content.items():
                # Add error responses to each endpoint
                error_reponses = {
                    "400": {"$ref": "#/components/responses/BadRequest"},
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "404": {"$ref": "#/components/responses/NotFound"},
                }
                method_content['responses'].update(error_reponses)
                # Only allow application/json as content type
                if 'requestBody' in method_content:
                    method_content['requestBody']['content'] = {
                        k: v for k, v in method_content['requestBody']['content'].items() if k == 'application/json'
                    }

                extra_params = [
                    {'$ref': '#/components/parameters/Accept-Language'},
                ]
                if {'Token': []} in method_content.get('security', []):
                    extra_params += [
                        {'$ref': '#/components/parameters/X-User-FirstName'},
                        {'$ref': '#/components/parameters/X-User-LastName'},
                        {'$ref': '#/components/parameters/X-User-Email'},
                        {'$ref': '#/components/parameters/X-User-GlobalID'},
                    ]
                method_content.setdefault('parameters', []).extend(extra_params)
        return schema
