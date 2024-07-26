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
from django.db.models import ExpressionWrapper, Q, BooleanField
from django.utils.translation import get_language
from rules.contrib.views import LoginRequiredMixin

from admission.models import DiplomaticPost


__all__ = [
    'DiplomaticPostsAutocomplete',
]


class DiplomaticPostsAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        queryset = DiplomaticPost.objects.annotate_countries().all()

        country_term = self.forwarded.get('country')
        name_field = 'name_fr' if get_language() == settings.LANGUAGE_CODE_FR else 'name_en'

        if self.q:
            # Filter the queryset by name
            queryset = queryset.filter(**{f'{name_field}__icontains': self.q})

        if country_term:
            # Order the queryset to retrieve the diplomatic posts of the specified country first
            return queryset.annotate(
                in_specified_country=ExpressionWrapper(
                    Q(countries_iso_codes__contains=[country_term]),
                    output_field=BooleanField(),
                )
            ).order_by('-in_specified_country', name_field)

        return queryset.order_by(name_field)

    def get_results(self, context):
        country = self.forwarded.get('country', '')
        name_attribute = 'name_fr' if get_language() == settings.LANGUAGE_CODE else 'name_en'

        final_results = [dict(id=post.code, text=getattr(post, name_attribute)) for post in context['object_list']]

        if country:
            # The diplomatic posts in the residential country are returned first and we add a separator between them
            # and the other ones
            previous_post_in_country = False
            for index, post in enumerate(context['object_list']):
                if post.in_specified_country:
                    previous_post_in_country = True
                else:
                    if previous_post_in_country:
                        final_results.insert(index, dict(id=None, text='<hr>'))
                    break

        return final_results
