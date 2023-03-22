# ##############################################################################
#         if not form.is_valid():
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from urllib.parse import unquote

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import RedirectView

from admission.api.views.submission import get_access_conditions_url


__all__ = [
    'AccessConditionsURL',
]


class AccessConditionsURL(LoginRequiredMixin, RedirectView):
    urlpatterns = {
        'access-conditions-url': (
            'access-conditions-url/<str:training_type>/<str:training_acronym>/<str:partial_training_acronym>/'
        ),
    }

    def get_redirect_url(self, *args, **kwargs) -> str:
        return get_access_conditions_url(
            training_type=self.kwargs.get('training_type'),
            training_acronym=unquote(self.kwargs.get('training_acronym')),
            partial_training_acronym=self.kwargs.get('partial_training_acronym'),
        )
