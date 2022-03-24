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
from django.contrib.auth.mixins import AccessMixin

from admission.auth.roles.cdd_manager import CddManager


class RoleRequiredMixin(AccessMixin):
    """Verify that the current user has the specific role."""

    role_manager_class = None

    def dispatch(self, request, *args, **kwargs):
        http_response = super().dispatch(request, *args, **kwargs)
        person = getattr(request.user, 'person')
        if person and self.role_manager_class.belong_to(person):
            return http_response
        else:
            return self.handle_no_permission()


class CddRequiredMixin(RoleRequiredMixin):
    """Verify that the current user has the cdd role."""
    role_manager_class = CddManager
