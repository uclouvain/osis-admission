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
from django.utils.translation import get_language, gettext

from admission.models.checklist import RefusalReason, RefusalReasonCategory, AdditionalApprovalCondition

__all__ = [
    'RefusalReasonAutocomplete',
    'RefusalReasonCategoryAutocomplete',
    'AdditionalApprovalConditionAutocomplete',
]


class TranslatedAutocompleteMixin:
    model = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_field_name = 'name_fr' if get_language() == settings.LANGUAGE_CODE_FR else 'name_en'

    def get_queryset(self):
        return super().get_queryset().order_by(self.model_field_name)


class RefusalReasonCategoryAutocomplete(autocomplete.Select2QuerySetView):
    model = RefusalReasonCategory
    urlpatterns = 'refusal-reason-category'
    model_field_name = 'name'


class RefusalReasonAutocomplete(autocomplete.Select2QuerySetView):
    model = RefusalReason
    urlpatterns = 'refusal-reason'
    model_field_name = 'name'


class AdditionalApprovalConditionAutocomplete(TranslatedAutocompleteMixin, autocomplete.Select2QuerySetView):
    model = AdditionalApprovalCondition
    urlpatterns = 'additional-approval-condition'

    def get_results(self, context):
        results = super().get_results(context)
        if not results:
            # Allow to add a free condition
            results.append(
                {
                    'id': self.q,
                    'text': f'[{gettext("Free condition")}] {self.q}',
                    'selected_text': self.q,
                }
            )
        return results
