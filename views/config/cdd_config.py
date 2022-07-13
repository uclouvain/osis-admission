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
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import OuterRef, Subquery
from django.views import generic
from django.utils.translation import gettext_lazy as _

from admission.auth.roles.cdd_manager import CddManager
from admission.contrib.models.cdd_config import CddConfiguration
from admission.forms.cdd_config import CddConfigForm
from base.models.entity_version import EntityVersion
from osis_role.contrib.views import PermissionRequiredMixin

__all__ = [
    'CddConfigListView',
    'CddConfigChangeView',
]


class CddConfigListView(PermissionRequiredMixin, generic.ListView):
    template_name = 'admission/config/cdd_config_list.html'
    permission_required = 'admission.change_cddconfiguration'

    def get_queryset(self):
        managed_cdds = (
            CddManager.objects.filter(person=self.request.user.person)
            .annotate(
                most_recent_acronym=Subquery(
                    EntityVersion.objects.filter(
                        entity__id=OuterRef('entity_id'),
                    )
                    .order_by("-start_date")
                    .values('acronym')[:1]
                )
            )
            .values_list('entity_id', 'most_recent_acronym')
        )
        if not managed_cdds:
            raise PermissionDenied('Current user has no CDD')
        return managed_cdds


class CddConfigChangeView(PermissionRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    template_name = 'admission/config/cdd_config_edit.html'
    permission_required = 'admission.change_cddconfiguration'
    model = CddConfiguration
    form_class = CddConfigForm
    success_message = _("Configuration saved.")

    def has_permission(self):
        managed_cdds = CddManager.objects.filter(person=self.request.user.person).values_list('entity_id', flat=True)
        return super().has_permission() and self.kwargs['pk'] in managed_cdds

    def get_object(self):
        return CddConfiguration.objects.get_or_create(cdd_id=self.kwargs['pk'])[0]

    def get_success_url(self):
        return self.request.get_full_path()
