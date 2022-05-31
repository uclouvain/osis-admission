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


class GetDefaultContextParam:
    """
    A default class that can be used to represent a context param.
    For instance, we can use it with CreateOnlyDefault to set a default argument with the value from a parameter
    specified in the context during create operations, e.g.:

    param_field = serializers.HiddenField(
        default=serializers.CreateOnlyDefault(GetDefaultContextParam('context_param_name')),
    )
    """
    requires_context = True

    def __init__(self, param):
        self.param = param

    def __call__(self, serializer_field):
        return serializer_field.context.get(self.param)

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class IncludedFieldsMixin:
    def get_fields(self) -> dict:
        """Filter source declared fields and order them by Meta.fields"""
        fields = super().get_fields()
        included_fields = getattr(self, 'Meta').fields
        return dict(
            sorted(
                {name: field for name, field in fields.items() if name in included_fields}.items(),
                key=lambda item: included_fields.index(item[0]),
            )
        )
