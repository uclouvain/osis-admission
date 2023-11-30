# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from dal import autocomplete


__all__ = [
    'ListSelect2',
    'Select2',
    'Select2Multiple',
    'TagSelect2',
]


# The media of the select2 widget are loaded in the base layout.html so we don't need to do it twice
class Select2WithoutMediaMixin:
    class Media:
        extend = False


class ListSelect2(Select2WithoutMediaMixin, autocomplete.ListSelect2):
    pass


class Select2(Select2WithoutMediaMixin, autocomplete.Select2):
    pass


class Select2Multiple(Select2WithoutMediaMixin, autocomplete.Select2Multiple):
    pass


class TagSelect2(Select2WithoutMediaMixin, autocomplete.TagSelect2):
    pass


class ModelSelect2(Select2WithoutMediaMixin, autocomplete.ModelSelect2):
    pass


class Select2MultipleWithTagWhenNoResultWidget(autocomplete.Select2Multiple):
    """
    We override the default widget:
     - to prevent the overriding of the option value with the option label when the tags are used
     - to insert the tag option only if there is no other result

     Note that to simplify the code, the part related to the creation of objects in Django has been removed.
    """

    autocomplete_function = "select2_tag"

    class Media:
        extend = False
        js = ['admission/select2_tag.js']
