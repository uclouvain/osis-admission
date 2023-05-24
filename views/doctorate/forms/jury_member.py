# ##############################################################################
#
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
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView

from admission.ddd.parcours_doctoral.jury.commands import (
    RecupererJuryMembreQuery,
    ModifierMembreCommand,
    ModifierRoleMembreCommand,
)
from admission.ddd.parcours_doctoral.jury.commands import RetirerMembreCommand
from admission.ddd.parcours_doctoral.jury.validator.exceptions import (
    MembreNonTrouveDansJuryException,
    NonDocteurSansJustificationException,
    MembreExterneSansInstitutionException,
    MembreExterneSansPaysException,
    MembreExterneSansNomException,
    MembreExterneSansPrenomException,
    MembreExterneSansTitreException,
    MembreExterneSansGenreException,
    MembreExterneSansEmailException,
    MembreDejaDansJuryException,
)
from admission.forms.doctorate.jury.membre import JuryMembreForm
from admission.forms.doctorate.jury.membre_role import JuryMembreRoleForm
from admission.views.doctorate.mixins import LoadDossierViewMixin
from admission.views.mixins.business_exceptions_form_view_mixin import BusinessExceptionFormViewMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    "DoctorateAdmissionJuryMemberRemoveView",
    "DoctorateAdmissionJuryMembreUpdateFormView",
    "DoctorateAdmissionJuryMemberChangeRoleView",
]

__namespace__ = {'jury-member': 'jury-member/<uuid:member_uuid>'}

from osis_role.contrib.views import PermissionRequiredMixin
from reference.models.country import Country


class DoctorateAdmissionJuryMemberRemoveView(
    LoadDossierViewMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    View,
):
    urlpatterns = 'remove'
    permission_required = 'admission.change_admission_jury'

    def post(self, request, *args, **kwargs):
        try:
            message_bus_instance.invoke(
                RetirerMembreCommand(
                    uuid_jury=str(self.kwargs['uuid']),
                    uuid_membre=str(self.kwargs['member_uuid']),
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            messages.error(self.request, _("Some errors have been encountered."))
            for exception in multiple_exceptions.exceptions:
                messages.error(self.request, exception.message)
        return redirect(reverse('admission:doctorate:jury', args=[str(self.kwargs['uuid'])]))


class DoctorateAdmissionJuryMembreUpdateFormView(
    LoadDossierViewMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    urlpatterns = 'update'
    template_name = 'admission/doctorate/forms/jury/member_update.html'
    permission_required = 'admission.change_admission_jury'
    form_class = JuryMembreForm
    error_mapping = {
        NonDocteurSansJustificationException: "justification_non_docteur",
        MembreExterneSansInstitutionException: "institution",
        MembreExterneSansPaysException: "pays",
        MembreExterneSansNomException: "nom",
        MembreExterneSansPrenomException: "prenom",
        MembreExterneSansTitreException: "titre",
        MembreExterneSansGenreException: "genre",
        MembreExterneSansEmailException: "email",
        MembreDejaDansJuryException: "matricule",
    }

    @cached_property
    def membre(self) -> 'MembreDTO':
        try:
            return message_bus_instance.invoke(
                RecupererJuryMembreQuery(
                    uuid_jury=str(self.admission_uuid),
                    uuid_membre=str(self.kwargs['member_uuid']),
                )
            )
        except MembreNonTrouveDansJuryException:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jury'] = self.jury
        context['membre'] = self.membre
        return context

    def get_initial(self):
        if self.membre.matricule:
            institution_principale = JuryMembreForm.InstitutionPrincipaleChoices.UCL.name
        else:
            institution_principale = JuryMembreForm.InstitutionPrincipaleChoices.OTHER.name
        return {
            'matricule': self.membre.matricule,
            'institution_principale': institution_principale,
            'institution': self.membre.institution,
            'autre_institution': self.membre.autre_institution,
            'pays': Country.objects.get(name=self.membre.pays) if self.membre.pays else None,
            'nom': self.membre.nom,
            'prenom': self.membre.prenom,
            'titre': self.membre.titre,
            'justification_non_docteur': self.membre.justification_non_docteur,
            'genre': self.membre.genre,
            'email': self.membre.email,
        }

    def call_command(self, form):
        message_bus_instance.invoke(
            ModifierMembreCommand(
                uuid_jury=self.admission_uuid,
                uuid_membre=self.membre.uuid,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return reverse('admission:doctorate:jury', args=[self.admission_uuid])


class DoctorateAdmissionJuryMemberChangeRoleView(
    LoadDossierViewMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    View,
):
    urlpatterns = 'change-role'
    permission_required = 'admission.change_admission_jury'

    def post(self, request, *args, **kwargs):
        form = JuryMembreRoleForm(data=request.POST)
        if form.is_valid():
            try:
                message_bus_instance.invoke(
                    ModifierRoleMembreCommand(
                        uuid_jury=str(self.kwargs['uuid']),
                        uuid_membre=str(self.kwargs['member_uuid']),
                        role=form.cleaned_data['role'],
                    )
                )
            except MultipleBusinessExceptions as multiple_exceptions:
                messages.error(self.request, _("Some errors have been encountered."))
                for exception in multiple_exceptions.exceptions:
                    messages.error(self.request, exception.message)
        else:
            messages.error(self.request, _("Some errors have been encountered."))
            if form.errors:
                messages.error(self.request, str(form.errors))
        return redirect(reverse('admission:doctorate:jury', args=[str(self.kwargs['uuid'])]))
