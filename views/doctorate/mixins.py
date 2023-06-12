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
import json
from typing import Union

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin

from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.sic_management import SicManagement
from admission.contrib.models import DoctorateAdmission, GeneralEducationAdmission, ContinuingEducationAdmission
from admission.contrib.models.base import AdmissionViewer, BaseAdmission
from admission.ddd.admission.doctorat.preparation.commands import GetPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.doctorat.preparation.dtos import PropositionDTO
from admission.ddd.admission.doctorat.validation.commands import RecupererDemandeQuery
from admission.ddd.admission.doctorat.validation.domain.validator.exceptions import DemandeNonTrouveeException
from admission.ddd.admission.doctorat.validation.dtos import DemandeDTO
from admission.ddd.admission.formation_continue.commands import RecupererPropositionQuery
from admission.ddd.admission.formation_generale.commands import RecupererPropositionGestionnaireQuery
from admission.ddd.admission.formation_generale.dtos.proposition import PropositionGestionnaireDTO
from admission.ddd.parcours_doctoral.commands import RecupererDoctoratQuery
from admission.ddd.parcours_doctoral.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.parcours_doctoral.dtos import DoctoratDTO
from admission.ddd.parcours_doctoral.epreuve_confirmation.commands import (
    RecupererDerniereEpreuveConfirmationQuery,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from admission.ddd.parcours_doctoral.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from admission.templatetags.admission import CONTEXT_CONTINUING, CONTEXT_DOCTORATE, CONTEXT_GENERAL
from admission.utils import (
    get_cached_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
)
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import PermissionRequiredMixin


class AdmissionViewMixin(LoginRequiredMixin, PermissionRequiredMixin, ContextMixin):
    @property
    def admission_uuid(self) -> str:
        return self.kwargs.get('uuid', '')

    @property
    def current_context(self):
        return self.request.resolver_match.namespaces[1]

    @cached_property
    def formatted_current_context(self):
        return self.current_context.replace('-', '_')

    @cached_property
    def base_namespace(self):
        return ':'.join(self.request.resolver_match.namespaces[:2])

    @property
    def admission(self) -> Union[DoctorateAdmission, GeneralEducationAdmission, ContinuingEducationAdmission]:
        return {
            CONTEXT_DOCTORATE: get_cached_admission_perm_obj,
            CONTEXT_GENERAL: get_cached_general_education_admission_perm_obj,
            CONTEXT_CONTINUING: get_cached_continuing_education_admission_perm_obj,
        }[self.current_context](self.admission_uuid)

    def get_permission_object(self):
        return self.admission

    @property
    def is_doctorate(self):
        return self.current_context == CONTEXT_DOCTORATE

    @property
    def is_continuing(self):
        return self.current_context == CONTEXT_CONTINUING

    @property
    def is_general(self):
        return self.current_context == CONTEXT_GENERAL


class LoadDossierViewMixin(AdmissionViewMixin):
    @cached_property
    def proposition(self) -> Union[PropositionDTO, PropositionGestionnaireDTO]:
        cmd = {
            CONTEXT_DOCTORATE: GetPropositionCommand(uuid_proposition=self.admission_uuid),
            CONTEXT_CONTINUING: RecupererPropositionQuery(uuid_proposition=self.admission_uuid),
            CONTEXT_GENERAL: RecupererPropositionGestionnaireQuery(uuid_proposition=self.admission_uuid),
        }[self.current_context]
        return message_bus_instance.invoke(cmd)

    @cached_property
    def dossier(self) -> 'DemandeDTO':
        return message_bus_instance.invoke(RecupererDemandeQuery(uuid=self.admission_uuid))

    @cached_property
    def doctorate(self) -> 'DoctoratDTO':
        return message_bus_instance.invoke(RecupererDoctoratQuery(doctorat_uuid=self.admission_uuid))

    @cached_property
    def last_confirmation_paper(self) -> EpreuveConfirmationDTO:
        try:
            last_confirmation_paper = message_bus_instance.invoke(
                RecupererDerniereEpreuveConfirmationQuery(self.admission_uuid)
            )
            if not last_confirmation_paper:
                raise Http404(_('Confirmation paper not found.'))
            return last_confirmation_paper
        except (DoctoratNonTrouveException, EpreuveConfirmationNonTrouveeException) as e:
            raise Http404(e.message)

    def get_permission_object(self):
        return self.admission

    @property
    def is_doctorate(self):
        return self.current_context == CONTEXT_DOCTORATE

    @property
    def is_continuing(self):
        return self.current_context == CONTEXT_CONTINUING

    @property
    def is_general(self):
        return self.current_context == CONTEXT_GENERAL

    @cached_property
    def base_namespace(self):
        return ':'.join(self.request.resolver_match.namespaces[:2])

    def update_current_admission_on_form_valid(self, form, admission):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admission_status = self.admission.status
        context['base_namespace'] = self.base_namespace
        context['base_template'] = f'admission/{self.formatted_current_context}/tab_layout.html'
        context['original_admission'] = self.admission

        if self.is_doctorate:
            try:
                if admission_status == ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name:
                    context['dossier'] = self.dossier
                    context['doctorate'] = self.doctorate
                else:
                    if admission_status == ChoixStatutPropositionDoctorale.CONFIRMEE.name:
                        context['dossier'] = self.dossier

                    context['admission'] = self.proposition

            except (PropositionNonTrouveeException, DemandeNonTrouveeException, DoctoratNonTrouveException) as e:
                raise Http404(e.message)
        elif self.is_general:
            context['admission'] = self.proposition
        else:
            context['admission'] = self.admission
        return context

    def dispatch(self, request, *args, **kwargs):
        if (
            request.method == 'GET'
            and self.admission_uuid
            and getattr(request.user, 'person', None)
            and (SicManagement.belong_to(request.user.person) or CentralManager.belong_to(request.user.person))
        ):
            AdmissionViewer.add_viewer(person=request.user.person, admission=self.admission)

        return super().dispatch(request, *args, **kwargs)


class DoctorateAdmissionLastConfirmationMixin(LoadDossierViewMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        context['confirmation_paper'] = self.last_confirmation_paper
        return context


class AdmissionFormMixin(AdmissionViewMixin):
    message_on_success = _('Your data has been saved.')
    message_on_failure = _('Some errors have been encountered.')
    update_requested_documents = False
    update_admission_author = False
    default_htmx_trigger_form_extra = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_headers = {}
        self.htmx_trigger_form_extra = {**self.default_htmx_trigger_form_extra}

    def htmx_trigger_form(self, is_valid: bool):
        """Add a JS event to listen for when the form is submitted through HTMX."""
        self.custom_headers = {
            'HX-Trigger': {
                "formValidation": {
                    "is_valid": is_valid,
                    "message": str(self.message_on_success if is_valid else self.message_on_failure),
                    **self.htmx_trigger_form_extra,
                }
            }
        }

    def update_current_admission_on_form_valid(self, form, admission):
        """Override this method to update the current admission on form valid."""
        pass

    def form_valid(self, form):
        messages.success(self.request, str(self.message_on_success))

        # Update the last update author of the admission
        author = getattr(self.request.user, 'person')
        if self.update_admission_author and author:
            admission = BaseAdmission.objects.get(uuid=self.admission_uuid)
            admission.last_update_author = author
            # Additional updates if needed
            self.update_current_admission_on_form_valid(form, admission)
            admission.save()

        # Update the requested documents
        if self.update_requested_documents and hasattr(self.admission, 'update_requested_documents'):
            self.admission.update_requested_documents()

        if self.request.htmx:
            self.htmx_trigger_form(is_valid=True)
            return self.render_to_response(self.get_context_data(form=form))

        # If specified, return to the correct checklist tab
        if 'next' in self.request.GET:
            url = resolve_url(f'admission:{self.current_context}:checklist', uuid=self.admission_uuid)
            return HttpResponseRedirect(f"{url}{'#' + self.request.GET['next']}")

        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # Add custom headers
        for header_key, header_value in self.custom_headers.items():
            current_data_str = response.headers.get(header_key)
            if current_data_str:
                current_data = json.loads(current_data_str)
                current_data.update(header_value)
            else:
                current_data = header_value
            response.headers[header_key] = json.dumps(current_data)
        return response

    def form_invalid(self, form):
        messages.error(self.request, str(self.message_on_failure))
        if self.request.htmx:
            self.htmx_trigger_form(is_valid=False)
        return super().form_invalid(form)
