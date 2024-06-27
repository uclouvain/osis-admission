# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from dal import autocomplete
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import get_language

from admission.contrib.models.categorized_free_document import CategorizedFreeDocument

__all__ = [
    'CategorizedFreeDocumentsAutocomplete',
]


class CategorizedFreeDocumentsAutocomplete(autocomplete.Select2QuerySetView):
    model = CategorizedFreeDocument
    urlpatterns = 'categorized-free-documents'

    @classmethod
    def get_short_label_field(cls):
        return 'short_label_fr'

    @classmethod
    def get_long_label_field(cls, language):
        return {
            settings.LANGUAGE_CODE_FR: 'long_label_fr',
            settings.LANGUAGE_CODE_EN: 'long_label_en',
        }[language or settings.LANGUAGE_CODE]

    @cached_property
    def current_language(self):
        return self.forwarded['language'] if self.forwarded.get('language') else get_language()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_field_name = self.get_short_label_field()
        self.ordering = self.model_field_name

    def get_search_results(self, queryset, search_term):
        results = super().get_search_results(queryset, search_term)

        # Filter by checklist tab if specified
        if 'checklist_tab' in self.forwarded:
            results = results.filter(checklist_tab=self.forwarded['checklist_tab'])

        if 'admission_context' in self.forwarded:
            results = results.filter(admission_context=self.forwarded['admission_context'])

        return results

    def get_results(self, context):
        full_label_field_name = self.get_long_label_field(self.current_language)

        return [
            {
                'id': result.pk,
                'text': getattr(result, self.model_field_name),
                'selected_text': getattr(result, self.model_field_name),
                'with_academic_year': result.with_academic_year,
                'full_text': getattr(result, full_label_field_name),
            }
            for result in context['object_list']
        ]
