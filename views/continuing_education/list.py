# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.functional import cached_property
from django.views.generic import ListView

from admission.models import ContinuingEducationAdmissionProxy
from admission.ddd.admission.formation_continue.commands import ListerDemandesQuery
from admission.forms.admission.filter import ContinuingAdmissionsFilterForm
from admission.views import ListPaginator
from admission.views.list import BaseAdmissionList
from osis_common.utils.htmx import HtmxMixin

__all__ = [
    "ContinuingAdmissionList",
]


class ContinuingAdmissionList(BaseAdmissionList):
    raise_exception = True
    template_name = 'admission/continuing_education/list.html'
    htmx_template_name = 'admission/continuing_education/list_block.html'
    permission_required = 'admission.view_continuing_enrolment_applications'
    filtering_query_class = ListerDemandesQuery
    form_class = ContinuingAdmissionsFilterForm
    urlpatterns = {'list': 'list'}
    paginator_class = ListPaginator

    def additional_command_kwargs(self):
        return {
            'demandeur': self.request.user.person.uuid,
        }
