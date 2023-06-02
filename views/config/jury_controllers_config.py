# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import messages
from django.views.generic import FormView

from admission.ddd.parcours_doctoral.jury.commands import RecupererVerificateursQuery, ModifierVerificateursCommand
from admission.forms.jury_controllers_config import ControllersFormset
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import PermissionRequiredMixin

__all__ = [
    'JuryControllersConfigChangeView',
]


class JuryControllersConfigChangeView(PermissionRequiredMixin, FormView):
    template_name = 'admission/config/jury_controllers_config.html'
    permission_required = 'admission.change_controller'
    success_url = 'admission:config:jury-controllers-config:update'
    form_class = ControllersFormset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = context['form']
        return context

    def get_initial(self):
        verificateurs = message_bus_instance.invoke(RecupererVerificateursQuery())
        return [
            {
                'entite_code': verificateur.entite_code,
                'matricule': verificateur.matricule,
            } for verificateur in verificateurs
        ]

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ModifierVerificateursCommand(
                    verificateurs=form.cleaned_data,
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                messages.error(self.request, exception.message)
            return self.form_invalid(form=form)
