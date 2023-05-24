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
from django.urls import reverse
from django.views.generic import TemplateView, FormView

from admission.ddd.parcours_doctoral.jury.commands import AjouterMembreCommand
from admission.ddd.parcours_doctoral.jury.domain.model.enums import RoleJury
from admission.ddd.parcours_doctoral.jury.validator.exceptions import (
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
from admission.views.doctorate.mixins import LoadDossierViewMixin

__all__ = [
    'DoctorateAdmissionJuryPreparationDetailView',
    'DoctorateAdmissionJuryView',
]
__namespace__ = False

from admission.views.mixins.business_exceptions_form_view_mixin import BusinessExceptionFormViewMixin
from infrastructure.messages_bus import message_bus_instance


class DoctorateAdmissionJuryPreparationDetailView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'jury-preparation'
    template_name = 'admission/doctorate/details/jury/preparation.html'
    permission_required = 'admission.view_admission_jury'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jury'] = self.jury
        context['cotutelle'] = self.cotutelle
        return context


class DoctorateAdmissionJuryView(
    LoadDossierViewMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    urlpatterns = 'jury'
    template_name = 'admission/doctorate/forms/jury/jury.html'
    permission_required = 'admission.view_admission_jury'
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jury'] = self.jury
        context['membre_president'] = [membre for membre in self.jury.membres if membre.role == RoleJury.PRESIDENT.name]
        context['membre_secretaire'] = [
            membre for membre in self.jury.membres if membre.role == RoleJury.SECRETAIRE.name
        ]
        context['membres'] = [membre for membre in self.jury.membres if membre.role == RoleJury.MEMBRE.name]
        if not self.request.user.has_perm('admission.change_admission_jury', obj=self.admission):
            del context['form']
        return context

    def call_command(self, form):
        message_bus_instance.invoke(
            AjouterMembreCommand(
                uuid_jury=self.admission_uuid,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return reverse('admission:doctorate:jury', args=[self.admission_uuid])
