# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.views import View
from django_htmx.http import HttpResponseClientRefresh

__all__ = [
    'EPCInjectionView',
]

from admission.models.base import BaseAdmission
from admission.services.injection_epc.injection_dossier import InjectionEPCAdmission

from base.utils.htmx import HtmxPermissionRequiredMixin


class EPCInjectionView(HtmxPermissionRequiredMixin, View):
    urlpatterns = {'epc-injection': 'epc-injection/<uuid:uuid>'}
    permission_required = 'admission.can_inject_to_epc'
    http_method_names = ['post']

    @property
    def admission(self):
        return BaseAdmission.objects.get(uuid=self.kwargs['uuid'])

    def post(self, request, *args, **kwargs):
        InjectionEPCAdmission().injecter(admission=self.admission)
        return HttpResponseClientRefresh()

    def get_permission_object(self):
        return self.admission
